from floppy.node import Node, Input, Output, Tag, abstractNode


class PlotNode(Node):
    Tag('plot')


class PlotA_vs_B(PlotNode):
    pass


class PlotA_and_B(PlotNode):
    Input('A', float)
    Input('B', float)
    Output('Trigger', object)

    def __init__(self,*args, **kwargs):
        super(PlotA_and_B, self).__init__(*args, **kwargs)
        self.data = []

    def run(self):
        super(PlotA_and_B, self).run()
        self.data.append((self._A, self._B))

    def report(self):
        r = super(PlotA_and_B, self).report()
        r['template'] = 'plotTemplate'
        r['points'] = self.data[:]
        r['keep'] = 'points'
        self.data = []
        return r


class PlotBarsGrouped(PlotNode):
    Input('A', float)
    Input('B', float)
    Output('Trigger', object)

    def __init__(self,*args, **kwargs):
        super(PlotBarsGrouped, self).__init__(*args, **kwargs)
        self.data = []

    def run(self):
        super(PlotBarsGrouped, self).run()
        self.data.append((self._A, self._B))

    def report(self):
        r = super(PlotBarsGrouped, self).report()
        r['template'] = 'plotBarsGroupedTemplate'
        r['points'] = self.data[:]
        # r['keep'] = 'points'
        # self.data = []
        return r
