import json
from pathlib import Path
import queue
import pandas
import shutil
import threading
from PyFlow.invoke_in_main import inmain, inthread
from blinker import Signal
# import threading
from PyFlow.ToolManagement.EnvironmentManager import environmentManager
# Warning: we cannot import generate_thumbnails.generateThumbnails directly here, otherwise the multiprocessing will initialize the entire BioImageIT app for each parallel process!
# from PyFlow.ThumbnailManagement.generate_thumbnails import generateThumbnails
import sys

if sys.version_info < (3, 11):
	from typing_extensions import TypedDict
else:
	from typing import TypedDict

class PathInfo(TypedDict):
	nodes: list[str]
	path: str

# Lock is not mandatory since all is in main thread. 
# Keep in case API changes, to show that ThumbnailGenerator.lowPath and ThumbnailGenerator.imageToThumbnail must be "thread safe".
lock = threading.Lock()

class ThumbnailGenerator:
	
	instance = None
	finished = Signal(object)
	queue = queue.Queue()

	def __init__(self) -> None:
		self.imageToThumbnail: dict[str, PathInfo] = {}
		self.environment = environmentManager.createAndLaunch('thumbnailGenerator', {'pip': ["h5py==3.11.0", "pillow==11.1.0", "numpy==2.2.3"]})
		if self.environment.process is not None:
			inthread(self.logOutput, self.environment.process)
		inthread(self._generateThumbnailsThread)

	@classmethod
	def logOutput(cls, process):
		with process.stdout:
			for line in process.stdout:
				print(line)
		return
	
	# Main thread
	def loadImageToThumbnail(self, workflowPath=None):
		imageToThumbnailPath = self.getThumbnailsPath(workflowPath or self.workflowPath) / 'imageToThumbnail.json'
		imageToThumbnail = {}
		if imageToThumbnailPath.exists():
			with open(imageToThumbnailPath, 'r') as f:
				try:
					imageToThumbnail = json.load(f)
				except json.JSONDecodeError:
					pass
		return imageToThumbnail
	
	# Main thread
	def setWorkflowPathAndLoadImageToThumbnail(self, workflowPath):
		with lock:
			self.workflowPath = workflowPath
			self.imageToThumbnail = self.loadImageToThumbnail()
		
	# Main thread
	def getThumbnailsPath(self, workflowPath=None):
		thumbnailsPath = Path(workflowPath or self.workflowPath) / 'Thumbnails'
		thumbnailsPath.mkdir(exist_ok=True, parents=True)
		return thumbnailsPath

	# Main thread
	def getNodeThumbnailsPath(self, nodeName):
		return self.getThumbnailsPath() / nodeName
	
	# Main thread
	def getThumbnailPath(self, imagePath):
		imagePath = str(imagePath) if isinstance(imagePath, Path) else imagePath
		if imagePath is None or not isinstance(imagePath, str): return None
		return Path(self.imageToThumbnail[imagePath]['path']) if imagePath in self.imageToThumbnail and self.imageToThumbnail[imagePath]['path'] is not None else None

	# Main thread
	# Generate a unique name for each item from the row and col indices ; since 2 images in 2 different folders could have the same stem.
	# The same image (full path) gets a unique thumbnail stored in self.imageToThumbnail
	def generateThumbnailPath(self, nodeName, path, rowIndex, colIndex, thumbnailsPath=None):
		thumbnailsPath = self.getNodeThumbnailsPath(nodeName) if thumbnailsPath is None else thumbnailsPath
		return thumbnailsPath / f'{Path(path).stem}_{rowIndex}-{colIndex}.png'

	# ThumbnailGenerator thread
	def _generateThumbnailsThread(self):
		while True:
			taskData = self.queue.get()
			results = self.environment.execute('PyFlow.ThumbnailManagement.generate_thumbnails', 'generateThumbnails', [taskData])
			if results is None: continue
			inmain(self._finishGenerateThumbnails, results)
			self.queue.task_done()
	
	# Main thread
	def _finishGenerateThumbnails(self, results):
		with lock:
			imageToThumbnail = self.imageToThumbnail if self.workflowPath == results['workflowPath'] else self.loadImageToThumbnail(results['workflowPath'])
			for path in results['paths']:
				if not isinstance(path, Exception):
					imageToThumbnail[path[0]]['path'] = path[1]
			with open(self.getThumbnailsPath(results['workflowPath']) / 'imageToThumbnail.json', 'w') as f:
				json.dump(imageToThumbnail, f)
			print(f'generated {len(results)} thumbnails')
			self.finished.send(results)
		return
	
	# Main thread
	def generateThumbnails(self, nodeName, dataFrame: pandas.DataFrame):
		if dataFrame is None: return
		thumbnailsPath = self.getNodeThumbnailsPath(nodeName)
		thumbnailsPath.mkdir(exist_ok=True, parents=True)
		images = []
		
		for ri, row in dataFrame.iterrows():
			for ci, item in enumerate(row):
				if not (isinstance(item, Path) or isinstance(item, str)): continue
				item = str(item)
				if item in self.imageToThumbnail:
					if nodeName not in self.imageToThumbnail[item]['nodes']:
						self.imageToThumbnail[item]['nodes'].append(nodeName)
					if self.imageToThumbnail[item]['path'] is not None: continue
				else:
					self.imageToThumbnail[item] = dict(nodes=[nodeName], path=None)
				if not Path(item).is_file(): continue
				thumbnailPath = self.generateThumbnailPath(nodeName, item, ri, ci, thumbnailsPath)
				images.append((item, str(thumbnailPath)))

		if len(images)>0:
			self.queue.put(dict(images=images, workflowPath=self.workflowPath))
		return 

	# Main thread
	def deleteThumbnails(self, nodeName):
		for path, pathInfo in list(self.imageToThumbnail.items()):
			if nodeName in pathInfo['nodes']:
				pathInfo['nodes'].remove(nodeName)
			if len(pathInfo['nodes']) == 0:
				if 'path' in pathInfo and (pathInfo['path'] is not None) and Path(pathInfo['path']).exists():
					Path(pathInfo['path']).unlink()
				del self.imageToThumbnail[path]
		folder:Path = self.getNodeThumbnailsPath(nodeName)
		if folder.exists() and len(list(folder.iterdir()))==0:
			folder.rmdir()
	
	# Main thread
	@classmethod
	def get(cls):
		if cls.instance is None:
			cls.instance = ThumbnailGenerator()
		return cls.instance