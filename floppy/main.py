from floppy.graph import Graph
from floppy.painter import Painter2D, MainWindow
import sys
from PyQt5.QtWidgets import QApplication


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
    win.show()
    sys.exit(app.exec_())
    # try:
    #     sys.exit(app.exec_())
    # except KeyboardInterrupt:
    #     print('Keyboard Interrupt. Shutting down gracefully.')
    #     win.killRunner()




