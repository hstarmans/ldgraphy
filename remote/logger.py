
"""
Logging functionality for Pi Zero camera's

@company: Hexastorm
@author: Rik Starmans
"""
import logging
from logging.handlers import SysLogHandler, TimedRotatingFileHandler
import time
import sys


# LOG FORMAT
LOGGING_FILE = '/var/log/hexastorm/picamera.log'
LOGGING_FORMAT = '%(asctime)s %(process)s %(levelname)s %(filename)s:%(lineno)d - %(message)s'
LOGGING_DATE = '%Y-%m-%dT%H:%M:%S'


class StreamToLogger(object):
	"""
	Fake file-like stream object that redirects writes to a logger instance.
	Needed to redirect stderror to the log
	"""
	def __init__(self, logger, log_level=logging.INFO):
		self.logger = logger
		self.log_level = log_level
		self.linebuf = ''

	def write(self, buf):
		for line in buf.rstrip().splitlines():
			self.logger.log(self.log_level, line.rstrip())


def init_logs(debug=False):
	if debug:
		LOGGING_FILE = './picamera.log'
	# UTC timezone
	logging.Formatter.converter = time.gmtime
	logging.basicConfig(
		filename=LOGGING_FILE,
		level=logging.DEBUG,
		format=LOGGING_FORMAT,
		datefmt=LOGGING_DATE
	)
	logger = logging.getLogger()
	logger.setLevel(logging.DEBUG)
	# logs are rotated every hour
	#fh = TimedRotatingFileHandler('filename', when="d", interval=1, backupCount=5)
	#fh.setFormatter(logging.Formatter('format'))
	#logger.addHandler(fh)
	# hook stderr to stream
	if not debug:
		sys.stderr = StreamToLogger(logger, logging.ERROR)
	if sys.platform == 'linux':
		# syslog
		sh = SysLogHandler(address='/dev/log')
		logger.addHandler(sh)
	if debug:
		# Print logs on screen
		ch = logging.StreamHandler(sys.stdout)
		ch.setLevel(logging.DEBUG)
		logger.addHandler(ch)

