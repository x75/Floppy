from floppy.graph import Graph
from floppy.painter import Painter2D, MainWindow
import sys
from PyQt5.QtWidgets import QApplication
import argparse


def run():
    app = QApplication(sys.argv)
    painter = test()
    testUI(app, painter)


def test():
    painter = Painter2D()
    Graph(painter=painter)

    return painter


def testUI(app, painter):
    win = MainWindow(painter=painter)
    win.setArgs(parseArgv())
    win.show()
    sys.exit(app.exec_())
    # try:
    #     sys.exit(app.exec_())
    # except KeyboardInterrupt:
    #     print('Keyboard Interrupt. Shutting down gracefully.')
    #     win.killRunner()

def parseArgv():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', action='store_true', required=False)
    parser.add_argument('--test', action='store_true', required=False, default=False)
    args = parser.parse_args()
    return args


