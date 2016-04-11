import os
# import sys
# from PyQt5 import QtCore
# from PyQt5 import QtGui
# from PyQt5 import QtOpenGL
from floppy.node import InputNotAvailable, ControlNode
from floppy.mainwindow import Ui_MainWindow
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
                 object: QColor(190, 190, 190),
                 bool: QColor(190, 0, 0),}
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
        self.drawItems = []
        self.drawItemsOfNode = {}
        self.watchingItems = set()
        self.setMouseTracking(True)
        self.contextSensitive = True

    def registerWatchingItem(self, item):
        self.watchingItems.add(item)

    def removeWatchingItem(self, item):
        self.watchingItems.remove(item)

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
        self.repaint()  # Dirty trick to make sure the connection beziers are drawn at the same zoom level as the nodes.
        self.update()




    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            self.drag = event.pos()
        if event.button() == Qt.LeftButton:
            for item in self.watchingItems:
                item.watchDown(event.pos())
            for drawItem in self.drawItems:
                if issubclass(type(drawItem), Selector):
                    # print(drawItem.data.name, drawItem._x,drawItem._y, event.pos())
                    # print(drawItem.data.name, drawItem._xx,drawItem._yy)
                    if drawItem.collide(event.pos()):
                        print(drawItem)

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
                    # print(self.clickedNode)
                    self.update()
                    self.downOverNode = event.pos()
                    break

    def getOutputPinAt(self, pos):
        for point, pin in self.outputPinPositions:
            if abs(pos.x() - point.x()) < 7 * self.scale and abs(pos.y() - point.y()) < 7 * self.scale:
                return pin

    def getInputPinAt(self, pos):
        for point, pin in self.inputPinPositions:
            if abs(pos.x() - point.x()) < 7 * self.scale and abs(pos.y() - point.y()) < 7 * self.scale:
                return pin

    def mouseReleaseEvent(self, event):
        super(Painter2D, self).mouseReleaseEvent(event)
        if event.button() == Qt.LeftButton and self.looseConnection and self.clickedPin:
            valid = True
            if ':I' in self.clickedPin:
                inputNodeID, _, inputName = self.clickedPin.partition(':I')
                try:
                    outputNodeID, _, outputName = self.getOutputPinAt(event.pos()).partition(':O')
                except AttributeError:
                    valid = False
            else:
                outputNodeID, _, outputName = self.clickedPin.partition(':O')
                try:
                    inputNodeID, _, inputName = self.getInputPinAt(event.pos()).partition(':I')
                except AttributeError:
                    valid = False
            if valid:
                try:
                    self.graph.connect(outputNodeID, outputName, inputNodeID, inputName)
                except TypeError:
                    print('Cannot connect pins of different type')
            else:
                print('Do something. NOW!!!')
                self.openDialog(event)
        self.drag = False
        self.downOverNode = False
        self.looseConnection = False
        self.clickedPin = None
        self.repaint()
        self.update()

    def openDialog(self, event):
        dialog = NodeDialog(self, event, self.clickedPin, self.graph)
        self.dialog = dialog
        dialog.show()

    def mouseMoveEvent(self, event):
        for drawItem in self.watchingItems:
            drawItem.watch(event.pos())
        super(Painter2D, self).mouseMoveEvent(event)

        if self.drag:
            self.globalOffset += event.pos()-self.drag
            self.drag = event.pos()
            # self.repaint()
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
        self.drawGrid(painter)
        try:
            self.drawConnections(painter)
        except KeyError:
            pass


        painter.translate(self.width()/2. + self.globalOffset.x(), self.height()/2. + self.globalOffset.y())
        self.center = QPoint(self.width()/2. + self.globalOffset.x(), self.height()/2. + self.globalOffset.y())
        painter.scale(self.scale, self.scale)
        #painter.translate(self.width()/2., self.height()/2.)
        painter.setRenderHint(QPainter.HighQualityAntialiasing)
        # painter.drawEllipse(QPoint(0,0),5,5)
        for j, node in enumerate(self.nodes):
            j *= 3
            j += 1
            pen = QPen()
            pen.setWidth(2)
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
            # for i, inputPin in enumerate(node.inputPins.values()):
            for i, drawItem in enumerate(self.drawItemsOfNode[node]['inp']):
                inputPin = drawItem.data
                # pen.setColor(QColor(255, 190, 0))
                pen.setColor(Painter2D.PINCOLORS[inputPin.info.varType])
                pen.setWidth(2)
                painter.setPen(pen)
                if inputPin.ID == self.clickedPin:
                    pen.setColor(Qt.red)
                    painter.setPen(pen)
                if inputPin.name == 'Control':
                    painter.drawEllipse(x-4+w/2., y-4, 8, 8)
                    point = QPoint(x+w/2., y) * painter.transform()
                    self.inputPinPositions.append((point, inputPin.ID))
                    continue
                else:
                    painter.drawEllipse(x-4, y+drawOffset+8, 8, 8)
                    point = QPoint(x, y+drawOffset+12) * painter.transform()
                # self.pinPositions.append((point, i+j))
                self.inputPinPositions.append((point, inputPin.ID))
                drawOffset += 16
                if self.graph.getConnectionOfInput(inputPin):
                    text = inputPin.name
                    self.drawLabel(x, y+drawOffset+8, w, h, text, painter, Qt.AlignLeft)
                else:
                    try:
                        text = inputPin.info()
                    except InputNotAvailable:
                        text = inputPin.name
                    self.drawLineEdit(x, y+drawOffset+8, w, h, text, painter, Qt.AlignLeft)
            # for k, outputPin in enumerate(node.outputPins.values()):
            finalBuffer = None
            for k, drawItem in enumerate(self.drawItemsOfNode[node]['out']):
                outputPin = drawItem.data
                # pen.setColor(QColor(0, 115, 130))
                pen.setColor(Painter2D.PINCOLORS[outputPin.info.varType])
                pen.setWidth(2)
                painter.setPen(pen)
                if outputPin.ID == self.clickedPin:
                    pen.setColor(Qt.red)
                    painter.setPen(pen)
                if outputPin.name == 'Final':
                    finalBuffer = (k, drawItem)
                    continue
                    # painter.drawEllipse(x-4+w/2., y+10+drawOffset, 8, 8)
                    # point = QPoint(x+w/2., y+drawOffset+14) * painter.transform()
                    # self.outputPinPositions.append((point, outputPin.ID))
                    # continue
                else:
                    painter.drawEllipse(x + w-4, y+drawOffset+8, 8, 8)
                    point = QPoint(x + w-4, y+drawOffset+12) * painter.transform()
                drawOffset += 16
                self.outputPinPositions.append((point, outputPin.ID))
                if not outputPin.info.select:
                    text = outputPin.name
                    self.drawLabel(x, y+drawOffset+8, w, h, text, painter, Qt.AlignRight)
                else:
                    text = outputPin.name
                    # self.drawSelector(x, y+drawOffset+8, w, h, text, painter, Qt.AlignRight)
                drawItem.update(x, y+drawOffset+8, w, h, painter.transform())
                drawItem.draw(painter)
            if finalBuffer:
                k, drawItem = finalBuffer
                outputPin = drawItem.data
                pen.setColor(Painter2D.PINCOLORS[outputPin.info.varType])
                pen.setWidth(2)
                painter.setPen(pen)
                if outputPin.ID == self.clickedPin:
                    pen.setColor(Qt.red)
                    painter.setPen(pen)
                painter.drawEllipse(x-4+w/2., y+10+drawOffset, 8, 8)
                point = QPoint(x+w/2., y+drawOffset+14) * painter.transform()
                self.outputPinPositions.append((point, outputPin.ID))

            # trans = painter.transform()
        self.pinPositions = {value[1]: value[0] for value in self.inputPinPositions+self.outputPinPositions}
        # self.drawConnections(painter)
        self.transform = painter.transform()

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
                rotate = None
                if issubclass(type(info['inputNode']), ControlNode) and info['inputName'] == 'Control':
                    rotate = 'input'
                elif issubclass(type(info['outputNode']), ControlNode) and info['outputName'] == 'Final':
                    rotate = 'output'
                self.drawBezier(start, end, color, painter, rotate)

    def drawLooseConnection(self, position):
        self.looseConnection = position

    def drawBezier(self, start, end, color, painter, rotate=None):
                pen = QPen()
                pen.setColor(color)
                pen.setWidth(2*self.scale)
                painter.setPen(pen)
                path = QPainterPath()
                path.moveTo(start)
                diffx = abs((start.x()-end.x())/2.)
                if diffx < 100 * self.scale:
                    diffx = 100 * self.scale
                if rotate == 'input':
                    p21 = start.x()+diffx
                    p22 = start.y()
                    p31 = end.x()
                    p32 = end.y() - 100*self.scale
                elif rotate == 'output':
                    p21 = start.x()
                    p22 = start.y() + 100 * self.scale
                    p31 = end.x()-diffx
                    p32 = end.y()
                else:
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

    def drawLabel(self, x, y, w, h, text, painter, alignment):
        text = str(text)
        pen = QPen(Qt.gray)
        painter.setPen(pen)
        xx, yy, ww, hh = x+(w)/2.-(w-25)/2., y-18, w-18, 12
        painter.setFont(QFont('Helvetica', 8))
        painter.setPen(pen)
        painter.drawText(xx+5, yy-3, ww-10, hh+5, alignment, text)

    def drawSelector(self, x, y, w, h, text, painter, alignment):
        text = str(text)
        pen = QPen(Qt.darkGray)
        painter.setPen(pen)
        xx, yy, ww, hh = x+(w)/2.-(w-25)/2., y-18, w-25, 12
        painter.drawRoundedRect(xx, yy, ww, hh, 2, 20)
        painter.setFont(QFont('Helvetica', 8))
        painter.setPen(pen)
        painter.drawText(xx-5, yy-3, ww-20, hh+5, alignment, text)
        pen.setColor(Qt.gray)
        # pen.setWidth(3)
        painter.setPen(pen)
        painter.setBrush(QBrush(Qt.gray))
        points = QPoint(xx+w-40, yy+2), QPoint(xx+10-40 +w, yy+2), QPoint(xx+5+w-40, yy+9)
        painter.drawPolygon(*points)

    def registerNode(self, node, position, silent=False):
        if not silent:
            self.parent().parent().parent().parent().statusBar.showMessage('Spawned node of class \'{}\'.'
                                                                           .format(type(node).__name__), 2000)
        node.__painter__ = {'position': position}
        node.__pos__ = position
        node.__size__ = (1, len(node.inputs) + len(node.outputs))
        node.__size__ = (1, node.__size__[1] if not issubclass(type(node), ControlNode) else node.__size__[1]-2)
        self.nodes.append(node)
        self.drawItemsOfNode[node] = {'inp': [], 'out': []}
        for out in node.outputPins.values():
            if out.info.select:
                s = Selector(node, out, self)
            else:
                s = OutputLabel(node, out, self)
            self.drawItems.append(s)
            self.drawItemsOfNode[node]['out'].append(s)
        for out in node.inputPins.values():
            if out.info.select:
                s = Selector(node, out, self)
            else:
                s = InputLabel(node, out, self)
            self.drawItems.append(s)
            self.drawItemsOfNode[node]['inp'].append(s)

    def drawGrid(self, painter):
        color = 105

        spacing = 100 * self.scale
        while spacing < 25:
            spacing *= 9
            color = 70 + (color-70) / 2.5
        if color < 0:
            return


        pen = QPen()
        pen.setColor(QColor(color, color, color))
        pen.setStyle(Qt.DashLine)
        painter.setPen(pen)
        verticalN = int(self.width() / spacing / 2) + 1
        horizontalN = int(self.height() / spacing / 2) + 1
        for i in range(verticalN):
            # painter.drawLine(self.width()/2 + self.globalOffset.x()+i*spacing, 0, self.width()/2+ self.globalOffset.x() + i*spacing, self.height())
            painter.drawLine(self.width()/2 +i*spacing, 0, self.width()/2 + i*spacing, self.height())
            # painter.drawLine(QPoint(self.width()/2 + self.globalOffset.x()-i*spacing, 0), QPoint(self.width()/2+ self.globalOffset.x() - i*spacing, self.height()))
            painter.drawLine(QPoint(self.width()/2 -i*spacing, 0), QPoint(self.width()/2 - i*spacing, self.height()))

        for i in range(horizontalN):
            # painter.drawLine(0, self.height()/2+self.globalOffset.y()+i*spacing, self.width(), self.height()/2+self.globalOffset.y()+i*spacing)
            painter.drawLine(0, self.height()/2+i*spacing, self.width(), self.height()/2+i*spacing)
            # painter.drawLine(0, self.height()/2+self.globalOffset.y()-i*spacing, self.width(), self.height()/2+self.globalOffset.y()-i*spacing)
            painter.drawLine(0, self.height()/2-i*spacing, self.width(), self.height()/2-i*spacing)


class MainWindow(QMainWindow, Ui_MainWindow):

    def __init__(self, parent=None, painter=None):
        super(MainWindow, self).__init__(parent)

        iconRoot = os.path.realpath(__file__)
        iconRoot = os.path.join(os.path.dirname(os.path.dirname(iconRoot)), 'floppy')
        self.iconRoot = os.path.join(iconRoot, 'ressources')

        self.setupUi(self)

        self.setWindowIcon(QIcon(os.path.join(self.iconRoot, 'appIcon.png')))

        self.resize(900, 700)
        self.setWindowTitle('Node Draw Test')

        self.initActions()
        self.initMenus()

        drawWidget = painter
        drawWidget.setAutoFillBackground(True)
        p = self.palette()
        p.setColor(drawWidget.backgroundRole(), QColor(70, 70, 70))
        drawWidget.setPalette(p)
        l = QGridLayout()
        l.addWidget(drawWidget)
        self.DrawArea.setLayout(l)
        self.drawer = drawWidget

        self.setupNodeLib()

    def initActions(self):
        self.exitAction = QAction('Quit', self)
        self.exitAction.setShortcut('Ctrl+Q')
        self.exitAction.setStatusTip('Exit application')
        self.exitAction.triggered.connect(self.close)

        self.runAction = QAction(QIcon(os.path.join(self.iconRoot, 'run.png')), 'Run', self)
        self.runAction.setShortcut('Ctrl+R')
        self.runAction.triggered.connect(self.runCode)
        self.runAction.setIconVisibleInMenu(True)
        self.addAction(self.runAction)
        
        self.loadAction = QAction(QIcon(os.path.join(self.iconRoot, 'load.png')), 'load', self)
        self.loadAction.setShortcut('Ctrl+O')
        self.loadAction.triggered.connect(self.loadGraph)
        self.loadAction.setIconVisibleInMenu(True)
        self.addAction(self.loadAction)
        
        self.saveAction = QAction(QIcon(os.path.join(self.iconRoot, 'save.png')), 'save', self)
        self.saveAction.setShortcut('Ctrl+S')
        self.saveAction.triggered.connect(self.saveGraph)
        self.saveAction.setIconVisibleInMenu(True)
        self.addAction(self.saveAction)

        self.connectAction = QAction(QIcon(os.path.join(self.iconRoot, 'save.png')), 'Connect', self)
        self.connectAction.setShortcut('Ctrl+Q')
        self.connectAction.triggered.connect(self.saveGraph)
        self.connectAction.setIconVisibleInMenu(True)
        self.addAction(self.connectAction)

    def initMenus(self):
        fileMenu = self.menuBar.addMenu('&File')
        fileMenu.addAction(self.exitAction)
        fileMenu.addAction(self.runAction)

        advancedMenu = self.menuBar.addMenu('&Advanced')
        advancedMenu.addAction(self.connectAction)
        
        self.mainToolBar.addAction(self.exitAction)
        self.mainToolBar.addAction(self.saveAction)
        self.mainToolBar.addAction(self.loadAction)
        self.mainToolBar.addSeparator()
        self.mainToolBar.addAction(self.runAction)

    def close(self):
        self.painter.graph.killRunner()
        qApp.quit()

    def runCode(self, *args):
        self.drawer.graph.execute()
        self.statusBar.showMessage('Code execution successful.', 2000)

    def loadGraph(self, *args):
        self.drawer.graph.load('')
        self.statusBar.showMessage('Graph loaded.', 2000)

    def saveGraph(self, *args):
        self.drawer.graph.save()
        self.statusBar.showMessage('Graph saved.', 2000)

    def resizeEvent(self, event):
        super(MainWindow, self).resizeEvent(event)
        self.drawer.repaint()
        self.drawer.update()

    def setupNodeLib(self):
        self.NodeListView.setup(self.FilterEdit, self.drawer.graph)


class DrawItem(object):
    def __init__(self, parent, data, painter):
        self.painter = painter
        self.state = False
        self.x = 0
        self.y = 0
        self.w = 0
        self.h = 0
        self.parent = parent
        self.data = data

    def update(self, x, y, w, h, transform):
        self.transform = transform
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        point = QPoint(x+12, y-16)*transform
        self._x = point.x()
        self._y = point.y()
        point = QPoint(x+w-24, y+h-60)*transform
        self._xx = point.x()
        self._yy = point.y()

    def draw(self, painter):
        pass

    def run(self):
        pass

    def setState(self, state):
        self.state = state

    def collide(self, pos):
        if self._x < pos.x() < self._xx and self._y < pos.y() < self._yy:
            return True


class Selector(DrawItem):

    def __init__(self, *args, **kwargs):
        super(Selector, self).__init__(*args, **kwargs)
        self.highlight = 0
        self.select = None
        self.items = self.data.info.select
        if self.data.info.default is not None:
            self.select = str(self.data.info.default)

    def update(self, x, y, w, h, transform):
        super(Selector, self).update(x, y, w, h, transform)
        if self.select is not None:
            self.items = self.data.info.select
            if self.data.info.default is not None:
                self.select = str(self.data.info.default)


    def watch(self, pos):
        scale = self.painter.scale
        for i in range(1, len(self.items)+1):
            if self._x < pos.x() < self._xx and self._y + 12*i*scale < pos.y() < self._yy + 12*i*scale:
                self.highlight = i
                return

    def watchDown(self, pos):
        self.select = str(self.items[self.highlight-1])
        self.parent.outputs[self.data.name].setDefault(self.select)
        # self.parent._Boolean.setDefault(self.select)

    def collide(self, pos):
        if self._x < pos.x() < self._xx+16 and self._y < pos.y() < self._yy:
            self.state = (self.state + 1) % 2
            self.painter.registerWatchingItem(self)
        else:
            if self.state:
                self.painter.removeWatchingItem(self)
            self.state = 0
        return super(Selector, self).collide(pos)

    def draw(self, painter):
        if not self.state:
            alignment = Qt.AlignRight
            text = self.data.name
            if self.select:
                text = str(self.select)
            pen = QPen(Qt.darkGray)
            painter.setPen(pen)
            painter.setBrush(QColor(40, 40, 40))
            xx, yy, ww, hh = self.x+(self.w)/2.-(self.w-25)/2., self.y-18, self.w-25, 12
            painter.drawRoundedRect(xx, yy, ww, hh, 2, 20)
            painter.setFont(QFont('Helvetica', 8))
            painter.setPen(pen)
            painter.drawText(xx-5, yy-3, ww-20, hh+5, alignment, text)
            pen.setColor(Qt.gray)
            # pen.setWidth(3)
            painter.setPen(pen)
            painter.setBrush(QBrush(Qt.gray))
            points = QPoint(xx+self.w-40, yy+2), QPoint(xx+10-40 + self.w, yy+2), QPoint(xx+5+self.w-40, yy+9)
            painter.drawPolygon(*points)
        else:
            alignment = Qt.AlignRight
            text = self.data.name
            pen = QPen(Qt.darkGray)
            painter.setPen(pen)
            painter.setBrush(QColor(40, 40, 40))
            xx, yy, ww, hh = self.x+(self.w)/2.-(self.w-25)/2., self.y-18 + 12, self.w-25, 12 * len(self.items)
            painter.drawRoundedRect(xx, yy, ww, hh, 2, 20)
            painter.setFont(QFont('Helvetica', 8))
            painter.setPen(pen)

            for i, item in enumerate(self.items):
                item = str(item)
                if i+1 == self.highlight:
                    pen.setColor(Qt.white)
                    painter.setPen(pen)
                else:
                    pen = QPen(Qt.darkGray)
                    painter.setPen(pen)
                painter.drawText(xx-5, yy-3+i*12, ww-20, hh+5, alignment, item)
            # painter.drawText(xx-5, yy-3+0, ww-20, hh+5, alignment, 'True')
            # painter.drawText(xx-5, yy-3+12, ww-20, hh+5, alignment, 'False')

            pen = QPen(Qt.darkGray)
            painter.setPen(pen)
            painter.setBrush(QColor(60, 60, 60))
            xx, yy, ww, hh = self.x+(self.w)/2.-(self.w-25)/2., self.y-18, self.w-25, 12
            painter.drawRoundedRect(xx, yy, ww, hh, 2, 20)
            painter.drawText(xx-5, yy-3, ww-20, hh+5, alignment, text)


class InputLabel(DrawItem):
    pass


class OutputLabel(DrawItem):
    pass


from floppy.nodeLib import ContextNodeFilter, ContextNodeList
class NodeDialog(QDockWidget):
    """
    Container Widget handling the set up of a ContextNodeFilter widget and a ContextNodeList when connections are
    dragged into open space.
    """
    def __init__(self, painter, event, pin, graph, parent=None):
        self.graph = graph
        self.painter = painter
        self.pin = pin
        super(NodeDialog, self).__init__(parent)
        self.setTitleBarWidget(QWidget(self))
        self.setStyleSheet("NodeDialog {background-color:rgb(45,45,45) ;border:1px solid rgb(0, 0, 0); "
                           "border-color:black}")
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint |Qt.X11BypassWindowManagerHint | Qt.FramelessWindowHint)
        self.setFeatures(QDockWidget.DockWidgetMovable)
        self.setFloating(True)
        pos = event.globalPos()
        self.setGeometry(pos.x(), pos.y(), 150, 250)
        dL = QVBoxLayout()
        cB = QCheckBox('Context sensitive')
        cB.setChecked(painter.contextSensitive)
        self.cB = cB

        nFilter = ContextNodeFilter()
        self.back = True if ':I' in pin else False
        nFilter.registerDialog(self, back=self.back)
        nFilter.setFocus()
        # nodeList = ContextNodeList(nFilter, painter, self)
        nodeList = ContextNodeList(self)
        nodeList.registerDialog(self)
        nodeList.registerGraph(graph)
        nodeList.registerPainter(painter)
        nodeList.setup(nFilter, graph)
        cB.stateChanged.connect(nFilter.check)
        nFilter.registerListView(nodeList)
        dL.addWidget(nFilter)
        dL.addWidget(cB)
        dL.addWidget(nodeList)
        # self.cl
        self.dialogWidget = QWidget()
        self.dialogWidget.setLayout(dL)
        self.setWidget(self.dialogWidget)

    def close(self, spawned=False):
        """
        Close the dialog and connect a newly connected node if necessary.
        :param spawned: Boolean defining whether a node was spawned and needs connecting.
        :return: None
        """
        if spawned:
            self.painter.contextSensitive = self.cB.checkState()
            newNode = self.graph.getNewestNode()
            pin = self.graph.getPinWithID(self.pin)
            if not self.back:
                endPin = newNode.getInputofType(pin.info.varType)
                if endPin:
                    self.graph.connect(self.graph.getNodeFromPinID(self.pin), self.pin.split(':')[1][1:], newNode, endPin.name)
            else:
                endPin = newNode.getOutputofType(pin.info.varType)
                if endPin:
                    # self.graph.connect(self.graph.getNodeFromPinID(self.pin), self.pin.split(':')[1][1:], newNode, endPin.name)
                    self.graph.connect(newNode, endPin.name, self.graph.getNodeFromPinID(self.pin), self.pin.split(':')[1][1:])

                # self.painter.app.connectionManager.registerStart(pin, pin.node)
                # self.painter.app.connectionManager.registerEnd(endPin, newNode)

        # painter.contextSensitive = self.cB.checkState()
        self.painter.update()
        super(NodeDialog, self).close()

    def getTypeHint(self):
        """
        Returns the name of the type of the pin the new node will be connected to.
        This is used to filter the node list for appropriate nodes.
        :return: String representing a Hint. In this case a type Hint.
        """
        pin = self.graph.getPinWithID(self.pin)
        return pin.info.varType.__name__
