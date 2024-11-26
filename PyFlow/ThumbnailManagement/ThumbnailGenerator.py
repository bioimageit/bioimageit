import json
from pathlib import Path
import queue
import pandas
import shutil
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

class ThumbnailGenerator:
	
	instance = None
	finished = Signal(object)
	queue = queue.Queue()

	def __init__(self) -> None:
		self.imageToThumbnail: dict[str, PathInfo] = {}
		self.environment = environmentManager.launch('bioimageit')
		if self.environment.process is not None:
			inthread(self.logOutput, self.environment.process)
		inthread(self._generateThumbnailsThread)

	@classmethod
	def logOutput(cls, process):
		with process.stdout:
			for line in process.stdout:
				print(line)
		return
	
	# @staticmethod
	# def thumbnail(inputPath, outputPath, size=(128,128)): 
	# 	try:
	# 		# Load just once, then successively scale down
	# 		im = Image.open(inputPath)
	# 		if im.mode[0] in ['I', 'F']:
	# 			data = np.asarray(im)
	# 			dmax, dmin = data.max(), data.min()
	# 			data = 255.0 * ( data - dmin ) / (dmax - dmin) if abs(dmax - dmin) > 0 else data
	# 			im = Image.fromarray(data.astype(np.uint8))
	# 		im.thumbnail(size)
	# 		im.save(outputPath)
	# 		return (inputPath, outputPath)
	# 	except Exception as e:
	# 		return e 

	def setWorkflowPathAndLoadImageToThumbnail(self, workflowPath):
		self.workflowPath = workflowPath
		imageToThumbnailPath = self.getThumbnailsPath() / 'imageToThumbnail.json'
		if imageToThumbnailPath.exists():
			with open(imageToThumbnailPath, 'r') as f:
				try:
					self.imageToThumbnail = json.load(f)
				except json.JSONDecodeError:
					self.imageToThumbnail = {}
		else:
			self.imageToThumbnail = {}
		
	def getThumbnailsPath(self):
		thumbnailsPath = Path(self.workflowPath) / 'Thumbnails'
		thumbnailsPath.mkdir(exist_ok=True, parents=True)
		return thumbnailsPath

	def getNodeThumbnailsPath(self, nodeName):
		return self.getThumbnailsPath() / nodeName
	
	def getThumbnailPath(self, imagePath):
		imagePath = str(imagePath) if isinstance(imagePath, Path) else imagePath
		if imagePath is None or not isinstance(imagePath, str): return None
		return Path(self.imageToThumbnail[imagePath]['path']) if imagePath in self.imageToThumbnail and self.imageToThumbnail[imagePath]['path'] is not None else None

	# Generate a unique name for each item from the row and col indices ; since 2 images in 2 different folders could have the same stem.
	# The same image (full path) gets a unique thumbnail stored in self.imageToThumbnail
	def generateThumbnailPath(self, nodeName, path, rowIndex, colIndex, thumbnailsPath=None):
		thumbnailsPath = self.getNodeThumbnailsPath(nodeName) if thumbnailsPath is None else thumbnailsPath
		return thumbnailsPath / f'{Path(path).stem}_{rowIndex}-{colIndex}.png'

	def _generateThumbnailsThread(self):
		while True:
			images = self.queue.get()
			results = self.environment.execute('PyFlow.ThumbnailManagement.generate_thumbnails', 'generateThumbnails', [images])
			inmain(self._finishGenerateThumbnails, results)
			self.queue.task_done()

	def _generateThumbnails(self, images):
		# multiprocessing.set_start_method('spawn')
		# pool = multiprocessing.Pool(8)
		# print(f'generate {len(images)} thumbnails')
		# results = pool.starmap(self.thumbnail, images)

		# results = [self.thumbnail(inputPath, outputPath) for inputPath, outputPath in images]
		# # self._finishGenerateThumbnails(results)

		# results = generateThumbnails(images)
		# inmain(self._finishGenerateThumbnails, results)
		results = self.environment.execute('PyFlow.ThumbnailManagement.generate_thumbnails', 'generateThumbnails', [images])
		inmain(self._finishGenerateThumbnails, results)
		return
	
	def _finishGenerateThumbnails(self, results):
		for result in results:
			if not isinstance(result, Exception):
				self.imageToThumbnail[result[0]]['path'] = result[1]
		with open(self.getThumbnailsPath() / 'imageToThumbnail.json', 'w') as f:
			json.dump(self.imageToThumbnail, f)
		print(f'generated {len(results)} thumbnails')
		self.finished.send(results)
		return
	
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

			# thread = threading.Thread(target=self._generateThumbnails, args=images)
			# thread.daemon = True
			# thread.start()
			
			# inthread(self._generateThumbnails, images)
			self.queue.put(images)

			# self._generateThumbnails(images)
		return 

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
	
	@classmethod
	def get(cls):
		if cls.instance is None:
			cls.instance = ThumbnailGenerator()
		return cls.instance