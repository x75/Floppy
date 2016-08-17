from matplotlib.pyplot import plot, savefig
from floppy.reportWidget import template
from numpy import array
# plt.plot([3,1,4,1,5], 'ks-', mec='w', mew=5, ms=20)
# # fig = plt.figure()
# plt.savefig("x.svg")

_pointCache = None

@template
def plotTemplate(data, cache):
    points = data['points']
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
                  <img id="plot" src="x.svg" alt="Plotting did not work." width=400>
        </div>

        """.format(nodeName=data['class'], nodeID=data['ID'],
                   inputs='<br>'.join(['{}[{}]:  {}'.format(name, varType, value) for
                                       name, varType, value in data['inputs']]),
                   outputs='<br>'.join(['{}[{}]:  {}'.format(name, varType, value) for
                                       name, varType, value in data['outputs']]))

@template
def programTemplate(data, cache):
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
           font-size: 50%
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