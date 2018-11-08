'''
Function which can be used to measure accuracy of Hexastorm via camera

Connects to PiZero Camera and takes pictures
@company: Hexastorm
@author: Rik Starmans
'''
import zmq
import random
import sys
import time


port = '5556'
context = zmq.Context()
socket = context.socket(zmq.PAIR)
socket.bind('tcp://*:%s' % port)


while True:
    socket.send_string('Server message to client')
    msg = socket.recv_string()
    print(msg)
    time.sleep(1)