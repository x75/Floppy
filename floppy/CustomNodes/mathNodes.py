from floppy.node import Node


class CrossProduct(Node):
    Input('Vector1', float, list=True)
    Input('Vector2', float, list=True)
    Output('XProduct', float, list=True)

    def run(self):
        super(CrossProduct, self).run()
        v1 = self._Vector1
        v2 = self._Vector2
        self._XProduct(v1[1]*v2[2]-v1[2]*v2[1], v1[2]*v2[0]-v1[0]*v2[2], v1[0]*v2[1]-v1[1]*v2[0])


class DotProduct(Node):
    Input('Vector1', float, list=True)
    Input('Vector2', float, list=True)
    Output('DotProduct', float, list=True)

    def run(self):
        super(DotProduct, self).run()
        v1 = self._Vector1
        v2 = self._Vector2
        self._DotProduct(v1[0]*v2[0] + v1[1]*v2[1] + v1[2]*v2[2])


class Distance(Node):
    Input('Position1', float, list=True)
    Input('Position2', float, list=True)
    Output('Distance', float, list=True)

    def run(self):
        super(Distance, self).run()
        v1 = self._Position1
        v2 = self._Position2
        d = (v1[0]-v2[0])**2 + (v1[1]-v2[1])**2 + (v1[2]-v2[2])**2
        self._Distance(d**.5)


class Difference(Node):
    Input('Vector1', float, list=True)
    Input('Vector2', float, list=True)
    Output('Difference', float, list=True)

    def run(self):
        super(Difference, self).run()
        v1 = self._Position1
        v2 = self._Position2
        self._Difference((v1[0]-v2[0])**2, (v1[1]-v2[1])**2, (v1[2]-v2[2]))


class Normalize(Node):
    Input('Vector', float, list=True)
    Input('NVector', float, list=True)
    Tag('Vector', 'Math')

    def run(self):
        super(Normalize, self).run()
        v = self._Vector
        d = (v[0]**2 + v[1]**2 + v[2]**2)**.5
        self._NVector((v[0]/d, v[1]/d, v[2]/d))
