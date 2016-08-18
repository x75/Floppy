from matplotlib.pyplot import plot, savefig
import matplotlib.pyplot as plt
from floppy.reportWidget import template
from numpy import array, arange

_pointCache = None

@template
def plotTemplate(data, cache, fileBase):
    points = data['points']
    fileName = fileBase+'/_ppy_{}.svg'.format(data['ID'])
    # print(cache)

    if not cache == globals()['_pointCache'] and cache:
        x, y = zip(*cache)
        plot(x, array(y), color='blue')
        # fig = plt.figure()
        savefig(__file__[:-12]+"/x.svg")
        globals()['_pointCache'] = cache[:]
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
        img  {{
            float: right;
        }}
        </style>

        <div id="wrap">
            <div id="left_col">
                {inputs}
            </div>
            <div id="right_col">
                {outputs}
            </div>
            <br>
            <br>
                  <img id="plot" src="{fileName}" alt="Plotting did not work." width=400>
        </div>

        """.format(nodeName=data['class'], nodeID=data['ID'],
                   inputs='<br>'.join(['{}[{}]:  {}'.format(name, varType, value) for
                                       name, varType, value in data['inputs']]),
                   outputs='<br>'.join(['{}[{}]:  {}'.format(name, varType, value) for
                                       name, varType, value in data['outputs']]),
                   fileName=fileName)

@template
def programTemplate(data, cache, fileBase):
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
        #stdout {{
           color: white;
           font-size: 75%
        }}
        </style>

        <div id="wrap">
            <div id="left_col">
                {inputs}
            </div>
            <div id="right_col">
                {outputs}
            </div>
            <br>
            <br>
            <div id="stdout">
                  {stdout}
            </div>
        </div>

        """.format(nodeName=data['class'], nodeID=data['ID'],
                   inputs='<br>'.join(['{}[{}]:  {}'.format(name, varType, value) for
                                       name, varType, value in data['inputs']]),
                   outputs='<br>'.join(['{}[{}]:  {}'.format(name, varType, value) for
                                       name, varType, value in data['outputs']]),
                   stdout=data['stdout'].replace('\\n', '<br>'))

@template
def plotBarsGroupedTemplate(data, cache, fileBase):
    points = data['points']
    fileName = fileBase+'/_ppy_{}.svg'.format(data['ID'])

    if not points == globals()['_pointCache'] and points:
        x, y = zip(*points)
        n_groups = len(x)
        fig, ax = plt.subplots()
        index = arange(n_groups)
        bar_width = 0.35
        opacity = .4
        rects1 = plt.bar(index, x, bar_width,
                         alpha=opacity,
                         color='b',
                         label='A')
        rects2 = plt.bar(index + bar_width, y, bar_width,
                         alpha=opacity,
                         color='r',
                         label='B')
        plt.xticks(index+bar_width)
        plt.legend()
        plt.tight_layout()
        savefig(fileName)
        globals()['_pointCache'] = cache[:]
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
        img  {{
            float: right;
        }}
        </style>

        <div id="wrap">
            <div id="left_col">
                {inputs}
            </div>
            <div id="right_col">
                {outputs}
            </div>
            <br>
            <br>
                  <img id="plot" src="{fileName}" alt="Plotting did not work." width=400>
        </div>

        """.format(nodeName=data['class'], nodeID=data['ID'],
                   inputs='<br>'.join(['{}[{}]:  {}'.format(name, varType, value) for
                                       name, varType, value in data['inputs']]),
                   outputs='<br>'.join(['{}[{}]:  {}'.format(name, varType, value) for
                                       name, varType, value in data['outputs']]),
                   fileName=fileName)