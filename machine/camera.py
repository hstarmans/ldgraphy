'''
Class which can be used to make pictures with a remote camera

In the remote folder is class which must be run on the camera machine.
THe camera class can then connect via ZMQ and ethernet to this machine and make pictures.
This was done as I wasn't able to install ueye and opencv on the beaglebone.
Also the viewing of images is slow as the beaglebone is headless.

@license: GPLv3
@company: Hexastorm
@author: Rik Starmans
'''
import zmq

class Camera:
    '''
    class to interact with remote camera via ZMQ
    '''
    def __init__(self, camera = False):
        self.connect()
        if not self.is_connected():
            raise Exception('Can not connect to camera')


    def connect(self, port = '5556'):
        '''
        connect with remote camera
        '''
        context = zmq.Context()
        self.socket = context.socket(zmq.PAIR)
        self.socket.bind('tcp://*:%s' % port)


    def set_exposure(self, ms):
        '''
        sets exposure in ms
        '''
        self.socket.send_string('set_exposure({})'.format(ms))
        return self.socket.recv_pyobj()


    def is_connected(self):
        '''
        checks connection
        '''
        self.socket.send_string('is_connected()')
        return self.socket.recv_pyobj()


    def get_spotinfo(self, wait=True):
        '''
        return spotsize and position in dictionary
        '''
        self.socket.send_string('get_spotinfo()')
        if wait:
            return self.socket.recv_pyobj()
    
    def get_answer(self):
        return self.socket.recv_pyobj()