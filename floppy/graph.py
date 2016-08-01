import json
import zlib
import io
# import time
from floppy.node import ControlNode
from floppy.runner import Runner, sendCommand, RGIConnection
from socket import AF_INET, SOCK_STREAM, socket #, SHUT_RDWR, timeout, SHUT_RDWR, SO_REUSEADDR, SOL_SOCKET
from floppy.node import NODECLASSES
from threading import Thread, Lock
from queue import Queue
import struct


def dummy(nodeClass):
    return nodeClass


class Graph(object):
    """
    Class for managing all nodes. The class provides interfaces for spawning/removing nodes and connections.
    It also provides interfaces for spawning and connecting to graph interpreters and for communicating with them.
    Since a Graph interpreter is nothing but a small program able to load a Graph instance and listening to commands,
    the Graph class also provides methods for executing the implemented logic.
    """
    nextFreeNodeID = 0
    nodes = {}

    def __init__(self, painter=None):
        self.slave = False
        self._requestUpdate = False
        self.executedBuffer = []
        self.statusLock = None
        self.connected = False
        self.nextFreeNodeID = 0
        self.nodes = {}
        self.connections = {}
        self.runner = None
        self.reverseConnections = {}
        # self.statusLock = Lock()
        if painter:
            self.painter = painter
            painter.registerGraph(self)
        else:
            self.painter = dummy

    def spawnAndConnect(self):
        """
        Spawns a new graph interpreter instance and establishes a TCP/IP connection to it.
        :return:
        """
        if not self.runner:
            self.runner = Runner()
        self.connect2RemoteRunner(host='127.0.0.1', port=7234)
        self.slave = True

    def connect2RemoteRunner(self, host='127.0.0.1', port=7234):
        self.cmdHost = host
        self.cmdPort = int(port)
        self.slave = False
        self.rgiConnection = RGIConnection()
        self.rgiConnection.connect(self.cmdHost, self.cmdPort)
        # self.connect2Runner(host, port)
        # self.statusLock = Lock()
        # self.statusQueue = Queue(100)
        self.connected = True
        # self.statusListener = StatusListener(self, self.clientSocket, self.statusQueue, self.statusLock)

    def __getattr__(self, item):
        if item == 'newID':
            newID = self.nextFreeNodeID
            self.nextFreeNodeID += 1
            return newID
        else:
            return super(Graph, self).__getattr__(item)

    def requestUpdate(self):
        """
        Tells the graph painter that changes to the graph were made that require a redraw.
        Use this method instead of a direct call of the painter update method if the request is not made by the main
        thread.
        :return:
        """
        self._requestUpdate = True

    def needsUpdate(self):
        """
        Called by the painter instance periodically to check whether a repaint was requested by another thread.
        :return:
        """
        if self.connected:
            IDs = self.requestRemoteStatus()
            if IDs:
                self.executedBuffer += [int(ID) for ID in IDs]
                return True
        if self._requestUpdate:
            self._requestUpdate = False
            return True

    def spawnNode(self, nodeClass, connections=None, position=(0, 0), silent=False):
        """
        Spawns a new node of a given class at a given position with optional connections to other nodes.
        :param nodeClass: subclass object of 'Node'.
        :param connections: Dictionary
        :param position: Tuple of two integer representing the nodes position on the screen relative the the graph's
        origin.
        :param silent: Boolean. Suppresses all notifications that a node was spawned if True.
        :return: newly created Node instance.
        """
        # nodeClass = self.decorator(nodeClass, position)
        newNode = nodeClass(self.newID, self)
        self.reverseConnections[newNode] = set()
        self.connections[newNode] = set()
        if connections:
            self._spawnConnections(connections, newNode)
        try:
            self.painter.registerNode(newNode, position, silent)
        except AttributeError:
            pass
        self.nodes[newNode.ID] = newNode
        self.newestNode = newNode

        return newNode

    def _spawnConnections(self, connections, newNode):
        try:
            outs = connections['outputs']
        except KeyError:
            pass
        else:
            for out in outs:
                self.connect(newNode, out[0], out[1], out[2])
        try:
            ins = connections['inputs']
        except KeyError:
            pass
        else:
            for inp in ins:
                self.connect(inp[1], inp[2], newNode, inp[0])

    def connect(self, outNode, out, inpNode, inp):
        """
        Creates a logical connection between two nodes.
        Before the actual connection is established checks will be performed to make sure that the input is actually
        legal.
        If necessary, previously created connections that are in conflict with the new one will be deleted.
        :param outNode: Node instance that has the output involved in the connection.
        :param out: string representing the Output's name.
        :param inpNode: Node instance that has the input involved in the connection.
        :param inp: string representing the Input's name.
        :return:
        """
        if type(outNode) == str:
            outNode = self.nodes[int(outNode)]
        if type(inpNode) == str:
            inpNode = self.nodes[int(inpNode)]
        outInfo = outNode.getOutputInfo(out)
        inpInfo = inpNode.getInputInfo(inp)
        # if not outInfo.varType == inpInfo.varType:
        if not issubclass(outInfo.varType, inpInfo.varType) and not issubclass(inpInfo.varType, outInfo.varType):
            raise TypeError('Output \'{}\' of node {} and input \'{}\' of not {} don\'t match.'.format(out,
                                                                                                       str(outNode),
                                                                                                       inp,
                                                                                                       str(inpNode)))
        print('Connect output \'{1}\' of node {0} to input \'{3}\' of node {2}'.format(str(outNode),
                                                                                       out,
                                                                                       str(inpNode),
                                                                                       inp))
        conn = Connection(outNode, out, inpNode, inp)
        if not issubclass(type(inpNode), ControlNode) or not inp == 'Control':
            for oldCon in self.reverseConnections[inpNode]:
                if oldCon['inputName'] == inp:
                    self.reverseConnections[inpNode].remove(oldCon)
                    self.connections[oldCon['outputNode']].remove(oldCon)
                    break
        inpInfo.setConnected(True)
        self.connections[outNode].add(conn)
        self.reverseConnections[inpNode].add(conn)
        # self.update()

    def getConnectionsFrom(self, node):
        """
        Returns a list of all connections that involve 'node's' outputs.
        :param node:
        :return: List of connection dictionaries.
        :rtype: list
        """
        return self.connections[node]

    def getConnectionsTo(self, node):
        """
        Returns a list of all connections that involve 'node's' inputs.
        :param node:
        :return:
        """
        return self.reverseConnections[node]

    def getConnectionOfInput(self, inp):
        """
        Returns the connection involving an input
        :param inp: InputInfo instance.
        :return: Connection instance.
        """
        for con in self.getConnectionsTo(self.nodes[int(inp.ID.partition(':')[0])]):
            if con['inputName'] == inp.name:
                return con

    def getConnectionsOfOutput(self, output):
        """
        Returns a list of connections involving an output.
        :param output: OutputInfo instance.
        :return: list of Connection instances.
        """
        node = self.nodes[int(output.ID.partition(':')[0])]
        return [con for con in self.getConnectionsFrom(node) if con['outputName'] == output.name]


    def update(self):
        """
        Updates and repaints the painter instance.
        WARNING: Only call this method from the main thread. Other threads must use the Graph.requestUpdate method which
        has a slight delay.
        :return:
        """
        try:
            self.painter.repaint()
            self.painter.update()
        except AttributeError:
            pass

    def getExecutionHistory(self):
        """
        Returns the current execution history: a list of nodeIDs in the order they were executed in.
        :return: list of nodIDs.
        """
        # self.statusLock.acquire()
        history = self.executedBuffer[:]
        # self.statusLock.release()
        return history


    def execute(self):
        """
        Execute the Graph instance.

        First, the execution loop will set itself up to terminate after the first iteration.
        Next, every node is given the chance to run if all prerequisites are met.
        If a node is executed, the loop termination criterion will be reset to allow an additional iteration over all
        nodes.
        If no node is execute during one iteration, the termination criterion will not be reset and the execution loop
        terminates.
        :return:
        """
        return self.testRun()
        running = True
        i = 0
        while running:
            i += 1
            print('\nExecuting iteration {}.'.format(i))
            running = False
            for node in self.nodes.values():
                checked = node.check()
                running = checked if not running else True
                if checked:
                    node.run()
                    # raise RuntimeError('Uncaught exception while executing node {}.'.format(node))
                    node.notify()

    def runNodePar(self, node, cb=None, arg=None):
        # node.lock()
        t = NodeThread(node, cb, arg)
        # t.join()

    # def testRun(self):
    #     if not self.runner:
    #         self.runner = Runner()
    #     sendCommand('PAUSE', self.cmdHost, self.cmdPort)
    #     data = self.serialize()
    #     self.sendUpdate(data)
    #     sendCommand('UPDATE', self.cmdHost, self.cmdPort)
    #     import time
    #     time.sleep(.5)
    #     sendCommand('UNPAUSE', self.cmdHost, self.cmdPort)
    #     return
    #
    #     import time
    #     time.sleep(2)
    #     sendCommand('PAUSE')
    #     time.sleep(1)
    #     sendCommand('KILL')
    #     del r

    def updateRunner(self):
        """
        Serializes the graph and sends it to the connected graph interpreter telling it to load the new data.
        :return:
        """
        self.executedBuffer = []
        print(self.rgiConnection.send('PAUSE'))
        message = self.serialize()
        # msg = struct.pack('>I', len(message)) + message.encode('utf-8')
        # self.sendUpdate(data)
        print(self.rgiConnection.send('UPDATE'+message))

    def push2Runner(self):
        """
        Serializes the graph and sends it to the connected graph interpreter telling it to load the new data.
        :return:
        """
        self.executedBuffer = []
        print(self.rgiConnection.send('PAUSE'))
        message = self.serialize()
        # msg = struct.pack('>I', len(message)) + message.encode('utf-8')
        # self.sendUpdate(data)
        print(self.rgiConnection.send('PUSH'+message))

    def serialize(self):
        """
        Returns a serialized representation of the graph instance.
        :return:
        """
        data = self.toJson()
        return data
        return zlib.compress(data.encode('utf-8'))

    def save(self, fileName):
        """
        Saves the graph as a JSON string to the disk
        :param fileName: string representing the file name.
        :return:
        """
        saveState = self.toJson()
        with open(fileName, 'w') as fp:
            fp.write(saveState)

    def toJson(self):
        """
        Encodes the graph as a JSON string and returns the string.
        :return:
        """
        return json.dumps([(node.ID, node.save()) for node in self.nodes.values()])
        return json.dumps({node.ID: node.save() for node in self.nodes.values()})

    def killRunner(self):
        """
        Send KILL command to the graph interpreter telling it to terminate itself.
        :return:
        """
        if not self.slave:
            return
        print(self.rgiConnection.send('KILL'))
        # sendCommand('KILL', self.cmdHost, self.cmdPort)
        # self.clientSocket.close()
        del self.runner
        self.runner = None
        self.connected = False

    def pauseRunner(self):
        """
        Send PAUSE command to the graph interpreter.
        :return:
        """
        print(self.rgiConnection.send('PAUSE'))
        # sendCommand('PAUSE', self.cmdHost, self.cmdPort)

    def unpauseRunner(self):
        """
        Send UNPAUSE command to the graph interpreter.
        :return:
        """
        print(self.rgiConnection.send('UNPAUSE'))
        # sendCommand('UNPAUSE', self.cmdHost, self.cmdPort)

    def stepRunner(self):
        """
        Send Step command to the graph interpreter causing it to execute one node and then reenter the PAUSED state.
        :return:
        """
        print(self.rgiConnection.send('STEP'))

    def gotoRunner(self, nextID):
        """
        Send GOTO<Node> command to the graph interpreter causing it to execute the node with the given ID next.
        :param nextID:
        :return:
        """
        print(self.rgiConnection.send('GOTO1'))

    def dropGraph(self):
        print(self.rgiConnection.send('DROP'))

    def requestRemoteStatus(self):
        if self.connected:
            try:
                status = self.rgiConnection.send('STATUS')
            except BrokenPipeError:
                self.connected = False
                return []
            except ConnectionResetError:
                self.connected = False
                return []
            except socket.timeout:
                self.connected = False
                return []
            else:
                return status.split(']')[-1].split('#') if len(status) > 10 else []
        else:
            return []

    def load(self, fileName):
        with open(fileName, 'r') as fp:
            saveState = json.loads(fp.read())
        self.loadState(saveState)
        # self.loadDict(saveState)

    def loadState(self, saveState):
        """
        Reconstruct a Graph instance from a JSON string representation created by the Graph.toJson() method.
        :param saveState:
        :return: Dictionary mapping the saved nodeIDs to the newly created nodes's IDs.
        """
        idMap = {}
        for id, nodeData in saveState:
            restoredNode = self.spawnNode(NODECLASSES[nodeData['class']], position=nodeData['position'], silent=True)
            idMap[int(id)] = restoredNode.ID
            inputs = nodeData['inputs']
            outputs = nodeData['outputs']
            for input in inputs:
                restoredNode.inputs[input[0]].setDefault(input[-1])
            for output in outputs:
                restoredNode.outputs[output[0]].setDefault(output[-1])
        for id, nodeData in saveState:
            id = int(id)
            for inputName, outputID in nodeData['inputConnections'].items():
                if inputName == 'Control':
                    continue
                outputNode, outputName = outputID.split(':O')
                outputNode = idMap[int(outputNode)]
                # print(id, nodeData['inputConnections'], outputNode, outputName)
                self.connect(str(outputNode), outputName, str(idMap[id]), inputName)

            for outputName, inputIDs in nodeData['outputConnections'].items():
                for inputID in inputIDs:
                    if not 'Control' in inputID:
                        continue
                    inputNode, inputName = inputID.split(':I')
                    inputNode = idMap[int(inputNode)]
                    # print(id, nodeData['inputConnections'], outputNode, outputName)
                    self.connect(str(idMap[id]), outputName, str(inputNode), inputName)

        self.update()
        return idMap

    def updateState(self, data):
        """
        Updates the current the Graph instance with the json representation of another, similar Graph instance.
        New Node instances are created for Nodes in the json data that are not already present.
        Also, all connections are removed and re-instanciated based on the provided json data.
        :param data:
        :return:
        """
        self.connections = {key: set() for key in self.connections.keys()}
        self.reverseConnections = {key: set() for key in self.reverseConnections.keys()}
        idMap = {}
        removeNodes = set(self.nodes.keys())
        for id, nodeData in data:
            idMap[int(id)] = int(id)
            if not int(id) in self.nodes.keys():
                restoredNode = self.spawnNode(NODECLASSES[nodeData['class']],
                                              position=nodeData['position'], silent=True)
                thisNode = restoredNode
            else:
                thisNode = self.nodes[int(id)]
            removeNodes.discard(thisNode.ID)
            inputs = nodeData['inputs']
            outputs = nodeData['outputs']
            for input in inputs:
                thisNode.inputs[input[0]].setDefault(input[-1])
            for output in outputs:
                thisNode.outputs[output[0]].setDefault(output[-1])
        for id, nodeData in data:
            id = int(id)
            for inputName, outputID in nodeData['inputConnections'].items():
                if inputName == 'Control':
                    continue
                outputNode, outputName = outputID.split(':O')
                outputNode = idMap[int(outputNode)]
                # print(id, nodeData['inputConnections'], outputNode, outputName)
                self.connect(str(outputNode), outputName, str(idMap[id]), inputName)

            for outputName, inputIDs in nodeData['outputConnections'].items():
                for inputID in inputIDs:
                    if not 'Control' in inputID:
                        continue
                    inputNode, inputName = inputID.split(':I')
                    inputNode = idMap[int(inputNode)]
                    # print(id, nodeData['inputConnections'], outputNode, outputName)
                    self.connect(str(idMap[id]), outputName, str(inputNode), inputName)
        for nodeID in removeNodes:
            self.deleteNode(self.nodes[nodeID])
        self.update()
        return idMap

    def loadDict(self, saveState):
        """
        Reconstruct a Graph instance from a JSON string representation created by the Graph.toJson() method.
        :param saveState:
        :return: Dictionary mapping the saved nodeIDs to the newly created nodes's IDs.
        """
        idMap = {}
        for id, nodeData in saveState.items():
            restoredNode = self.spawnNode(NODECLASSES[nodeData['class']], position=nodeData['position'], silent=True)
            idMap[int(id)] = restoredNode.ID
            inputs = nodeData['inputs']
            outputs = nodeData['outputs']
            for input in inputs:
                restoredNode.inputs[input[0]].setDefault(input[-1])
            for output in outputs:
                restoredNode.outputs[output[0]].setDefault(output[-1])
        for id, nodeData in saveState.items():
            id = int(id)
            for inputName, outputID in nodeData['inputConnections'].items():
                if inputName == 'Control':
                    continue
                outputNode, outputName = outputID.split(':O')
                outputNode = idMap[int(outputNode)]
                # print(id, nodeData['inputConnections'], outputNode, outputName)
                self.connect(str(outputNode), outputName, str(idMap[id]), inputName)

            for outputName, inputIDs in nodeData['outputConnections'].items():
                for inputID in inputIDs:
                    if not 'Control' in inputID:
                        continue
                    inputNode, inputName = inputID.split(':I')
                    inputNode = idMap[int(inputNode)]
                    # print(id, nodeData['inputConnections'], outputNode, outputName)
                    self.connect(str(idMap[id]), outputName, str(inputNode), inputName)

        self.update()
        return idMap

    def getPinWithID(self, pinID):
        """
        Get a reference to the pin object with pinID.
        :param pinID: string representing a Pin instance's ID.
        :return: Pin instance.
        """
        nodeID, pinName = pinID.split(':')
        pinName = pinName[1:]
        node = self.nodes[int(nodeID)]
        try:
            return node.getInputPin(pinName)
        except KeyError:
            return node.getOutputPin(pinName)

    def getNodeFromPinID(self, pinID):
        """
        Get a reference to the Node instance that has the pin object with pinID.
        :param pinID: string representing a Pin instance's ID.
        :return: Node instance.
        """
        nodeID, pinName = pinID.split(':')
        pinName = pinName[1:]
        return self.nodes[int(nodeID)]

    def getNewestNode(self):
        """
        Get a reference to the node instance that was created last.
        :return:
        """
        return self.newestNode

    def removeConnection(self, pinID):
        """
        Remove the connection that involves the Pin instance with pinID.
        :param pinID: string representing a Pin instance's ID.
        :return:
        """
        node = self.getNodeFromPinID(pinID)
        pinName = self.getPinWithID(pinID).name
        thisConn = None
        for conn in self.reverseConnections[node]:
            if any([conn.inputName == pinName, conn.outputName == pinName]):
                thisConn = conn
                break
        if thisConn:
            self.reverseConnections[node].remove(thisConn)
            self.connections[conn.outputNode].remove(thisConn)
            return
        thisConn = None
        for conn in self.connections[node]:
            if any([conn.inputName == pinName, conn.outputName == pinName]):
                thisConn = conn
                break
        if thisConn:
            self.connections[node].remove(thisConn)
            self.reverseConnections[conn.inputNode].remove(thisConn)

    def deleteNode(self, node):
        """
        Delete the node.
        :param node: Node instance.
        :return:
        """
        for inp in node.inputs.values():
            self.removeConnection(inp.ID)
        for out in node.outputs.values():
            self.removeConnection(out.ID)
        del self.nodes[node.ID]


class NodeThread(Thread):

    def __init__(self, node, cb, arg):
        # node.lock()
        self.node = node
        self.cb = cb
        self.arg = arg
        super(NodeThread, self).__init__()
        self.start()

    def run(self):
        super(NodeThread, self).run()
        self.node.run()
        self.node.notify()
        if self.cb:
            self.cb(self.arg)
        self.node.unlock()


class Connection(object):
    """
    Class representing a connection and storing information about involved Inputs and Outputs.
    """
    def __init__(self, outNode, outName, inpNode, inpName):
        self.outputNode = outNode
        self.outputName = outName
        self.inputNode = inpNode
        self.inputName = inpName

    def __hash__(self):
        return hash(''.join([str(i) for i in (self.outputNode, self.outputName, self.inputNode, self.inputName)]))

    def __getitem__(self, item):
        return self.__getattribute__(item)


class StatusListener(Thread):
    """
    Thread for listening to the remote graph interpreter for status updates.
    """
    def __init__(self, master, socket, statusQueue, statusLock):
        Thread.__init__(self)
        self.alive = True
        self.connection = socket
        self.master = master
        self.daemon = True
        self.statusQueue = statusQueue
        self.statusLock = statusLock
        self.start()

    # def kill(self):
    #     self.alive = False
    #     time.sleep(.1)
    #     self.listenSocket.shutdown(SHUT_RDWR)

    def run(self):
        while self.alive:
            try:
                message = self.connection.recv(1024).decode()
            except:
                pass
            else:
                self.statusLock.acquire()
                for ID in [i for i in message.split('#')if i]:
                    self.master.executedBuffer.append(int(ID))
                self.statusLock.release()
                self.master.requestUpdate()





