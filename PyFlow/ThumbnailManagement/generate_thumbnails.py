import numpy as np
from PIL import Image
import multiprocessing
import logging

if __name__ == '__main__':
	multiprocessing.set_start_method('spawn')

logging.basicConfig(
    level=logging.INFO,
    handlers=[
        logging.FileHandler('thumbnails.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__file__)

def thumbnail(inputPath, outputPath, size=(128,128)): 
	try:
		# Load just once, then successively scale down
		im = Image.open(inputPath)
		if im.mode[0] in ['I', 'F']:
			data = np.asarray(im)
			dmax, dmin = data.max(), data.min()
			data = 255.0 * ( data - dmin ) / (dmax - dmin) if abs(dmax - dmin) > 0 else data
			im = Image.fromarray(data.astype(np.uint8))
		im.thumbnail(size)
		im.save(outputPath)
		return (inputPath, outputPath)
	except Exception as e:
		return None

def generateThumbnails(images):
	pool = multiprocessing.Pool(8)
	logger.info(f'generate {len(images)} thumbnails')
	results = pool.starmap(thumbnail, images)
	return [r for r in results if r is not None]