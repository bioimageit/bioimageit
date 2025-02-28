import pandas
from PyFlow.Core.OmeroService import DoesNotExistException
from .base import OmeroBase
    
class Tool(OmeroBase):

    name = "Omero Download"
    description = "Download files from Omero: either enter the dataset name or id to download. Negative ids will be ignored."
    categories = ['Omero']
    inputs = [
            dict(
            name = 'dataset_id',
            help = 'Dataset ID (ignored if negative)',
            type = 'int',
            default = None,
        ),
        dict(
            name = 'dataset_name',
            help = 'Dataset name',
            type = 'str',
            default = None,
        ),
    ]
    outputs = [
        dict(
            name = 'out',
            help = 'Output data',
            type = 'Path',
            default = '(path)',
            # editable = False,
        ),
    ]
    
    def processDataFrame(self, dataFrame, argsList):
        try:
            datasets = self.getDatasets(argsList)
        except DoesNotExistException as e: # Pass if dataset does not exist
            self.outputMessage = str(e)
            return
        if datasets is None or len(datasets)==0: return
        # dataset = omero.get_dataset(datasetName)
        records = []
        for dataset in datasets:
            for image in dataset.listChildren():
                image = self.omero.getImage(uid=image.id)
                records.append(dict(name=image.getName(), author=image.getAuthor(), description=image.getDescription(), dataset=dataset.name, dataset_id=dataset.getId(), project_id=image.getProject().getId(), image_id=image.getId(), path=image.getName()))
        self.outputMessage = ''
        return pandas.DataFrame.from_records(records)

    def processData(self, args):
        dataset = self.getDataset(args)
        for image in dataset.listChildren():
            omero_image = self.omero.getImage(uid=image.id)
            self.omero.downloadImage(args.out, omero_image=omero_image)