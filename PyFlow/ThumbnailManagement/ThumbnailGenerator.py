import json
from pathlib import Path
import queue
import pandas
import numpy as np
from PyFlow.invoke_in_main import inmain, inthread
from blinker import Signal
# from PyFlow.Packages.PyFlowBase.Tools.generate_thumbnails import generateThumbnails
# import threading
from PyFlow.ToolManagement.EnvironmentManager import environmentManager


from PIL import Image
import multiprocessing

class ThumbnailGenerator:
	
	instance = None
	finished = Signal(object)
	queue = queue.Queue()

	def __init__(self) -> None:
		self.imageToThumbnail: dict[str, str] = {}
		self.environment = environmentManager.launch('ThumbnailGenerator', condaEnvironment=False)
		if self.environment.process is not None:
			inthread(self.logOutput, self.environment.process)
		inthread(self._generateThumbnailsThread)

	@classmethod
	def logOutput(cls, process):
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
		return Path(self.imageToThumbnail[imagePath]) if imagePath in self.imageToThumbnail else None

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
				self.imageToThumbnail[result[0]] = result[1]
		with open(self.getThumbnailsPath() / 'imageToThumbnail.json', 'w') as f:
			json.dump(self.imageToThumbnail, f)
		print(f'generated {len(results)} thumbnails')
		self.finished.send(results)
		return
	
	def generateThumbnails(self, nodeName, dataFrame: pandas.DataFrame):
		thumbnailsPath = self.getNodeThumbnailsPath(nodeName)
		thumbnailsPath.mkdir(exist_ok=True, parents=True)
		images = []
		
		for ri, row in dataFrame.iterrows():
			for ci, item in enumerate(row):
				if not (isinstance(item, Path) or isinstance(item, str)): continue
				if item in self.imageToThumbnail: continue
				if not Path(item).is_file(): continue
				thumbnailPath = self.generateThumbnailPath(nodeName, item, ri, ci, thumbnailsPath)
				images.append((str(item), str(thumbnailPath)))
		if len(images)>0:

			# thread = threading.Thread(target=self._generateThumbnails, args=images)
			# thread.daemon = True
			# thread.start()
			
			# inthread(self._generateThumbnails, images)
			self.queue.put(images)

			# self._generateThumbnails(images)
		return 

	@classmethod
	def get(cls):
		if cls.instance is None:
			cls.instance = ThumbnailGenerator()
		return cls.instance