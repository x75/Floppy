import json
import zlib
import io
import time
from floppy.node import ControlNode
from floppy.runner import Runner, sendCommand
from socket import AF_INET, SOCK_STREAM, socket, SHUT_RDWR, timeout, SHUT_RDWR, SO_REUSEADDR, SOL_SOCKET
from floppy.node import NODECLASSES
from threading import Thread, Lock
from queue import Queue


def dummy(nodeClass):
    return nodeClass


class Graph(object):
    nextFreeNodeID = 0
    nodes = {}

    def __init__(self, painter=None):
        self._requestUpdate = False
        self.executedBuffer = []
        self.statusLock = None
        self.connected = False
        self.nextFreeNodeID = 0
        self.nodes = {}
        self.connections = {}
        self.runner = None
        self.reverseConnections = {}
        if painter:
            self.painter = painter
            painter.registerGraph(self)
        else:
            self.painter = dummy

    def spawnAndConnect(self):
        if not self.runner:
            self.runner = Runner()
        self.connect2Runner()
        self.statusLock = Lock()
        self.statusQueue = Queue(100)
        self.statusListener = StatusListener(self, self.clientSocket, self.statusQueue, self.statusLock)

    def __getattr__(self, item):
        if item == 'newID':
            newID = self.nextFreeNodeID
            self.nextFreeNodeID += 1
            return newID
        else:
            return super(Graph, self).__getattr__(item)

    def requestUpdate(self):
        self._requestUpdate = True

    def needsUpdate(self):
        if self._requestUpdate:
            self._requestUpdate = False
            return True

    def spawnNode(self, nodeClass, connections=None, position=(0, 0), silent=False):
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
        :param node:
        :return:
        """
        return self.reverseConnections[node]

    def getConnectionOfInput(self, inp):
        for con in self.getConnectionsTo(self.nodes[int(inp.ID.partition(':')[0])]):
            if con['inputName'] == inp.name:
                return con

    def getConnectionsOfOutput(self, output):
        node = self.nodes[int(output.ID.partition(':')[0])]
        return [con for con in self.getConnectionsFrom(node) if con['outputName'] == output.name]


    def update(self):
        try:
            self.painter.repaint()
            self.painter.update()
        except AttributeError:
            pass

    def getExecutionHistory(self):
        self.statusLock.acquire()
        history = self.executedBuffer[:]
        self.statusLock.release()
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

    def testRun(self):
        if not self.runner:
            self.runner = Runner()
        sendCommand('PAUSE')
        data = self.serialize()
        self.sendUpdate(data)
        sendCommand('UPDATE')
        import time
        time.sleep(.5)
        sendCommand('UNPAUSE')
        return

        import time
        time.sleep(2)
        sendCommand('PAUSE')
        time.sleep(1)
        sendCommand('KILL')
        del r

    def updateRunner(self):
        self.executedBuffer = []
        sendCommand('PAUSE')
        data = self.serialize()
        self.sendUpdate(data)
        sendCommand('UPDATE')

    def serialize(self):
        data = self.toJson()
        return data
        return zlib.compress(data.encode('utf-8'))

    def convert_to_bytes(self, no):
        """
        Returns a 4 byte large representation of an integer.
        :param no: Integer
        :return: bytearray representation of input Integer.
        """
        result = bytearray()
        result.append(no & 255)
        for i in range(3):
            no >>= 8
            result.append(no & 255)
        return result

    def connect2Runner(self):
        self.clientSocket = socket(AF_INET, SOCK_STREAM)
        self.clientSocket
        host = '127.0.0.1'
        port = 7237
        self.clientSocket.settimeout(3)
        self.clientSocket.connect((host, port))
        # self.clientSocket.listen(1)
        self.connected = True

    def receiveStatus(self):
        if not self.connected:
            self.connect2Runner()
        pass

    def sendUpdate(self, message):
        """
        Sends a message to the error server specified in the INI file.
        :param message: String representation of the message
        :param config: Reference to a plugin manager instance.
        :return: None
        """
        if not self.connected:
            self.connect2Runner()
        import struct
        # Prefix each message with a 4-byte length (network byte order)
        msg = struct.pack('>I', len(message)) + message.encode('utf-8')
        self.clientSocket.sendall(msg)
        return
        #message = message.encode('utf-8')
        #self.clientSocket.sendall(message)
        ##return

        message = message.encode('utf-8')
        bs = self.convert_to_bytes(len(message))
        message = io.TextIOWrapper(io.BytesIO(message))
        self.clientSocket.send(bs)
        chunk = message.read(1024)
        while chunk:
            self.clientSocket.send(chunk)
            chunk = message.read(1024)
        # printer('Report sent')
        _ = self.clientSocket.recv(1024).decode()
        # printer(answer)
        # self.clientSocket.close()



    def save(self):
        saveState = self.toJson()
        with open('save.json', 'w') as fp:
            fp.write(saveState)

    def toJson(self):
        return json.dumps({node.ID: node.save() for node in self.nodes.values()})

    def killRunner(self):
        sendCommand('KILL')
        self.clientSocket.close()
        self.runner = None

    def pauseRunner(self):
        sendCommand('PAUSE')

    def unpauseRunner(self):
        sendCommand('UNPAUSE')

    def stepRunner(self):
        sendCommand('STEP')

    def gotoRunner(self, nextID):
        sendCommand('GOTO{}'.format(nextID))

    def load(self, fileName):

        with open('save.json', 'r') as fp:
            saveState = json.loads(fp.read())
        self.loadDict(saveState)

    def loadDict(self, saveState):
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
        nodeID, pinName = pinID.split(':')
        pinName = pinName[1:]
        node = self.nodes[int(nodeID)]
        try:
            return node.getInputPin(pinName)
        except KeyError:
            return node.getOutputPin(pinName)

    def getNodeFromPinID(self, pinID):
        nodeID, pinName = pinID.split(':')
        pinName = pinName[1:]
        return self.nodes[int(nodeID)]

    def getNewestNode(self):
        return self.newestNode


class Connection(object):
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





