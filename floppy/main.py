from floppy.graph import Graph
from floppy.node import TestNode, TestNode2
from floppy.painter import Painter, Painter2D, MainWindow
import sys
from PyQt5.QtWidgets import QApplication


def run():
    app = QApplication(sys.argv)
    painter = test()
    testUI(app, painter)


def test():
    painter = Painter2D()
    graph = Graph(painter=painter)
    node0 = graph.spawnNode(TestNode, position=(200,0))
    inputPin = node0.getInputPin('strInput')
    node3 = graph.spawnNode(TestNode2, position=(-200,0))
    conns = {'outputs': [('strOutput', node0, 'strInput')], 'inputs': [('strInput', node3, 'strOutput')]}
    node1 = graph.spawnNode(TestNode, connections=conns, position=(0,0))

    # node0.inProgress = 5
    node1.inputs['strInput'].set('Hello')
    graph.execute()
    print(repr(node1))
    return painter


def testUI(app, painter):
    # class MyWidget(QMainWindow):
    #     def __init__(self):
    #         super(MyWidget, self).__init__()
    #         uic.loadUi('/home/jens/Floppy/floppy/ressources/test.ui', self)
    # app = QApplication(sys.argv)
    # window = MyWidget()
    # window.show()

    win = MainWindow(painter=painter)
    win.show()
    sys.exit(app.exec_())




