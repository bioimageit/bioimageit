import sys
import logging
import traceback
from importlib import import_module
from multiprocessing.connection import Listener

sys.path.append('./') # Necessary to be able to import when running independently from PyFlow
# from PyFlow.ToolManagement import host
# from PyFlow.invoke_in_main import inthread

# import pdb_attach
# pdb_attach.listen(50000)


# Configure the logging from now: write all INFO logs to environment.log, stdout and stderr 
logging.basicConfig(
    level=logging.INFO,
    handlers=[
        logging.FileHandler('environment.log'),
        logging.StreamHandler()
    ]
)

# Create another logger for this file which will also write to environment.log, but not stdout and stderr
logger = logging.getLogger(__name__)
fileHandler = logging.FileHandler('environment.log', encoding='utf-8')
fileHandler.setLevel(logging.INFO)
logger.addHandler(fileHandler)

# class WriteProcessor:

# 	def __init__(self, connection):
# 		self.buf = ""
# 		self.connection = connection

# 	# Fills self.buf until it contains new line, then sends it to connection
# 	def write(self, buf):
# 		# emit on each newline
# 		while buf:
# 			try:
# 				newline_index = buf.index("\n")
# 			except ValueError:
# 				# no newline, buffer for next call
# 				self.buf += buf
# 				break
# 			# get data to next newline and combine with any buffered data
# 			data = self.buf + buf[:newline_index + 1]
# 			self.buf = ""
# 			buf = buf[newline_index + 1:]
# 			self.connection.send(dict(action='print', content=data))

def getMessage(connection):
	logger.debug(f'Waiting for message...')
	return connection.recv()

def launchListener():
	with Listener(('localhost', 0)) as listener:
		while True:
			# Print ready message for the environment manager (it can now open a client to send messages)
			print(f'Listening port {listener.address[1]}')
			with listener.accept() as connection:
				logger.debug(f'Connection accepted {listener.address}')
				try:
					while message := getMessage(connection):
						logger.debug(f'Got message: {message}')
						try:
							if message['action']  == 'execute':
								# Redirect all outputs to connection.send
								# with redirect_stdout(WriteProcessor(connection)):
								logger.debug(f'Execute {message["module"]}.{message["function"]}({message["args"]})')
								module = import_module(message['module'])
								if not hasattr(module, message['function']):
									raise Exception(f'Module {message["module"]} has no function {message["function"]}.')
								getattr(module, message['function'])(*message['args'])
								logger.debug(f'Executed')
								connection.send(dict(action='execution finished', message='process execution done'))
							if message['action'] == 'exit':
								logger.debug(f'exit')
								connection.send(dict(action='exited'))
								return
						except Exception as e:
							logger.error('Caught exception:')
							logger.error(e)
							logger.error(e.args)
							logger.error(traceback.format_exc())
							# '\n'.join(traceback.format_tb(e.__traceback__))
							connection.send(dict(action='error', exception=e, traceback=traceback.format_exc()))
				except Exception as e:
					logger.error('Caught exception while waiting for message:')
					logger.error(e)
					logger.error(e.args)
					logger.error(traceback.format_exc())
					logger.error(message)
					connection.send(dict(action='error', exception=e))

if __name__ == '__main__':
	launchListener()
	
logger.debug('Exit')