import matplotlib.pyplot as plt, mpld3
from floppy.reportWidget import template
plt.plot([3,1,4,1,5], 'ks-', mec='w', mew=5, ms=20)
# fig = plt.figure()
plt.savefig("x.svg")


@template
def plotTemplate(data, cache):
    plt.plot([3,1,4,1,5], 'ks-', mec='w', mew=5, ms=20)
    # fig = plt.figure()
    plt.savefig("x.svg")
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
        <figure>
          <img src="x.svg" alt="The Pulpit Rock" width="304" height="228">
        </figure>
        """.format(nodeName=data['class'], nodeID=data['ID'],
                         inputs='<br>'.join(['{}[{}]:  {}'.format(name, varType, value) for name, varType, value in data['inputs']]),
                         outputs='<br>'.join(['{}[{}]:  {}'.format(name, varType, value) for name, varType, value in data['outputs']]))