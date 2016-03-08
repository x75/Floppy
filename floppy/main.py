from floppy.graph import Graph
from floppy.node import TestNode
from floppy.painter import Painter


def run():
    test()


def test():
    graph = Graph(painter=Painter())
    node0 = graph.spawnNode(TestNode)
    inputPin = node0.getInputPin('strInput')
    conns = {'outputs': [('strOutput', node0, 'strInput')]}#, 'inputs': [('strInput', node0, 'strOutput')]}
    node1 = graph.spawnNode(TestNode, connections=conns)
    # node0.inProgress = 5
    node0.inputs['strInput'].set('Hello')
    graph.execute()


