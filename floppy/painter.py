# import sys
# from PyQt5 import QtCore
# from PyQt5 import QtGui
# from PyQt5 import QtOpenGL
from floppy.node import InputNotAvailable
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import *


class Painter(QWidget):
    def decorateNode(self, node, position):
        return node


class Painter2D(Painter):
    PINCOLORS = {str: QColor(255, 190, 0),
                 int: QColor(0, 115, 130),
                 float: QColor(0, 200, 0),
                 object: QColor(190, 190, 190)}
    nodes = []
    scale = 1.
    globalOffset = QPoint(0, 0)
    drag = False
    inputPinPositions = []
    clickedPin = None
    clickedNode = None
    nodePoints = []
    downOverNode = False
    
    def __init__(self, parent=None):
        super(Painter2D, self).__init__(parent)
        self.graph = None
        self.looseConnection = None
        self.pinPositions = {}


    def registerGraph(self, graph):
        self.graph = graph

    def wheelEvent(self, event):
        # self.scale += event.deltaX()
        up = event.angleDelta().y()>0
        if up:
            x = 1.1
        else:
            x = .9
        self.scale *= x
        self.repaint()
        self.update()




    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            self.drag = event.pos()
        if event.button() == Qt.LeftButton:
            for point, i in self.inputPinPositions:
                # print(event.pos(), point, i)
                if abs(event.pos().x() - point.x()) < 7 * self.scale and abs(event.pos().y() - point.y()) < 7 * self.scale:
                    self.clickedPin = i
                    self.update()
                    return
            for point, i in self.outputPinPositions:
                # print(event.pos(), point, i)
                # w = node.__size__[0]*100
                if abs(event.pos().x() - point.x()) < 7 * self.scale and abs(event.pos().y() - point.y()) < 7 * self.scale:
                    self.clickedPin = i
                    self.update()
                    return
            for nodePoints in self.nodePoints:
                x1 = nodePoints[0].x()
                x2 = nodePoints[1].x() #+ x1
                y1 = nodePoints[0].y()
                y2 = nodePoints[1].y() #+ y1
                xx = event.pos()
                yy = xx.y()
                xx = xx.x()
                if x1 < xx < x2 and y1 < yy < y2:
                    self.clickedNode = nodePoints[-1]
                    self.update()
                    self.downOverNode = event.pos()
                    break


    def mouseReleaseEvent(self, event):
        super(Painter2D, self).mouseReleaseEvent(event)
        self.drag = False
        self.downOverNode = False
        self.looseConnection = False
        self.clickedPin = None
        self.update()


    def mouseMoveEvent(self, event):
        super(Painter2D, self).mouseMoveEvent(event)
        if self.drag:
            self.globalOffset += event.pos()-self.drag
            self.drag = event.pos()
            self.update()
        if self.downOverNode:
            node = self.clickedNode
            newPos = (event.pos() - self.downOverNode)*self.scale**-1
            oldPos = QPoint(node.__pos__[0], node.__pos__[1])
            newPos = oldPos + newPos
            node.__pos__ = (newPos.x(), newPos.y())
            self.downOverNode = event.pos()
            self.update()
        else:
            self.drawLooseConnection(event.pos())
            self.update()


    def paintEvent(self, event):
        self.inputPinPositions = []
        self.outputPinPositions = []
        self.nodePoints = []
        super(Painter2D, self).paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.HighQualityAntialiasing)
        self.drawConnections(painter)

        painter.translate(self.width()/2. + self.globalOffset.x(), self.height()/2. + self.globalOffset.y())
        painter.scale(self.scale, self.scale)
        #painter.translate(self.width()/2., self.height()/2.)
        painter.setRenderHint(QPainter.HighQualityAntialiasing)
        for j, node in enumerate(self.nodes):
            j *= 3
            j += 1
            pen = QPen()
            if self.clickedNode == node:
                pen.setColor(Qt.green)
                painter.setBrush(QColor(75, 75, 75))
            else:
                pen.setColor(Qt.black)
                painter.setBrush(QColor(55, 55, 55))

            font = QFont('Helvetica', 12)
            painter.setFont(font)
            path = QPainterPath()
            x = node.__pos__[0]# + self.globalOffset.x()
            y = node.__pos__[1]# + self.globalOffset.y()
            w = node.__size__[0]*100
            h = node.__size__[1]*16+40
            # painter.translate(xxx, yyy)
            # x=0
            # y=0

            path.addRoundedRect(x, y, w, h, 50, 5)
            self.nodePoints.append((QPoint(x, y)*painter.transform(), QPoint(x+w, y+h)*painter.transform(), node))
            pen.setColor(Qt.black)
            painter.setPen(pen)

            painter.fillPath(path, QColor(55,55,55))
            # painter.drawRoundedRect(node.pos[0], node.pos[1], node.size[0], node.size[1], 50, 5)
            painter.drawPath(path)
            pen.setColor(QColor(150, 150, 150))
            painter.setPen(pen)
            painter.drawText(x, y, w, h, Qt.AlignHCenter, node.__class__.__name__)
            painter.setBrush(QColor(40, 40, 40))
            drawOffset = 25
            for i, inputPin in enumerate(node.inputPins.values()):
                # pen.setColor(QColor(255, 190, 0))
                pen.setColor(Painter2D.PINCOLORS[inputPin.info.varType])
                pen.setWidth(2)
                painter.setPen(pen)
                if inputPin.ID == self.clickedPin:
                    pen.setColor(Qt.red)
                    painter.setPen(pen)

                painter.drawEllipse(x-4, y+drawOffset+8, 8, 8)
                point = QPoint(x, y+drawOffset+12) * painter.transform()
                # self.pinPositions.append((point, i+j))
                self.inputPinPositions.append((point, inputPin.ID))
                drawOffset += 16
                try:
                    text = inputPin.info()
                except InputNotAvailable:
                    text = 'None'
                self.drawLineEdit(x, y+drawOffset+8, w, h, text, painter, Qt.AlignLeft)
            for k, outputPin in enumerate(node.outputPins.values()):
                # pen.setColor(QColor(0, 115, 130))
                pen.setColor(Painter2D.PINCOLORS[outputPin.info.varType])
                pen.setWidth(2)
                painter.setPen(pen)
                if outputPin.ID == self.clickedPin:
                    pen.setColor(Qt.red)
                    painter.setPen(pen)
                painter.drawEllipse(x + w-4, y+drawOffset+8, 8, 8)
                point = QPoint(x + w-4, y+drawOffset+12) * painter.transform()
                drawOffset += 16
                self.outputPinPositions.append((point, outputPin.ID))
                self.drawLineEdit(x, y+drawOffset+8, w, h, 'out', painter, Qt.AlignRight)
            # trans = painter.transform()
        self.pinPositions = {value[1]: value[0] for value in self.inputPinPositions+self.outputPinPositions}
        # self.drawConnections(painter)

    def drawConnections(self, painter):
        if not self.graph:
            print('No graph connected yet.')
            return
        if not self.pinPositions:
            return

        if self.looseConnection and self.clickedPin:
            start = self.pinPositions[self.clickedPin]
            if ':I' in self.clickedPin:
                start, end = self.looseConnection, start
            else:
                end = self.looseConnection
            self.drawBezier(start, end, Qt.white, painter)

        for outputNode, connList in self.graph.connections.items():
            for info in connList:
                # print(info)
                outputID = outputNode.getOutputID(info['outputName'])
                inputID = info['inputNode'].getInputID(info['inputName'])
                varType = outputNode.getOutputInfo(info['outputName']).varType
                start = self.pinPositions[outputID]
                end = self.pinPositions[inputID]
                color = Painter2D.PINCOLORS[varType]
                self.drawBezier(start, end, color, painter)

    def drawLooseConnection(self, position):
        self.looseConnection = position

    def drawBezier(self, start, end, color, painter):
                pen = QPen()
                pen.setColor(color)
                pen.setWidth(2*self.scale)
                painter.setPen(pen)
                path = QPainterPath()
                path.moveTo(start)
                diffx = abs((start.x()-end.x())/2.)
                if diffx < 150 * self.scale:
                    diffx = 150 * self.scale
                p21 = start.x()+diffx
                p22 = start.y()
                p31 = end.x()-diffx
                p32 = end.y()
                path.cubicTo(p21, p22, p31, p32, end.x(), end.y())
                painter.drawPath(path)

    def drawLineEdit(self, x, y, w, h, text, painter, alignment):
        text = str(text)
        pen = QPen(Qt.darkGray)
        painter.setPen(pen)
        xx, yy, ww, hh = x+(w)/2.-(w-25)/2., y-18, w-25, 12
        painter.drawRoundedRect(xx, yy, ww, hh, 2, 20)
        pen.setColor(Qt.gray)
        painter.setFont(QFont('Helvetica', 8))
        painter.setPen(pen)
        painter.drawText(xx+5, yy-3, ww-10, hh+5, alignment, text)

    def registerNode(self, node, position):
        node.__painter__ = {'position': position}
        node.__pos__ = position
        node.__size__ = (1, len(node.inputs) + len(node.outputs))

        # for inp in node.inputs.values():
        #     color = Painter2D.PINCOLORS[inp.varType]
        #     name = inp.name
        #     try:
        #         value = inp()
        #     except InputNotAvailable:
        #         value = inp.default
        self.nodes.append(node)
        # exit()


class MainWindow(QMainWindow):

    def __init__(self, parent=None, painter=None):
        super(MainWindow, self).__init__(parent)

        self.resize(900, 700)
        self.setWindowTitle('Node Draw Test')

        self.initActions()
        self.initMenus()

        drawWidget = painter
        drawWidget.setAutoFillBackground(True)
        p = self.palette()
        p.setColor(drawWidget.backgroundRole(), QColor(50,50,50))
        drawWidget.setPalette(p)
        # drawWidget.registerNode(x)
        self.setCentralWidget(drawWidget)

        # timer = QtCore.QTimer(self)
        # timer.setInterval(20)
        # # QtCore.QObject.connect(timer, QtCore.SIGNAL('timeout()'), glWidget.spin)
        # timer.timeout.connect(glWidget.spin)
        # timer.start()


    def initActions(self):
        self.exitAction = QAction('Quit', self)
        self.exitAction.setShortcut('Ctrl+Q')
        self.exitAction.setStatusTip('Exit application')
        # self.connect(self.exitAction, QtCore.SIGNAL('triggered()'), self.close)
        self.exitAction.triggered.connect(self.close)

    def initMenus(self):
        menuBar = self.menuBar()
        fileMenu = menuBar.addMenu('&File')
        fileMenu.addAction(self.exitAction)

    def close(self):
        qApp.quit()

# app = QApplication(sys.argv)
#
# win = MainWindow()
# win.show()
#
#
# sys.exit(app.exec_())