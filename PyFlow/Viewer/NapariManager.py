# import napari
# import sys
# sys.path.append('./') # Necessary to be able to import the following when running independently from PyFlow

# from PyFlow.ToolManagement import host

# import logging
# import traceback
# from importlib import import_module
# from multiprocessing.connection import Listener
# from PyFlow.Viewer import environment, dependencies

# from napari.qt.threading import thread_worker



# logging.basicConfig(
#     level=logging.INFO,
#     handlers=[
#         logging.FileHandler('napariManager.log'),
# 		logging.StreamHandler()
#     ]
# )

# logger = logging.getLogger(__name__)


# class NapariManager:

# 	environment = environment
# 	dependencies = dependencies
# 	viewer = None

# 	def __init__(self) -> None:
# 		pass

# 	def launchNapari(self):
# 		logger.info(f'launchNapari')
# 		cv = napari.current_viewer()
# 		logger.info(f'got cv {cv}')
# 		if self.viewer is None or cv is None:
# 			logger.info(f'create viewer')
# 			self.viewer = napari.Viewer()
# 			logger.info(f'viewer created')
# 		logger.info(f'end launch napari')
	
# 	def addImage(self, imagePath, removeOthers=False):
# 		logger.info(f'addImage()')
# 		self.launchNapari()
# 		if removeOthers:
# 			self.viewer.layers.clear()
# 		logger.info(f'open {imagePath}')
# 		self.viewer.open(imagePath)
# 		logger.info(f'show')
# 		self.viewer.show()
# 		logger.info(f'shown')

# logger.info('Init napari manager')

# napariManager = NapariManager()
# napariManager.launchNapari()

# def getMessage(connection):
# 	logger.info(f'Waiting for message...')
# 	return connection.recv()

# @thread_worker
# def launchListener(listenerPort):
# 	logger.info(f'launchListener {host}:{listenerPort}')
# 	with Listener((host, listenerPort)) as listener:
# 		while True:
# 			logger.info(f'Listen {host}:{listenerPort}')
# 			# Print ready message for the environment manager (it can now open a client to send messages)
# 			print(f'Listen {host}:{listenerPort}')
# 			with listener.accept() as connection:
# 				logger.info(f'Connection accepted {host}:{listenerPort}')
# 				try:
# 					while message := getMessage(connection):
# 						logger.info(f'Got message: {message}')
# 						try:
# 							if message['action']  == 'execute':
# 								_ = yield message['args']
# 								connection.send(dict(action='execution finished', message='process execution done'))
# 							if message['action'] == 'exit':
# 								logger.info(f'exit')
# 								connection.send(dict(action='exited'))
# 								return
# 						except Exception as e:
# 							logger.error('Caught exception:')
# 							logger.error(e)
# 							logger.error(e.args)
# 							logger.error(traceback.format_exc())
# 							# '\n'.join(traceback.format_tb(e.__traceback__))
# 							connection.send(dict(action='error', exception=e, traceback=traceback.format_exc()))
# 				except Exception as e:
# 					logger.error('Caught exception while waiting for message:')
# 					logger.error(e)
# 					logger.error(e.args)
# 					logger.error(traceback.format_exc())
# 					connection.send(dict(action='error', exception=e))

# def addImage(args):
# 	logger.info(f'add image')
# 	napariManager.addImage(*args)

# if __name__ == '__main__':
# 	if len(sys.argv)>1 and sys.argv[1] == '--listener_port':
# 		logger.info(f'main')
# 		worker = launchListener(int(sys.argv[2]))
# 		# worker.yielded.connect(lambda args: napariManager.addImage(*args))
# 		worker.yielded.connect(addImage)
# 		worker.start()

# napari.run()

import sys
import napari
from multiprocessing.connection import Listener
from napari.qt.threading import thread_worker

viewer = napari.Viewer()

def add_image(image_path, remove_others=False):
	print('add image', image_path, remove_others)
	if remove_others:
		viewer.layers.clear()
	viewer.open(image_path)

@thread_worker
def launch_listener():
	with Listener(('localhost', 0)) as listener:
		print(f'Listening port {listener.address[1]}')
		with listener.accept() as connection:
			print(f'accecpted')
			while message := connection.recv():
				_ = yield message

worker = launch_listener()
worker.yielded.connect(lambda args: add_image(*args))
worker.start()

napari.run()

