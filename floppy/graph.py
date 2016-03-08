
def dummy(nodeClass):
    return nodeClass


class Graph(object):
    nextFreeNodeID = 0
    nodes = {}

    def __init__(self, painter=None):
        self.connections = {}
        if painter:
            self.decorator = painter.decorateNode
        else:
            self.decorator = dummy

    def __getattr__(self, item):
        if item == 'newID':
            newID = Graph.nextFreeNodeID
            Graph.nextFreeNodeID += 1
            return newID
        else:
            return super(Graph, self).__getattr__(item)

    def spawnNode(self, nodeClass, connections=None, position=(0, 0)):
        nodeClass = self.decorator(nodeClass)
        newNode = nodeClass(self.newID)
        if connections:
            self._spawnConnections(connections, newNode)
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
        self.connections[outNode] = {'outputName': out,
                                     'inputName': inp,
                                     'inputNode': inpNode}
        self.update()

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
        while running:
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



