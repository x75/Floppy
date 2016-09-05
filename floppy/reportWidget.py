from PyQt5 import QtCore, QtGui, QtWidgets#, QtWebKitWidgets, QtWebKit
from PyQt5 import QtWebEngineWidgets, QtWebEngineCore
from PyQt5.QtCore import Qt, QPoint, QSettings
from floppy.templates import TEMPLATES

class ReportWidget(QtWebEngineWidgets.QWebEngineView):

    def __init__(self, *args, **kwargs):
        super(ReportWidget, self).__init__(*args, **kwargs)
        self.setStyleSheet('''ReportWidget{background: rgb(55,55,55)}
        ''')
        self.data = None
        self.cache = []
        self.templateCache = {}
        self.setHtml('')
        #import floppy.templates

    def updateReport(self, data):
        if data == self.data:
            return
        settings = QSettings('Floppy', 'Floppy')
        self.fileBase = settings.value('WorkDir', type=str)
        self.data = data
        self._update()

    def _update(self):
        data = self.data
        if not data:
            return
        try:
            keep = data['keep']
        except KeyError:
            pass
        else:
            if keep:
                if keep == 'CLEAR':
                    self.cache = []
                elif data[keep]:
                    self.cache += data[keep]
                    # print('xxxxx', self.cache)

        try:
            tmplt = self.templateCache[data['ID']]
        except KeyError:
            try:
                tmplt = TEMPLATES[data['template']]()
            except KeyError:
                print('Error: {} template missing'.format(data['template']))
                return
            else:
                self.templateCache[data['ID']] = tmplt

        #tmplt = defaultTemplate
        # url = QtCore.QUrl.fromLocalFile(self.fileBase)
        url = QtCore.QUrl.fromLocalFile(QtCore.QDir(self.fileBase).absoluteFilePath('dummy.html'))
        # QtWebKit.QWebSettings.clearMemoryCaches()
        #QtWebEngineCore.QWebSettings.clearMemoryCaches()
        #scrollValue = self.page().scrollPosition()
        self.setHtml(tmplt(data, self.cache[:], self.fileBase, self.width()), url)




