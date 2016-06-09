# import lauescript
# from lauescript.laueio import loader
from lauescript.cryst.transformations import frac2cart
from lauescript.types.adp import ADPDataError
from floppy.node import Node
from floppy.types import Atom


class ReadAtoms(Node):
    Input('FileName', str)
    Output('Atoms', Atom, list=True)

    def run(self):
        super(ReadAtoms, self).run()
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
    Output('ADP_Flag', str)
    Output('Cell',float, list=True)

    def run(self):
        super(BreakAtom, self).run()
        atom = self._Atom
        # print(atom, atom.molecule.get_cell(degree=True))
        self._Name(atom.get_name())
        self._Element(atom.get_element())
        self._frac(atom.get_frac())
        self._cart(atom.get_cart())
        try:
            adp = atom.adp['cart_meas']
        except ADPDataError:
            adp = [0, 0, 0, 0, 0, 0]
        self._ADP(adp)
        self._ADP_Flag(atom.adp['flag'])
        self._Cell(atom.molecule.get_cell(degree=True))


class Frac2Cart(Node):
    Input('Position', float, list=True)
    Input('Cell', float, list=True)
    Output('Cart', float, list=True)

    def run(self):
        super(Frac2Cart, self).run()
        self._Cart(frac2cart(self._Position, self._Cell))

