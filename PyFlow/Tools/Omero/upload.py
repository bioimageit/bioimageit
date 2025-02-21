import pandas
from munch import DefaultMunch
from pathlib import Path
from PyFlow.Core.OmeroService import DoesNotExistException
from .base import OmeroBase

class OmeroUpload(OmeroBase):

    name = "omero_upload"
    description = "Upload data to an Omero database."
    inputs = [
            dict(
            names = ['--image'],
            help = 'Image to upload',
            type = Path,
            required = True,
        ),
        dict(
            names = ['--metadata_columns'],
            help = 'Metadata columns (for example ["column 1", "column 2"])',
            type = str,
            default = None,
        ),
        dict(
            names = ['--dataset_id'],
            help = 'Dataset ID (ignored if negative)',
            type = int,
            default = None,
        ),
        dict(
            names = ['--dataset_name'],
            help = 'Dataset name',
            type = str,
            default = None,
        ),
        dict(
            names = ['--project_id'],
            help = 'Project ID (optional, ignored if negative)',
            type = int,
            default = None,
        ),
        dict(
            names = ['--project_name'],
            help = 'Project name (optional)',
            type = str,
            default = None,
        ),
    ]
    outputs = [
    ]
    
    def processData(self, args):
        # Get or create dataset
        # Projects are not created by BioImageIT
        # See self.description()
        
        try:
            project = self.omero.getProject(name=args.project_name, uid=args.project_id)
        except DoesNotExistException:
            project = None
        
        try:
            dataset = self.getDataset(args, project)
        except DoesNotExistException:
            if project is None or args.dataset_name is None:
                raise DoesNotExistException(f'Neither the dataset nor the project were found (the project must exist to create the dataset).')
            else:
                dataset = self.omero.createDataset(DefaultMunch.fromDict(dict(md_uri=project.id)), args.dataset_name)

        metaDataColumns = [mdc for mdc in args.metadata_columns.split(',') if len(mdc)>0]
        for metaDataName in metaDataColumns:
            if metaDataName not in args.idf_row.index:
                raise Exception(f'The column "{metaDataName}" does not exist in the input dataframe. The columns are: {args.idf_row.index}.')

        if self.omero.imageInDataset(dataset, args.image):
            raise Exception(f'Images {args.image} already exist on dataset {dataset.getId()}.')
        
        self.omero.importData(dataset, args.image, 'imagetiff', key_value_pairs={md:args.idf_row[md] for md in metaDataColumns if md in args.idf_row}, check_image_exists=False)