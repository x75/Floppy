
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
        self.reverseConnections[newNode] = []
        self.connections[newNode] = []
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
        outInfo = outNode.getOutputInfo(out)
        inpInfo = inpNode.getInputInfo(inp)
        if not outInfo.varType == inpInfo.varType:
            raise TypeError('Output \'{}\' of node {} and input \'{}\' of not {} don\'t match.'.format(out,
                                                                                                       str(outNode),
                                                                                                       inp,
                                                                                                       str(inpNode)))
        print('Connect output \'{1}\' of node {0} to input \'{3}\' of node {2}'.format(str(outNode),
                                                                                       out,
                                                                                       str(inpNode),
                                                                                       inp))
        self.connections[outNode].append({'outputName': out,
                                          'inputName': inp,
                                          'inputNode': inpNode})
        self.reverseConnections[inpNode].append({'outputName': out,
                                                 'inputName': inp,
                                                 'outputNode': outNode})
        self.update()

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
        return [con for con in self.getConnectionsFrom(self.nodes[int(output.ID.partition(':')[0])]) if con['outputName'] == output.name]


    def update(self):
        pass

    def execute(self):
        """
        Execute the Graph instance.

        First, the execution loop will set itself up to terminate after the first iteration.
        Next, every node is given the chance to run if all perquisites are met.
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
                    try:
                        node.run()
                    except:
                        RuntimeError('Uncaught exception while executing node {}.'.format(node))
                    else:
                        node.notify()



