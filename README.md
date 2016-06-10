# Floppy
Flowchart Python -- A multipurpose Python node editor.

![alt tag](https://github.com/JLuebben/Floppy/tree/master/floppy/ressources/img.png)

Floppy includes a PyQt5 based graphical editor for creating graphs consisting of logically connected nodes.
Floppy also provides an interpreter for these graphs that can run on a remote machine and is controlled via TCP/IP.

A main design goal is to make the addition of custom nodes as easy as possible. For example the following code will
make a node for adding two integer available in the editor:


    class AddIntergers(Node):
        Input('Integer1', int)
        Input('Integer2', int)
        Output('Sum', int)

    def run():
        self._Sum(self._Integer1 + self._Integer2)


While most IDEs will complain about the code the Node class's meta class takes care of making the objects 'Input' and
'Output' available in the class's scope. The meta class will also make sure the editor itself is aware of the newly
defined node class.
Every defined input can be accessed either by using 'self._<InputName>' or by using 'self.inputs[\'<InputName>\']''.
Outputs are set by calling the 'self._<OutputName>(<value>)' object with the new value as argument.

By default any custom node will wait for all inputs to be set before trying to execute a node. If a more sophisticated
check is required, the 'Node.check()' method can be overridden.

After executing a node the node\'s 'notify()' method is called to notify all connected nodes about possible changes to
the inputs they are waiting for. Custom post-execution behavior can be implemented here.
