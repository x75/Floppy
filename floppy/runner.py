"""
Module implementing a program for executing a Floppy graph.
The program can be called from the Floppy editor but will run independently from the calling process.
Communication between the editor and the runner is realized via Sockets.
The runner will report its status to the editor and the editor is able to send commands to the runner.
"""

from threading import Thread, Lock
import time
from queue import Queue
from socket import AF_INET, SOCK_STREAM, socket, SHUT_RDWR, timeout, SHUT_RDWR, SO_REUSEADDR, SOL_SOCKET
import json
import struct


# host = '127.0.0.1'
# host = '10.76.64.86'
host = ''
port = 7236

updatePort = 7237

xLock = Lock()


class Runner(object):

    def __init__(self):
        self.conn = None
        self.idMap = None
        self.nextNodePointer = None
        self.currentNodePointer = None
        self.lastNodePointer = None
        self.graphData = {}
        self.cmdQueue = Queue(1)
        self.listener = Listener(self)
        self.executionThread = ExecutionThread(self.cmdQueue, self)

        self.updateSocket = socket(AF_INET, SOCK_STREAM)
        self.updateSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.updateSocket.bind((host, updatePort))
        self.updateSocket.listen(1)
        self.conn, self.clientAddress = None, None
        self.status = []

    def __del__(self):
        self.updateSocket.close()

    def resetPointers(self):
        self.nextNodePointer = None
        self.currentNodePointer = None
        self.lastNodePointer = None

    def recvall(self, sock, n, retry=5):
        # Helper function to recv n bytes or return None if EOF is hit
        data = b''
        while len(data) < n:
            packet = sock.recv(n - len(data))
            if not packet:
                if retry>0:
                    time.sleep(.1)
                    self.recvall(sock, n, retry-1)
                else:
                    self.conn , address = self.updateSocket.accept()
                    return self.updateGraph('')
            data += packet
        return data

    def updateGraph(self, data):
        # if not self.conn:
        #     self.conn , address = self.updateSocket.accept()
        # import struct
        #
        # raw_msglen = self.recvall(self.conn, 4, 5)
        # if not raw_msglen:
        #     return None
        # msglen = struct.unpack('>I', raw_msglen)[0]
        # data = self.recvall(self.conn, msglen).decode('utf-8')
        data = json.loads(data)

        self.graphData = data
        xLock.acquire()
        if not self.cmdQueue.empty():
            self.cmdQueue.get()
        self.cmdQueue.put(ExecutionThread.updateGraph)
        xLock.release()

    def pause(self):
        xLock.acquire()
        if not self.cmdQueue.empty():
            self.cmdQueue.get()
        self.cmdQueue.put(ExecutionThread.pause)
        xLock.release()

    def kill(self):
        self.updateSocket.close()
        xLock.acquire()
        if not self.cmdQueue.empty():
            self.cmdQueue.get()
        self.cmdQueue.put(ExecutionThread.kill)
        xLock.release()

    def unpause(self):
        xLock.acquire()
        if not self.cmdQueue.empty():
            self.cmdQueue.get()
        self.cmdQueue.put(ExecutionThread.unpause)
        xLock.release()

    def goto(self, nextID):
        self.nextNodePointer = nextID

    def step(self):
        xLock.acquire()
        if not self.cmdQueue.empty():
            self.cmdQueue.get()
        self.cmdQueue.put(ExecutionThread.step)
        xLock.release()

    def updateStatus(self, ID):
        nodeID = self.idMap[ID]
        self.status.append(nodeID)

    def getStatus(self):
        string = '#'.join([str(i) for i in self.status])
        self.status = []
        return string

    # def sendStatus(self, nodeID):
    #     nodeID = self.idMap[nodeID]
    #     self.conn.send(('#'+str(nodeID)).encode('utf-8'))


class ExecutionThread(Thread):
    def __init__(self, cmdQueue, master):
        self.graph = None
        self.master = master
        self.paused = True
        self.alive = True
        self.cmdQueue = cmdQueue
        super(ExecutionThread, self).__init__()
        # self.updateGraph()
        self.start()

    def run(self):
        while self.alive:
            xLock.acquire()
            cmd = None
            if not self.cmdQueue.empty():
                cmd = self.cmdQueue.get()
            xLock.release()
            # print(cmd)
            if cmd:
                cmd(self)
            if self.paused:
                print('Sleeping')
                time.sleep(1)
                continue
            if self.alive and self.graph:

                # print(self.graph.nodes)
                #print('Doing stuff.')
                self.executeGraphStepPar()
            else:
                time.sleep(.5)
        print('That\'s it. I\'m dead.')

    def pause(self):
        self.paused = True

    def unpause(self):
        self.paused = False

    def kill(self):
        self.alive = False

    def step(self):
        print('Stepping up.')
        self.executeGraphStepPar()

    def updateGraph(self):
        from floppy.graph import Graph
        self.graph = Graph()
        # print(type(self.master.graph))
        idMap = self.graph.loadState(self.master.graphData)
        self.master.idMap = {value:key for key, value in idMap.items()}
        #self.resetPointers()

    def executeGraphStep(self):
        if self.master.nextNodePointer:
            print(self.master.nextNodePointer, self.graph.nodes.keys())
            nextNode = self.graph.nodes[self.master.nextNodePointer]
            self.master.nextNodePointer = None
            if nextNode.check():
                nextNode.run()
                nextNode.notify()
                self.master.sendStatus(nextNode.ID)
        else:
            running = False
            for node in self.graph.nodes.values():
                checked = node.check()
                running = checked if not running else True
                if checked:
                    node.run()
                    # self.graph.runNodePar(node)
                    # raise RuntimeError('Uncaught exception while executing node {}.'.format(node))
                    node.notify()
                    # self.master.sendStatus(node.ID)
                    self.master.updateStatus(node.ID)
                    break
            if not running:
                print('Nothing to do here @ {}'.format(time.time()))
                time.sleep(.5)

    def executeGraphStepPar(self):
        if self.master.nextNodePointer:
            # print(self.master.nextNodePointer, self.graph.nodes.keys())
            nextNode = self.graph.nodes[self.master.nextNodePointer]
            self.master.nextNodePointer = None
            if nextNode.check():
                nextNode.run()
                nextNode.notify()
                self.master.sendStatus(nextNode.ID)
        else:
            running = False
            readyNodes = []
            for node in self.graph.nodes.values():
                checked = node.check()
                running = checked if not running else True
                if checked and not node.locked:
                    readyNodes.append(node)
                    node.lock()
            for node in readyNodes:
                self.graph.runNodePar(node, cb=self.master.updateStatus, arg=node.ID)
            if not running:
                print('Nothing to do here @ {}'.format(time.time()))
                time.sleep(.5)

    def execute(self):
        """
        Execute the Graph instance.

        First, the execution loop will set itself up to terminate after the first iteration.
        Next, every node is given the chance to run if all prerequisites are met.
        If a node is executed, the loop termination criterion will be reset to allow an additional iteration over all
        nodes.
        If no node is execute during one iteration, the termination criterion will not be reset and the execution loop
        terminates.
        :return:
        """
        return self.testRun()
        running = True
        i = 0
        while running:
            i += 1
            print('\nExecuting iteration {}.'.format(i))
            running = False
            for node in self.nodes.values():
                checked = node.check()
                running = checked if not running else True
                if checked:
                    node.run()
                    # raise RuntimeError('Uncaught exception while executing node {}.'.format(node))
                    node.notify()


class Listener(Thread):
    def __init__(self, master):
        Thread.__init__(self)
        self.alive = True
        self.listenSocket = socket(AF_INET, SOCK_STREAM)
        self.listenSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.listenSocket.settimeout(1)
        self.listenSocket.bind((host, port))
        self.listenSocket.listen(1)
        self.master = master
        self.daemon = True
        self.start()

    def kill(self):
        self.alive = False
        time.sleep(.1)
        # self.listenSocket.shutdown(SHUT_RDWR)
        self.listenSocket.close()

    def run(self):
        while self.alive:
            # print('++++++++++Waiting for client.')
            try:
                cSocket, address = self.listenSocket.accept()
                print('++++++++++client accepted.')
            except OSError as x:
                continue
            # if str(address[0]) == '127.0.0.1':
            else:
                CommandProcessor(cSocket, address, self.master, self)


class CommandProcessor(Thread):
    def __init__(self, cSocket, Adress, master, listener):
        super(CommandProcessor, self).__init__()
        self.master = master
        self.cSocket = cSocket
        self.listener = listener
        self.daemon = True
        self.start()

    def send(self, message):
        msg = struct.pack('>I', len(message)) + message.encode('utf-8')
        self.cSocket.sendall(msg)
        # return '[ANSWER]  '+self.cSocket.recv(1024).decode()

    def run(self):
        while True:
            # message = self.cSocket.recv(1024).decode()
            message = self.receive()
            if message:
                if message == 'KILL':
                    # print('Killing myself')
                    self.send('Runner is terminating.')
                    self.listener.kill()
                    self.master.kill()
                    return
                elif message == 'READY?':
                    self.send('READY')
                elif message == 'PAUSE':
                    self.send('Runner is pausing.')
                    self.master.pause()
                elif message == 'UNPAUSE':
                    self.send('Runner is unpausing.')
                    self.master.unpause()
                elif message.startswith('UPDATE'):
                    self.send('Runner is updating.')
                    self.master.updateGraph(message[6:])
                elif message.startswith('GOTO'):
                    nextID = int(message[4:])
                    self.send('Runner jumping to node {}.'.format(nextID))
                    self.master.goto(nextID)
                elif message == 'STEP':
                    self.send('Runner is performing one step.')
                    self.master.step()
                elif message == 'STATUS':
                    status = self.master.getStatus()
                    self.send(status)
                else:
                    self.send('Command \'{}...\' not understood.'.format(message[:50]))

    def recvall(self, sock, n,):
        # Helper function to recv n bytes or return None if EOF is hit
        data = b''
        while len(data) < n:
            packet = sock.recv(n - len(data))
            if not packet:
                return False
            data += packet
        return data

    def receive(self):
        data = None
        raw_msglen = self.recvall(self.cSocket, 4)
        if not raw_msglen:
            return None
        msglen = struct.unpack('>I', raw_msglen)[0]
        # Read the message data
        try:
            data = self.recvall(self.cSocket, msglen).decode('utf-8')
        except AttributeError:
            print('[ERROR] No data received.')
        return data


class RGIConnection(object):
    def __init__(self, verbose=True):
        self.socket = None
        self.host = None
        self.port = None

    def connect(self, host, port, validate=True):
        self.host = host
        self.port = port
        self.socket = socket(AF_INET, SOCK_STREAM)
        self.socket.settimeout(5.)
        self.socket.connect((host, port))
        if validate:
            print(self.send('READY?'))


    def disconnect(self):
        self.socket.close()

    def reconnect(self):
        self.disconnect()
        time.sleep(.5)
        self.socket.connect((self.host, self.port))

    def send(self, message):
        print('[REQUEST] ' + message)
        msg = struct.pack('>I', len(message)) + message.encode('utf-8')
        self.socket.sendall(msg)
        try:
            answer = '[ANSWER]  '+self._receive()
        except TypeError:
            answer = ''
        return answer

    def _recvall(self, sock, n,):
        # Helper function to recv n bytes or return None if EOF is hit
        data = b''
        while len(data) < n:
            packet = sock.recv(n - len(data))
            if not packet:
                return False
            data += packet
        return data

    def _receive(self):
        data = None
        raw_msglen = self._recvall(self.socket, 4)
        if not raw_msglen:
            return None
        msglen = struct.unpack('>I', raw_msglen)[0]
        # Read the message data
        try:
            data = self._recvall(self.socket, msglen).decode('utf-8')
        except AttributeError:
            print('[ERROR] No data received.')
        return data


def terminate(clientSocket):
    message = 'Kill'
    clientSocket.send(message.encode())
    print('Kill command sent.')

    answer = clientSocket.recv(1024).decode()

    print(answer)


def sendCommand(cmd, host, port):
    port -= 1
    # global clientSocket
    clientSocket = socket(AF_INET, SOCK_STREAM)
    clientSocket.settimeout(5.)
    print(host,port)
    # host = '127.0.0.1'
    # port = 7236

    clientSocket.connect((host, port))
    clientSocket.send(cmd.encode())
    print('Sent {} command'.format(cmd))
    # terminate(clientSocket)
    try:
        answer = clientSocket.recv(1024).decode()
        print(answer)
    except timeout:
        print('Runner did not answer command \'{}\''.format(cmd))

    clientSocket.close()


def spawnRunner():
    pass

if __name__ == '__main__':
    import os
    from importlib.machinery import SourceFileLoader
    customNodesPath = os.path.join(os.path.realpath(__file__)[:-10], 'CustomNodes')
    for i, path in enumerate(os.listdir(customNodesPath)):
        if path.endswith('py'):
            try:
                SourceFileLoader(str(i), os.path.join(customNodesPath, path)).load_module()
            except Exception as e:
                print('Warning: error in custom node:\n{}'.format(str(e)))
    r = Runner()
