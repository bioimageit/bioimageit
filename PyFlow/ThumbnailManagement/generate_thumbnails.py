import multiprocessing
import logging
from pathlib import Path
import numpy as np
from PIL import Image
import h5py


if __name__ == '__main__':
	multiprocessing.set_start_method('spawn')

logging.basicConfig(
    level=logging.INFO,
    handlers=[
        logging.FileHandler('thumbnails.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__file__)

def openH5array(filename, datasetName='dataset'):
	with h5py.File(filename, 'r') as h5file:
		return h5file[datasetName][:]

def normalizeAndConvert(data):
	dmax, dmin = data.max(), data.min()
	data = 255.0 * ( data - dmin ) / (dmax - dmin) if abs(dmax - dmin) > 0 else data
	return Image.fromarray(data.astype(np.uint8))

def thumbnail(inputPath, outputPath, size=(128,128)): 
	try:
		if Path(inputPath).suffix == '.h5':
			data = openH5array(inputPath)
			im = normalizeAndConvert(data[data.shape[0]//2,:,:])
		else:
			im = Image.open(inputPath)
			if im.mode[0] in ['I', 'F', 'L']:
				im = normalizeAndConvert(np.asarray(im))
		im.thumbnail(size)
		im.save(outputPath)
		return (inputPath, outputPath)
	except Exception as e:
		return None

def generateThumbnails(taskData):
	pool = multiprocessing.Pool(8)
	logger.info(f'generate {len(taskData["images"])} thumbnails')
	results = pool.starmap(thumbnail, taskData['images'])
	return dict(paths=[r for r in results if r is not None], workflowPath=taskData['workflowPath'])