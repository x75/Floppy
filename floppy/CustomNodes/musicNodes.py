from floppy.node import Node, Input, Output, Tag, abstractNode
from floppy.FloppyTypes import Type, StructureInfo, Atom
from floppy.CustomNodes.infoNodes import PlotNode

import time
import random
import subprocess

import numpy as np
import matplotlib.pyplot as plt

import librosa

plt.ion()

# custom types
class Ndarray(Type):
    color = (102, 102, 0)

    @staticmethod
    def checkType(instance):
        return instance

    @staticmethod
    def debugInfoGetter(obj):
        return obj.get_name
    
# custom nodes
class MLibrosaDataLoadNode(Node):
    Input('filename', str)
    Input('duration', float)
    Output('y', Ndarray, list=True)
    Output('sr', int)
    Output('filename', str)

    def run(self):
        # self.duration = 75
        # self.filename_ = self._file
        print('Loading audio file %s' % (self._filename))
        y, sr = librosa.load(self._filename, offset=0, duration=self._duration)
        print('Loaded audio file with %s samples at rate %d' % (y.shape, sr))

        self._y(y)
        self._sr(sr)
        # self._filename(self.filename_)

class MPLPlot(PlotNode):
    Input('y', Ndarray, list=True)

    def __init__(self, *args, **kwargs):
        PlotNode.__init__(self, *args, **kwargs)
        # super(MPLPlot, self).__init__(*args, **kwargs)
        self.fig = plt.figure()
        self.ax = self.fig.add_subplot(1,1,1)
        plt.show()

    def run(self):
        super(MPLPlot, self).run()
        self.ax.plot(self._Y)
        plt.draw()
    
# class AMyNode(Node):
#     Input('Inta', int)
#     Input('Intb', int)
#     Input('Int1', int, select=[1,2,3,4])
#     Input('Int3', int, select=[1,2,3,4])
#     Output('Int2', int)

#     def run(self):
#         self._Int1
#         self._Int2(self._Int1 + 1)




# class FakeWorkNode(Node):
#     Input('inp', object)
#     Output('out', object)

#     def run(self):
#         print('Working @ {}'.format(str(self._inp)))
#         time.sleep(random.randrange(1,5))
#         print('Done')
#         # self._return('Test Return Value')


# class IncrementNode(Node):
#     Output('Integer', int)

#     def setup(self):
#         self.i = 0

#     def run(self):
#         self._Integer(self.i)
#         self.i += 1


# class RandomFloat(Node):
#     Output('Float', float)

#     def run(self):
#         self._Float(random.random())


# class RunProgram(Node):
#     """
#     Node for calling an external program of given name and given command line arguments.
#     Returns the program's return value and its stdout output.
#     """
#     Input('ProgramName', str)
#     Input('Arguments', str)
#     Output('ReturnValue', int)
#     Output('StdOut', str)

#     def run(self):
#         programName = self._ProgramName
#         args = [programName] + self._Arguments.split()
#         r = 0
#         try:
#             out = subprocess.check_output(args, shell=True)
#         except subprocess.CalledProcessError as e:
#             out = ''
#             r = e[-1]
#         self._ReturnValue(r)
#         self._StdOut(out)




# class Range(Node):
#     Input('EndValue', int)
#     Output('ValueList', int, list=True)
#     def run(self):
#         self._ValueList(list(range(self._EndValue)))


# class Int2Str(Node):
#     Input('Int', int)
#     Output('Str', str)
#     def run(self):
#         self._Str(str(self._Int))












# class PlotNode2(Node):
#     Input('XX', str)
#     Output('YY', str)

#     def __init__(self, *args, **kwargs):
#         super(PlotNode2, self).__init__(*args, **kwargs)
#         self.time = time.time()
#         self.points = []
#         self.counts = 0

#     def check(self):
#         t = time.time()
#         if t - self.time > 3:
#             self.time = t
#             return True

#     def run(self):
#         super(PlotNode2, self).run()
#         self.counts += 1
#         self.points.append(
#             (self.counts, (random.randint(5, 20), random.randint(5, 20), random.randint(5, 20), random.randint(5, 20))))

#     def report(self):
#         r = super(PlotNode2, self).report()
#         r['template'] = 'PlotTemplate'
#         r['points'] = self.points[:]
#         r['keep'] = 'points'
#         self.points = []
#         return r

