import sys
import logging
import threading
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
		logging.FileHandler('environment_modules.log', encoding='utf-8'),
		logging.StreamHandler()
	]
)

# Create another logger for this file which will also write to environment.log, but not stdout and stderr
logger = logging.getLogger(__name__) # Name should contain the module name
fileHandler = logging.FileHandler('environment_modules.log', encoding='utf-8')
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

def functionExecutor(lock, connection, message):
	try:
		module = import_module(message['module'])
		if not hasattr(module, message['function']):
			raise Exception(f'Module {message["module"]} has no function {message["function"]}.')
		result = getattr(module, message['function'])(*message['args'])
		logger.info(f'Executed')
		with lock:
			connection.send(dict(action='execution finished', message='process execution done', result=result))
	except Exception as e:
		with lock:
			connection.send(dict(action='error', exception=str(e), traceback=traceback.format_tb(e.__traceback__)))

def launchListener():
	lock = threading.Lock()
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
								logger.info(f'Execute {message["module"]}.{message["function"]}({message["args"]})')
								
								thread = threading.Thread(target=functionExecutor, args=(lock, connection, message))
								thread.start()

							if message['action'] == 'exit':
								logger.info(f'exit')
								with lock:
									connection.send(dict(action='exited'))
								connection.close()
								listener.close()
								return
						except Exception as e:
							logger.error('Caught exception:')
							logger.error(e)
							logger.error(e.args)
							# logger.error(traceback.format_exc())
							for line in traceback.format_tb(e.__traceback__):
								logger.error(line)
							with lock:
								connection.send(dict(action='error', exception=str(e), traceback=traceback.format_tb(e.__traceback__)))
				except Exception as e:
					logger.error('Caught exception while waiting for message:')
					logger.error(e)
					logger.error(e.args)
					# logger.error(traceback.format_exc())
					for line in traceback.format_tb(e.__traceback__):
						logger.error(line)
					with lock:
						connection.send(dict(action='error', exception=str(e), traceback=traceback.format_tb(e.__traceback__)))

if __name__ == '__main__':
	launchListener()
	
logger.debug('Exit')
