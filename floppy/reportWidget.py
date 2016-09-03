from PyQt5 import QtCore, QtGui, QtWidgets#, QtWebKitWidgets, QtWebKit
from PyQt5 import QtWebEngineWidgets, QtWebEngineCore
from PyQt5.QtCore import Qt, QPoint, QSettings
from floppy.templates import TEMPLATES
'''
TEMPLATES = {}



def template(func):
    TEMPLATES[func.__name__] = func
    return func



@template
def defaultTemplate(data, cache):
        return """<h1 id="head">{nodeName} -- {nodeID}</h1>
        <style>
          h1 {{ text-align:center; color: white}};
        </style>

        <style type="text/css">
        #wrap {{
           width:400;
           margin:0 auto;
        }}
        #left_col {{
           float:left;
           width:200;
           text-align:left;
           color: white
        }}
        #right_col {{
           float:right;
           width:200;
           text-align:right;
           color: white
        }}
        </style>
        <div id="wrap">
            <div id="left_col">
                {inputs}
            </div>
            <div id="right_col">
                {outputs}
            </div>
        </div>""".format(nodeName=data['class'], nodeID=data['ID'],
                         inputs='<br>'.join(['{}[{}]:  {}'.format(name, varType, value) for name, varType, value in data['inputs']]),
                         outputs='<br>'.join(['{}[{}]:  {}'.format(name, varType, value) for name, varType, value in data['outputs']]))

'''
#class ReportWidget(QtWebKitWidgets.QWebView):
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
        self.setHtml(tmplt(data, self.cache[:], self.fileBase, self.width()), url)

'''
@template
def defaultTemplate(data, cache, fileBase):
        return """
        <style>
          h1 {{ text-align:center; color: white}}
        </style>

        <style type="text/css">
        #wrap {{
           width:400;
           margin:0 auto;
        }}
        #left_col {{
           float:left;
           width:200;
           text-align:left;
           color: white
        }}
        #right_col {{
           float:right;
           width:200;
           text-align:right;
           color: white
        }}
        </style>
        <HTML>
        <h1 id="head">{nodeName} -- {nodeID}</h1>
        <div id="wrap">
            <div id="left_col">
                {inputs}
            </div>
            <div id="right_col">
                {outputs}
            </div>
        </div></HTML>
        """.format(nodeName=data['class'], nodeID=data['ID'],
                         inputs='<br>'.join(['{}[{}]:  {}'.format(name, varType, value) for name, varType, value in data['inputs']]),
                         outputs='<br>'.join(['{}[{}]:  {}'.format(name, varType, value) for name, varType, value in data['outputs']]))
'''
from floppy.quickPlot import test
def defaultTemplate(data, cache, fileBase, width):
    print(width)

    return '''
<HTML>

    <BODY bgcolor="#606060">
        <H1>{nodeName}</H1>
        <div id=nodeID>ID: {ID} </div>
        <P>This is very minimal "hello world" HTML document.</P>
{plot}
    </BODY>
</HTML>
    '''.format(nodeName=data['class'],
               ID=data['ID'],
               plot=test(width-30))


