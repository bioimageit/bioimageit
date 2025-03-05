import pandas
from omero.gateway import BlitzGateway
from .base import OmeroBase
from PIL import Image
import numpy as np

class Tool(OmeroBase):

    name = "Omero Download"
    description = "Download files from Omero."
    categories = ['Omero']
    inputs = [
            dict(
            name = 'dataset_id',
            help = 'Dataset ID',
            type = 'int',
            default = None,
        ),
    ]
    outputs = [
        dict(
            name = 'out',
            help = 'Output data',
            type = 'Path',
            default = '(path)',
        ),
    ]
    
    def processDataFrame(self, dataFrame, argsList):

        host, port, username, password = self.getSettings()
        records = []
        with BlitzGateway(username, password, host=host, port=port, secure=True) as connection:
            for args in argsList:
                dataset = connection.getObject('Dataset', args.dataset_id)
                if dataset is None:
                    raise Exception(f'Error: Dataset {args.dataset_id} does not exist.')
                
                images = list(dataset.listChildren())
                for image in images:
                    image = connection.getObject('Image', image.id)
                    records.append(dict(name=image.getName(), author=image.getAuthor(), description=image.getDescription(), dataset=dataset.name, dataset_id=dataset.getId(), project_id=image.getProject().getId(), image_id=image.getId(), path=image.getName()))
        self.outputMessage = ''
        return pandas.DataFrame.from_records(records)

    def downloadImageData(self, img, c=0, t=0):
        """Get one channel and one time point of a data
        
        Parameters
        ----------
        img: omero.gateway.ImageWrapper
            Omero image wrapper
        c: int
            Channel index
        t: int
            Time point index    

        """
        size_z = img.getSizeZ()
        # get all planes we need in a single generator
        zct_list = [(z, c, t) for z in range(size_z)]
        pixels = img.getPrimaryPixels()
        plane_gen = pixels.getPlanes(zct_list)

        if size_z == 1:
            return np.array(next(plane_gen))
        else:
            z_stack = []
            for z in range(size_z):
                # print("plane c:%s, t:%s, z:%s" % (c, t, z))
                z_stack.append(next(plane_gen))
            return np.array(z_stack)

    def downloadImage(self, destination_file_path, omero_image):
        if destination_file_path is None:
            raise Exception('Output file must be valid')
        image_data = self.downloadImageData(omero_image)
        Image.fromarray(image_data).save(destination_file_path)
        return omero_image
    
    def processAllData(self, argsList):
        host, port, username, password = self.getSettings()
        with BlitzGateway(username, password, host=host, port=port, secure=True) as connection:
            for args in argsList:
                dataset = connection.getObject('Dataset', args.dataset_id)
                if dataset is None:
                    raise Exception(f'Error: Dataset {args.dataset_id} does not exist.')
                images = list(dataset.listChildren())
                for image in images:
                    omero_image = image = connection.getObject('Image', image.id)
                    self.downloadImage(args.out, omero_image)