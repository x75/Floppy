# import lauescript
# from lauescript.laueio import loader
from floppy.node import Node
from floppy.types import Atom

class ReadAtoms(Node):
    Input('FileName', str)
    Output('Atoms', Atom, list=True)

    def run(self):
        super(ReadAtoms, self).run()
        print(self._FileName)
        from lauescript.laueio.loader import Loader
        loader = Loader()
        loader.create(self._FileName)
        mol = loader.load('quickloadedMolecule')
        self._Atoms(mol.atoms)


class BreakAtom(Node):
    Input('Atom', Atom)
    Output('Name', str)
    Output('Element', str)
    Output('frac', float, list=True)
    Output('cart', float, list=True)
    Output('ADP',float, list=True)

    def run(self):
        super(BreakAtom, self).run()
        self._ADP((1,2,3))
        self._Name('test')