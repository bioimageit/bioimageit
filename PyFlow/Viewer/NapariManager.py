import napari
from multiprocessing.connection import Listener
import napari._event_loop
from napari.qt.threading import thread_worker

viewer = napari.Viewer()

connection = None

def add_image(image_path, remove_others=False):
	print('add image', image_path, remove_others)
	if remove_others:
		viewer.layers.clear()
	# viewer.open([image_path], plugin=None)
	viewer.window.qt_viewer._qt_open([image_path], stack=False)

@thread_worker
def launch_listener():
	with Listener(('localhost', 0)) as listener:
		print(f'Listening port {listener.address[1]}')
		global connection
		try:
			with listener.accept() as c:
				connection = c
				print(f'accepted')
				while message := connection.recv():
					_ = yield message
		except Exception as e:
			print(e)
			return


worker = launch_listener()

from qtpy.QtWidgets import QApplication

def onClose():
	if connection is not None:
		connection.close()
	worker.quit()

QApplication.instance().lastWindowClosed.connect(onClose) 
QApplication.instance().setQuitOnLastWindowClosed(True)

worker.yielded.connect(lambda args: add_image(*args))
worker.start()

napari.run()

