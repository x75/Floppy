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