"""
Module implementing a program for executing a Floppy graph.
The program can be called from the Floppy editor but will run independently from the calling process.
Communication between the editor and the runner is realized via Sockets.
The runner will report its status to the editor and the editor is able to send commands to the runner.
"""

from threading import Thread, Lock
import time
from queue import Queue
from socket import AF_INET, SOCK_STREAM, socket, SHUT_RDWR
import random

host = '127.0.0.1'
port = 7236

xLock = Lock()


class Runner(object):

    def __init__(self):
        self.graph = list(range(10))
        self.cmdQueue = Queue(1)
        self.listener = Listener(self)
        self.executionThread = ExecutionThread(self.cmdQueue, self)

    def updateGraph(self, fileName):
        self.graph= list(range(int(random.randrange(1,10))))
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


class ExecutionThread(Thread):
    def __init__(self, cmdQueue, master):
        self.master = master
        self.paused = False
        self.alive = True
        self.cmdQueue = cmdQueue
        super(ExecutionThread, self).__init__()
        self.updateGraph()
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
                time.sleep(.1)
                continue
            print('Doing stuff.')
            print(self.graph)
            time.sleep(.5)
        print('That\'s it. I\'m dead.')

    def pause(self):
        self.paused = True

    def unpause(self):
        self.paused = False

    def kill(self):
        self.alive = False

    def updateGraph(self):
        self.graph = self.master.graph[:]




class Listener(Thread):
    def __init__(self, master):
        Thread.__init__(self)
        self.listenSocket = socket(AF_INET, SOCK_STREAM)
        self.listenSocket.bind((host, port))
        self.listenSocket.listen(5)
        self.master = master
        self.daemon = True
        self.start()

    def run(self):
        while True:
            cSocket, address = self.listenSocket.accept()
            if str(address[0]) == '127.0.0.1':
                CommandProcessor(cSocket, address, self.master)


class CommandProcessor(Thread):
    def __init__(self, Socket, Adress, master):
        super(CommandProcessor, self).__init__()
        self.master = master
        self.socket = Socket
        self.daemon = True
        self.start()

    def run(self):
        while True:
            message = self.socket.recv(1024).decode()
            if message:
                if message == 'KILL':
                    # print('Killing myself')
                    self.socket.send('Runner is terminating.'.encode())
                    self.master.kill()
                    break
                elif message == 'PAUSE':
                    self.socket.send('Runner is pausing.'.encode())
                    self.master.pause()
                    break
                elif message == 'UNPAUSE':
                    self.socket.send('Runner is unpausing.'.encode())
                    self.master.unpause()
                    break
                elif message == 'UPDATE':
                    self.socket.send('Runner is updating.'.encode())
                    self.master.updateGraph('')
                    break



# from socket import AF_INET, SOCK_STREAM, socket


def terminate(clientSocket):
    message = 'Kill'
    clientSocket.send(message.encode())
    print('Kill command sent.')

    answer = clientSocket.recv(1024).decode()

    print(answer)


def sendCommand(cmd):
    # global clientSocket
    clientSocket = socket(AF_INET, SOCK_STREAM)

    host = '127.0.0.1'
    port = 7236

    clientSocket.connect((host, port))
    clientSocket.send(cmd.encode())
    print('Sent {} command'.format(cmd))
    # terminate(clientSocket)
    answer = clientSocket.recv(1024).decode()

    print(answer)
    clientSocket.close()

if __name__ == '__main__':
    r = Runner()
    # input()
    # r.pause()
    # input()
    # r.unpause()
    # input()
    # r.updateGraph('')
    # input()
    # r.kill()
    # input()
    # sendCommand()


    # while True:
    #     time.sleep(1)
    #     sendCommand('KILL')
    #     break
    while True:
        sendCommand(str(input()))