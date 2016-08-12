from floppy.node import Node, Input, Output, Tag, abstractNode
from floppy.CustomNodes.crystNodes import CrystNode
import subprocess
import os

@abstractNode
class ShelxNode(CrystNode):
    Tag('Shelx')


class RunShelxl(ShelxNode):
    Input('INS', str)
    Input('HKL', str)
    Input('List', int)
    Input('Cycles', int)
    Input('DAMP', int)
    Input('Type', str, select=('CGLS', 'L.S.'))
    Output('RES', str)
    Output('LST', str)
    Output('FCF', str)
    Output('R1', float)

    def __init__(self, *args, **kwargs):
        super(RunShelxl, self).__init__(*args, **kwargs)
        self.p = None

    def run(self):
        super(RunShelxl, self).run()
        with open('__tmp__.ins', 'w') as fp:
            fp.write(self._INS)
        with open('__tmp__.hkl', 'w') as fp:
            fp.write(self._HKL)

        self.p = subprocess.Popen('shelxl {}'.format('__tmp__'), shell=True)
        os.waitpid(self.p.pid, 0)
        output = ''
        with open('__tmp__.res', 'r') as fp:
            output = fp.read()
        self._RES(output)
        with open('__tmp__.lst', 'r') as fp:
            output = fp.read()
        self._LST(output)
        with open('__tmp__.fcf', 'r') as fp:
            output = fp.read()
        self._FCF(output)
        for file in os.listdir():
            if file.startswith('__tmp__'):
                os.remove(file)
