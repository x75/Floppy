from collections import OrderedDict
from copy import copy

NODECLASSES = {}


class InputNotAvailable(Exception):
    pass


class InputAlreadySet(Exception):
    pass


class Info(object):
    def __init__(self, name, varType, hints=None, default='', select=None, owner = False):
        self.name = name
        self.connected = False
        self.varType = varType
        if not hints:
            self.hints = [varType.__name__]
        else:
            self.hints = [varType.__name__] + hints
        self.default = default
        self.valueSet = False
        self.value = None
        self.select = select
        self.owner = owner

    def setOwner(self, owner):
        self.owner = owner

    def setDefault(self, value):
        if not self.varType == object:
            try:
                self.default = self.varType(value)
            except ValueError:
                self.default = ''
        else:
            self.default = value

    def __str__(self):
        return 'INFO'

    def reset(self):
        self.default = None
        self.valueSet = False
        self.value = None


class InputInfo(Info):
    def __call__(self, noException=False):
        if self.valueSet:
            if not self.varType == object:
                return self.varType(self.value)
            else:
                return self.value
        elif self.default and not self.connected:
            if not self.varType == object:
                return self.varType(self.default)
            else:
                return self.default
        else:
            if noException:
                return None
            else:
                raise InputNotAvailable('Input not set for node.')

    def set(self, value, override=False):
        if self.valueSet and not override:
            raise InputAlreadySet('Input \'{}\' of node \'{}\' is already set.'.format(self.name, str(self.owner)))
        self.value = value
        self.valueSet = True

    def setConnected(self, value: bool):
        self.connected = value

    def isAvailable(self):
        if self.valueSet:
            return True
        elif self.default and not self.connected:
            return True
        return False


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
                 default='',
                 select=None):
        MetaNode.inputs.append({'name': name,
                                'varType': varType,
                                'hints': hints,
                                'default': default,
                                'select': select})

    def addOutput(name: str,
                  varType: object,
                  hints=None,
                  default='',
                  select=None):
        MetaNode.outputs.append({'name': name,
                                 'varType': varType,
                                 'hints': hints,
                                 'default': default,
                                 'select': select})

    def __new__(cls, name, bases, classdict):
        result = type.__new__(cls, name, bases, classdict)
        # result.__dict__['Input'] = result._addInput
        NODECLASSES[name] = result
        try:
            result.__inputs__ = result.__bases__[0].__inputs__.copy()
        except AttributeError:
            result.__inputs__ = OrderedDict()
        try:
            result.__outputs__ = result.__bases__[0].__outputs__.copy()
        except AttributeError:
            result.__outputs__ = OrderedDict()
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

    def __init__(self, nodeID, graph):
        self.__pos__ = (0, 0)
        self.graph = graph
        self.ID = nodeID
        self.inputs = OrderedDict()
        self.outputs = OrderedDict()
        self.inputPins = OrderedDict()
        self.outputPins = OrderedDict()
        for i, inp in enumerate(self.__inputs__.values()):
            inp = copy(inp)
            inp.setOwner(self)
            inpID = '{}:I{}'.format(self.ID, inp.name)
            newPin = Pin(inpID, inp, self)
            self.inputPins[inp.name] = newPin
            self.inputs[inp.name] = inp

        for i, out in enumerate(self.__outputs__.values()):
            out = copy(out)
            out.setOwner(self)
            outID = '{}:O{}'.format(self.ID, out.name)
            newPin = Pin(outID, out, self)
            self.outputPins[out.name] = newPin
            self.outputs[out.name] = out
        if not self.inputs.keys():
            raise AttributeError('Nodes without any input are not valid.')

    def __str__(self):
        return '{}-{}'.format(self.__class__.__name__, self.ID)

    def __hash__(self):
        return hash(str(self))

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
        """
        Manage the node's state after execution and set input values of subsequent nodes.
        :return: None
        :rtype: None
        """
        for con in self.graph.getConnectionsFrom(self):
            outputName = con['outputName']
            nextNode = con['inputNode']
            nextInput = con['inputName']
            nextNode.prepare()
            if self.outputs[outputName].valueSet:
                nextNode.setInput(nextInput, self.outputs[outputName].value, override=True)
            else:
                nextNode.setInput(nextInput, self.outputs[outputName].default, override=True)

        [Info.reset(inp) for inp in self.inputs.values()]

    def setInput(self, inputName, value, override=False):
        self.inputs[inputName].set(value, override=override)

    def check(self) -> bool:
        for inp in self.inputs.values():
            if not inp.isAvailable():
                print('        {}: Prerequisites not met.'.format(str(self)))
                return False
        return True

    def prepare(self):
        """
        Method for preparing a node for execution.
        This method is called on each node before the main execution loop of the owning graph instance is started.
        The methods makes sure that artifacts from previous execution are reset to their original states and default
        values of inputs that are connected to other nodes' outputs are removed.
        TODO: Implement this.
        :return:
        """
        return
        [InputInfo.reset(inp) for inp in self.inputs.values()]

    def _addInput(*args, data='', cls=None):
        inputInfo = InputInfo(**data)
        cls.__inputs__[data['name']] = inputInfo

    def _addOutput(*args, data='', cls=None):
        outputInfo = OutputInfo(**data)
        cls.__outputs__[data['name']] = outputInfo
        
    def __getattr__(self, item):
        if item.startswith('_') and not item.startswith('__'):
            try:
                return self.inputs[item.lstrip('_')]()
            except KeyError:
                try:
                    return self.outputs[item.lstrip('_')]
                except KeyError:
                    raise AttributeError('No I/O with name {} defined.'.format(item.lstrip('_')))
                # raise AttributeError('No Input with name {} defined.'.format(item.lstrip('_')))
        else:
            return super(Node, self).__getattr__(item)

    def getInputPin(self, inputName):
        return self.inputPins[inputName]

    def getOutputPin(self, outputName):
        return self.outputPins[outputName]

    def getInputInfo(self, inputName):
        return self.inputs[inputName]

    def getOutputInfo(self, outputName):
        return self.outputs[outputName]

    def getInputID(self, inputName):
        return '{}:I{}'.format(self.ID, inputName)

    def getOutputID(self, outputName):
        return '{}:O{}'.format(self.ID, outputName)

    def getInputofType(self, varType):
        for inp in self.inputs.values():
            if issubclass(varType, inp.varType) or issubclass(inp.varType, varType):
                return inp

    def getOutputofType(self, varType):
        for out in self.outputs.values():
            if issubclass(varType, out.varType) or issubclass(out.varType, varType):
                return out

    def save(self):
        inputConns = [self.graph.getConnectionOfInput(inp) for inp in self.inputs.values()]
        # print(inputConns)
        inputConns = {inputConn['inputName']: inputConn['outputNode'].getOutputID(inputConn['outputName']) for inputConn in inputConns if inputConn}
        outputConns = {out.name: self.graph.getConnectionsOfOutput(out) for out in self.outputs.values()}
        for key, conns in outputConns.items():
            conns = [outputConn['inputNode'].getInputID(outputConn['inputName']) for outputConn in conns]
            outputConns[key] = conns
        return {'class': self.__class__.__name__,
                     'position': self.__pos__,
                     'inputs': [(inputName, inp.varType.__name__, inp(True), inp.default)
                                for inputName, inp in self.inputs.items()],
                     'inputConnections': inputConns,
                     'outputs': [(outputName, out.varType.__name__, out.value, out.default)
                                 for outputName, out in self.outputs.items()],
                     'outputConnections': outputConns}

    @classmethod
    def matchHint(cls, text: str):
        return cls.matchInputHint(text) or cls.matchOutputHint(text)

    @classmethod
    def matchInputHint(cls, text: str):
        if text == 'object':
            return True
        if any([any([hint.startswith(text) for hint in inp.hints]) for inp in cls.__inputs__.values()]):
            return True

    @classmethod
    def matchOutputHint(cls, text: str):
        if text == 'object':
            return True
        if any([any([hint.startswith(text) for hint in out.hints]) for out in cls.__outputs__.values()]):
            return True


class ControlNode(Node):
    """
    Base class for nodes controlling the program flow e.g. If/Else constructs and loops.
    Control nodes have an additional control input and a finalize output.

    The control input is a special input that supports multiple input connections. For example a loop node gets
    notified of a finished iteration over its body by setting the input of the control input. If all iterations are
    completed, the last set input is passed to the finalize output.
    An If/Else construct uses the control input to notify the node that the selected branch terminated. When that
    happens, the value of the control input is set to the finalize output.

    Restricting the option to have multiple connections to ControlNodes only makes sure that the node responsible for
    branches in the execution tree is also the node responsible for putting the pieces back together.
    """
    Input('Start', object)
    Input('Control', object)
    Output('Final', object)

    def __init__(self, *args, **kwargs):
        super(ControlNode, self).__init__(*args, **kwargs)
        self.waiting = False




class SwitchNode(ControlNode):
    """
    Node for creating a basic if/else construction.
    The input 'Switch' accepts a bool. Depending of the value of the input, the 'True' or 'False' outputs are set to
    the value of the 'Start' input.
    As soon as the 'Control' input is set by one of the code branches originating from the 'True' and 'False' outputs,
    the value of the 'Final' output is set to the value of the 'Control' input.
    """
    Input('Switch', bool)
    Output('True', object)
    Output('False', object)

    def check(self):
        for inp in self.inputs.values():
            if inp.name == 'Control':
                continue
            if not inp.valueSet:
                print('        {}: Prerequisites not met.'.format(str(self)))
                return False
        return True
        if self.waiting:
            if self.inputs['Control'].valueSet:
                return True

    def run(self):
        print('Executing node {}'.format(self))
        if not self.waiting:
            if self._Switch:
                self._True(self._Start)
            else:
                self._False(self._Start)
        elif self.waiting:
            self._Final(self._Control)

    def notify(self):
        if not self.waiting:
            output = self.outputs['True'] if self._Switch else self.outputs['False']
            for con in self.graph.getConnectionsOfOutput(output):
                outputName = con['outputName']
                nextNode = con['inputNode']
                nextInput = con['inputName']
                nextNode.setInput(nextInput, self.outputs[outputName].value)
            self.waiting = True
        else:
            output = self.outputs['Final']
            for con in self.graph.getConnectionsOfOutput(output):
                outputName = con['outputName']
                nextNode = con['inputNode']
                nextInput = con['inputName']
                nextNode.setInput(nextInput, self.outputs[outputName].value)
            self.waiting = False


class CreateBool(Node):
    Input('Value', bool, select=(True, False))
    Output('Boolean', bool)

    def run(self):
        super(CreateBool, self).run()
        self._Boolean(self._Value)

class CreateInt(Node):
    Input('Value', int, select=(1, 2, 3, 4, 5))
    Output('Integer', int)
    def run(self):
        super(CreateInt, self).run()
        self._Integer(self._Value)


class Pin(object):
    def __init__(self, pinID, info, node):
        self.ID = pinID
        self.name = info.name
        self.info = info
        info.ID = pinID
        self.node = node


class TestNode(Node):
    Input('strInput', str)
    Output('strOutput', str)

class FinalTestNode(TestNode):
    pass


class TestNode2(Node):
    Input('strInput', str)
    Input('floatInput', float, default=10.)
    Input('Input', str, default='TestNode')
    Output('strOutput', str)



class Loop(ControlNode):
    Input('Iterations', int)
    Output('LoopBody', object)

    def __init__(self, *args, **kwargs):
        super(ControlNode, self).__init__(*args, **kwargs)
        self.fresh = True
        self.counter = 0

    # def prepare(self):
    #     pass

    def check(self):
        if self.fresh:
            for inp in self.inputs.values():
                print('--------------',inp.name, inp.value, inp.valueSet, inp.default)
                if inp.name == 'Control':
                    continue
                if not inp.valueSet:
                    print(inp.name)
                    print('        {}: Prerequisites not met.'.format(str(self)))
                    return False
            return True
        if self.counter > 0:
            if self.inputs['Control'].valueSet:
                return True

    def run(self):
        print('Executing node {}'.format(self))
        if self.fresh:
            self.counter = self._Iterations
            self._LoopBody(self._Start)
            self.fresh = False
        elif self.counter == 0:
            self._Final(self._Control)
        else:
            self.counter -= 1
            self._LoopBody(self._Control)


    def notify(self):
        if self.counter > 0:
            output = self.outputs['LoopBody']
            for con in self.graph.getConnectionsOfOutput(output):
                outputName = con['outputName']
                nextNode = con['inputNode']
                nextInput = con['inputName']
                nextNode.prepare()
                nextNode.setInput(nextInput, self.outputs[outputName].value, override=True)
            self.inputs['Control'].reset()

        else:
            output = self.outputs['Final']
            for con in self.graph.getConnectionsOfOutput(output):
                outputName = con['outputName']
                nextNode = con['inputNode']
                nextInput = con['inputName']
                nextNode.setInput(nextInput, self.outputs[outputName].value)
            self.prepare()
            self.fresh = True
            for inp in self.inputs.values():
                inp.reset()
        # print(self.inProgress)
        # exit()





class WaitAll(Node):
    Input('1', object)
    Input('2', object)
    Output('out', object)


class WaitAny(WaitAll):

    def check(self):
        for inp in self.inputs.values():
            if inp.valueSet:
                print('        {}: Prerequisites not met.'.format(str(self)))
                return True

    def run(self):
        super(WaitAny, self).run()
        for inp in self.inputs.values():
            if inp.valueSet:
                self._out(inp.value)




class Test(Node):
    Input('Test', bool)
    Output('T', bool)

    def run(self):
        super(Test, self).run()
        print(self._Test)
        self._T(self._Test)

# TODO Cleanup this mess. Prepare method and probably a lot of other stuff is no longer needed. Fix SwitchNode.