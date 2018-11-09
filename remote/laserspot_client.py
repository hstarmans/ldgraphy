#!/usr/bin/env python3
'''
Script that runs on the client side

Connects to PiZero Camera and takes pictures
Server side, first start client at Pizero camera.
@company: Hexastorm
@author: Rik Starmans
'''
import argparse
import zmq
import random
import time
from logger import init_logs
import logging


# ZMQ
PORT = '5556'


def parse_args():
	parser = argparse.ArgumentParser()
	parser.add_argument('--debug', action='store_true', help='prints log messages,' + 
                        'shows processor exceptions, writes logs on current dir')
	return parser.parse_args()


def main():
    context = zmq.Context()
    socket = context.socket(zmq.PAIR)
    socket.connect('tcp://10.42.0.192:%s' % PORT)
    while True:
        msg = socket.recv_string()
        logging.info('Received {}'.format(msg))
        socket.send_string('client message to server1')
        socket.send_string('client message to server2')
        time.sleep(1)


if __name__ == '__main__':
    args = parse_args()
    init_logs(args.debug)
    logging.info('Starting Laserspot Client')
    main()
