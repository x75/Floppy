import lauescript
from lauescript.laueio import loader
from floppy.node import Node

class ReadAtoms(Node):
    Input('FileName', str)
    Output('Atoms', object)

    def run(self):
        super(ReadAtoms, self).run()
        from lauescript.laueio.loader import Loader
        loader = Loader()
        loader.create(self._FileName)
        mol = loader.load('quickloadedMolecule')
        return mol