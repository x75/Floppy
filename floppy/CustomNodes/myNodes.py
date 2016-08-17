from floppy.node import Node, Input, Output, Tag
import time
import random


class MyNode(Node):
    Input('AAA', int)
    Output('BBB', int)


class PlotNode2(Node):
    Input('XX', str)
    Output('YY', str)
    def __init__(self, *args, **kwargs):
        super(PlotNode2, self).__init__(*args, **kwargs)
        self.time = time.time()
        self.points = []
        self.counts = 0

    def check(self):
        t = time.time()
        if t - self.time > 3:
            self.time = t
            return True

    def run(self):
        super(PlotNode2, self).run()
        self.counts += 1
        self.points.append((self.counts, random.randint(5,20)))

    def report(self):
        r = super(PlotNode2, self).report()
        r['template'] = 'plotTemplate'
        r['points'] = self.points[:]
        r['keep'] = 'points'
        self.points = []
        return r
        