import json
from floppy.node import ControlNode

def dummy(nodeClass):
    return nodeClass


class Graph(object):
    nextFreeNodeID = 0
    nodes = {}

    def __init__(self, painter=None):
        self.connections = {}
        self.reverseConnections = {}
        if painter:
            self.painter = painter
            painter.registerGraph(self)
        else:
            self.painter = dummy

    def __getattr__(self, item):
        if item == 'newID':
            newID = Graph.nextFreeNodeID
            Graph.nextFreeNodeID += 1
            return newID
        else:
            return super(Graph, self).__getattr__(item)

    def spawnNode(self, nodeClass, connections=None, position=(0, 0)):
        # nodeClass = self.decorator(nodeClass, position)
        newNode = nodeClass(self.newID, self)
        self.reverseConnections[newNode] = set()
        self.connections[newNode] = set()
        if connections:
            self._spawnConnections(connections, newNode)
        self.painter.registerNode(newNode, position)
        Graph.nodes[newNode.ID] = newNode

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
        self.painter.repaint()
        self.painter.update()

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

    def save(self):
        saveState = {node.ID: node.save() for node in self.nodes.values()}
        with open('save.json', 'w') as fp:
            fp.write(json.dumps(saveState))

    def load(self, fileName):
        from floppy.node import NODECLASSES
        with open('save.json', 'r') as fp:
            saveState = json.loads(fp.read())
        idMap = {}
        for id, nodeData in saveState.items():
            restoredNode = self.spawnNode(NODECLASSES[nodeData['class']], position=nodeData['position'])
            idMap[int(id)] = restoredNode.ID
        for id, nodeData in saveState.items():
            id = int(id)
            for inputName, outputID in nodeData['inputConnections'].items():
                outputNode, outputName = outputID.split(':O')
                outputNode = idMap[int(outputNode)]
                # print(id, nodeData['inputConnections'], outputNode, outputName)
                self.connect(str(outputNode),outputName,str(idMap[id]), inputName)

        self.update()


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


