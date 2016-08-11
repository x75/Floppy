from PyQt5 import QtCore, QtGui, QtWidgets, QtWebKitWidgets

TEMPLATES = {}



def template(func):
    TEMPLATES[func.__name__] = func
    return func



@template
def defaultTemplate(data, cache):
        return """<h1 id="head">{nodeName} -- {nodeID}</h1>
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


class ReportWidget(QtWebKitWidgets.QWebView):

    def __init__(self, *args, **kwargs):
        super(ReportWidget, self).__init__(*args, **kwargs)
        self.setStyleSheet('''ReportWidget{background: rgb(55,55,55)}
        ''')
        self.data = None
        self.cache = []
        self.setHtml('')
        import floppy.templates

    def updateReport(self, data):
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
                else:
                    self.cache.append(data[keep])
        try:
            tmplt = TEMPLATES[data['template']]
        except KeyError:
            print('Error: {} template missing'.format(data['template']))
            print(TEMPLATES.keys())
            return
        url = QtCore.QUrl.fromLocalFile(__file__)
        self.setHtml(tmplt(data, self.cache), url)


@template
def defaultTemplate(data, cache):
        return """<h1 id="head">{nodeName} -- {nodeID}</h1>
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

        <div id="wrap">
            <div id="left_col">
                {inputs}
            </div>
            <div id="right_col">
                {outputs}
            </div>
        </div>
        """.format(nodeName=data['class'], nodeID=data['ID'],
                         inputs='<br>'.join(['{}[{}]:  {}'.format(name, varType, value) for name, varType, value in data['inputs']]),
                         outputs='<br>'.join(['{}[{}]:  {}'.format(name, varType, value) for name, varType, value in data['outputs']]))


