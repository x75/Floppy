from collections import OrderedDict
from copy import copy

NODECLASSES = {}


class InputNotAvailable(Exception):
    pass


class Info(object):
    def __init__(self, name, varType, hints=None, default=''):
        self.name = name
        self.varType = varType
        self.hints = hints
        self.default = default
        self.valueSet = False
        self.value = None


class InputInfo(Info):
    def __call__(self):
        if self.valueSet:
            return self.value
        elif self.default:
            return self.default
        else:
            raise InputNotAvailable('Input not set for node.')

    def set(self, value):
        self. value = value
        self.valueSet = True


class OutputInfo(Info):
    def __call__(self, value):
        self.value = value
        self.valueSet = True


class MetaNode(type):
    inputs = []
    outputs = []

    @classmethod
    def __prepare__(metacls, name, bases):
        MetaNode.inputs = []
        MetaNode.outputs = []
        return {'Input': MetaNode.addInput,
                'Output': MetaNode.addOutput}

    def addInput(name: str,
                 varType: object,
                 hints=None,
                 default=''):
        MetaNode.inputs.append({'name': name,
                                'varType': varType,
                                'hints': hints,
                                'default': default})

    def addOutput(name: str,
                  varType: object,
                  hints=None,
                  default=''):
        MetaNode.outputs.append({'name': name,
                                 'varType': varType,
                                 'hints': hints,
                                 'default': default})

    def __new__(cls, name, bases, classdict):
        result = type.__new__(cls, name, bases, classdict)
        # result.__dict__['Input'] = result._addInput
        NODECLASSES[name] = result
        result._inputs = OrderedDict()
        result._outputs = OrderedDict()
        for inp in MetaNode.inputs:
            result._addInput(data=inp, cls=result)

        for out in MetaNode.outputs:
            result._addOutput(data=out, cls=result)
        return result


class Node(object, metaclass=MetaNode):
    """
    Base class for Nodes.

    To add Inputs to a custom Node class call 'Input(name, varType, hints, default)' in the class's
    body e.g.:

        class MyNode(Node):
            Input('myStringInput', str, default='Hello World')

    To access the value of an input during the Node's 'run' method or 'check' method use
    'myNodeInstance._myStringInput'. An 'InputNotAvailable' Exception is raised is the input is not set yet.
    """
    _inputs = OrderedDict()

    def __init__(self, nodeID):
        # self._inputs = OrderedDict()
        self.ID = nodeID
        self.inputs = {}
        self.outputs = {}
        self.inputPins = {}
        self.outputPins = {}
        self.inProgress = 1
        for i, inp in enumerate(self._inputs.values()):
            inp = copy(inp)
            inpID = '{}:I{}'.format(self.ID, i)
            newPin = Pin(inpID, inp, self)
            self.inputPins[inp.name] = newPin
            self.inputs[inp.name] = inp

        for i, out in enumerate(self._outputs.values()):
            out = copy(out)
            outID = '{}:O{}'.format(self.ID, i)
            newPin = Pin(outID, out, self)
            self.outputPins[out.name] = newPin
            self.outputs[out.name] = out

    def __str__(self):
        return '{}-{}'.format(self.__class__.__name__, self.ID)

    def next(self):
        """

        :rtype: Node
        """
        pass

    def previous(self):
        """

        :rtype: Node
        """
        pass

    def run(self) -> None:
        """

        :rtype: None
        """
        print('Executing node {}'.format(self))

    def notify(self):
        self.inProgress -= 1
        pass

    def check(self) -> bool:
        if self.inProgress:
            for inp in self.inputs.values():
                if not inp.valueSet:
                    print('{}: Prerequisites not met.'.format(str(self)))
                    return False
            return True

    def _addInput(*args, data='', cls=None):
        inputInfo = InputInfo(**data)
        cls._inputs[data['name']] = inputInfo

    def _addOutput(*args, data='', cls=None):
        outputInfo = OutputInfo(**data)
        cls._outputs[data['name']] = outputInfo
        
    def __getattr__(self, item):
        if item.startswith('_') and not item.startswith('__'):
            try:
                return self.inputs[item.lstrip('_')]()
            except KeyError:
                raise AttributeError('No Input with name {} defined.'.format(item.lstrip('_')))
        else:
            return super(Node, self).__getattr__(item)

    def getInputPin(self, inputName):
        return self.inputPins[inputName]

    def getInputInfo(self, inputName):
        return self.inputs[inputName]

    def getOutputInfo(self, outputName):
        return self.outputs[outputName]



class Pin(object):
    def __init__(self, pinID, info, node):
        self.ID = pinID
        self.info = info
        self.node = node


class TestNode(Node):
    Input('strInput', str)
    Output('strOutput', str)

