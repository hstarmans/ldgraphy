#!/usr/bin/env python3
'''
Script that runs on the client side

Connects to uEye Camera and takes pictures
Start client before starting server
@company: Hexastorm
@author: Rik Starmans
'''
import argparse
import logging
import random
import time

import zmq

from logger import init_logs
import pyueye_utils
from pyueye import ueye
import spots

# ZMQ
PORT = '5556'


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', action='store_true', help='prints log messages,' + 
                    'shows processor exceptions, writes logs on current dir')
    return parser.parse_args()


class Cam:
    '''
    TODO: just fix the original object OMG
    '''
    def __init__(self):
        self.cam = pyueye_utils.Camera()
        if self.cam.init():	
            raise Exception("Can't init camera")
        self.cam.alloc()
        self.picnum = 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.cam.exit()

    def take_picture(self):
        """
        returns image as numpy array
        """
        if self.cam.capture_video():
            raise Exception("Can't start image capture")
        img_buffer = pyueye_utils.ImageBuffer()
        if ueye.is_WaitForNextImage(self.cam.handle(), 
                                    1000,
                                    img_buffer.mem_ptr,
                                    img_buffer.mem_id):
            raise Exception('Timeout on capture')

        image_data = pyueye_utils.ImageData(self.cam.handle(), img_buffer)
        img = image_data.as_1d_image()
        image_data.unlock()
        self.cam.stop_video()
        return img


def main():
    context = zmq.Context()
    socket = context.socket(zmq.PAIR)
    address = '10.42.0.192'
    print('Using address ' + address)
    socket.connect('tcp://'+address+':%s' % PORT)
    with Cam() as camera:
        camera.cam.set_pixelclock(20)
        
        def set_exposure(ms):
            camera.cam.set_exposure(ms)
            return True


        def get_spotinfo(debug=True):
            img = camera.take_picture()
            if debug:
                import cv2
                camera.picnum += 1
                cv2.imwrite(str(camera.picnum)+'.png', img)
            return spots.getellipse(img, pixelsize = 4.65)


        def is_connected():
            return True


        while True:
            msg = socket.recv_string()
            logging.info('Executing call {}'.format(msg))
            res = eval(msg)
            socket.send_pyobj(res)
            time.sleep(1)


if __name__ == '__main__':
    args = parse_args()
    init_logs(args.debug)
    logging.info('Starting Laserspot Client')
    main()
