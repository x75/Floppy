# Floppy
Flowchart Python -- A multipurpose Python node editor.

![Example Graph](/floppy/ressources/img.png?raw=true "Graph Example")

Floppy includes a PyQt5 based graphical editor for creating graphs consisting of logically connected nodes.
Floppy also provides an interpreter for these graphs that can run on a remote machine and is controlled via TCP/IP.

A recently added feature is the automatic concurrent execution of graphs. The Graph Interpreter will continuously check
which nodes are ready to be executed and will then create a new thread for running each node.

To execute a graph, the editor must connect to a graph interpreter. If a graph interpreter is running on a remote
machine, the 'Connect' button can be used to establish a connection. However the easiest way is probably to create a local
interpreter by clicking the 'Spawn' button. To load the currently active graph instance on the interpreter side, it has to
be pushed via the 'Push' button. The 'Unpause' can then be used to start the execution.
The 'Step' button can be used instead of 'Unpause' to execute the graph one step at a time.

Now that I am writing this I realize how complicated that sounds... I need to change that.


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
Every defined input can be accessed either by using 'self.\_\<InputName\>' or by using 'self.inputs['\<InputName\>']''.
Outputs are set by calling the 'self.\_\<OutputName\>(\<value\>)' object with the new value as argument.

By default any custom node will wait for all inputs to be set before trying to execute a node. If a more sophisticated
check is required, the 'Node.check()' method can be overridden.

After executing a node the node's 'notify()' method is called to notify all connected nodes about possible changes to
the inputs they are waiting for. Custom post-execution behavior can be implemented here.
