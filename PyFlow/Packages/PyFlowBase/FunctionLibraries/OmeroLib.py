import pandas
from munch import DefaultMunch
from PyFlow.Core import FunctionLibraryBase

from PyFlow.Core.OmeroService import OmeroService, DoesNotExistException
from PyFlow.Packages.PyFlowBase.FunctionLibraries.BiitArrayNode import BiitArrayNodeBase

class OmeroLib(FunctionLibraryBase):
    """doc string for OmeroLib"""
    classes = {}

class OmeroBase(BiitArrayNodeBase):

    omero: OmeroService = OmeroService()

    def __init__(self, name):
        super(OmeroBase, self).__init__(name)
        self.executed = None
        self.lib = 'BiitLib'
    
    @staticmethod
    def category():
        return "Data|Omero"

    def postCreate(self, jsonTemplate=None):
        super().postCreate(jsonTemplate)
        self.setExecuted(False)
    
    def dataChanged(self, datasetName:str):
        self.dirty = True
        self.setExecuted(False)

    # setOutputColumns does not apply for Omero nodes
    def setOutputColumns(self, tool, data):
        return

    def getDatasets(self, project=None):
        data = self.getDataFrame()
        dataRows = data.iterrows() if data is not None else [(0, None)]
        datasets = []
        for index, row in dataRows:
            datasetId = self.getParameter('dataset_id', row)
            datasetName = self.getParameter('dataset_name', row)
            if datasetId is None and datasetName is None:
                raise Exception('Dataset name or id must be set.')
            dataset = self.omero.getDataset(name=datasetName, uid=datasetId, project=project)
            if dataset is not None:
                datasets.append(dataset)
        return datasets
    
class OmeroDownload(OmeroBase):

    tool = DefaultMunch.fromDict(dict(info=dict(fullname=lambda: 'omero_download', inputs=[
            dict(name='dataset_id', description='Dataset ID (ignored if negative)', type='integer'),
            dict(name='dataset_name', description='Dataset name', type='string'),
        ], outputs=[
            dict(name='data files', description='Output data', type='path'),
        ])))
    
    def __init__(self, name):
        super(OmeroDownload, self).__init__(name)

    @staticmethod
    def description():
        return """Download files from Omero: either enter the dataset name or id to download. Negative ids will be ignored."""

    def compute(self, *args, **kwargs):
        data = super().compute(*args, **kwargs)
        if data is None: return
        try:
            datasets = self.getDatasets()
        except DoesNotExistException as e: # Pass if dataset does not exist
            self.dirty = False
            self.setOutputAndClean(None)
            self.outputMessage = str(e)
            return
        if datasets is None or len(datasets)==0: return
        # dataset = omero.get_dataset(datasetName)
        records = []
        for dataset in datasets:
            for image in dataset.listChildren():
                image = self.omero.getImage(uid=image.id)
                path = self.getOutputDataFolderPath()(self.name) / image.getName()
                records.append(dict(name=image.getName(), author=image.getAuthor(), description=image.getDescription(), dataset=dataset.name, project=image.getProject(), id=image.getId(), path=path))
        dataFrame = pandas.DataFrame.from_records(records)
        # ThumbnailGenerator.get().generateThumbnails(self.name, dataFrame)
        self.setOutputAndClean(dataFrame)
        self.dirty = False
        self.outputMessage = None

    def execute(self):
        try:
            datasets = self.getDatasets()
        except DoesNotExistException: # Pass if dataset does not exist
            self.setExecuted(True)
            return
        # dataset = omero.get_dataset(datasetId)
        outputFolder = self.getOutputDataFolderPath()(self.name)
        for dataset in datasets:
            for image in dataset.listChildren():
                omero_image = self.omero.getImage(uid=image.id)
                path = outputFolder / omero_image.getName()
                path.parent.mkdir(exist_ok=True, parents=True)
                if path.exists(): continue
                self.omero.downloadImage(path, omero_image=omero_image)
        # outputData = self.outArray.currentData()
        # outputMetadataFolder = getOutputMetadataFolderPath(self.name)
        # outputData.to_csv(outputMetadataFolder / 'output_data_frame.csv')
        # host, port, username = OmeroService().getSettings()
        # with open(outputMetadataFolder / PARAMETERS_PATH, 'w') as f:
        #     json.dump(dict(host=host,port=port,username=username, datasetName=dataset.name, datasetId=dataset.id), f)
        
        # self.setExecuted(True)
        argsList = self.getArgs()
        self.finishExecution(argsList)
        
class OmeroUpload(OmeroBase):

    tool = DefaultMunch.fromDict(dict(info=dict(fullname=lambda: 'omero_download', inputs=[
            dict(name='image', description='Image to upload', type='string'),
            dict(name='metadata_columns', description='Metadata columns (for example ["column 1", "column 2"])', type='string'),
            dict(name='dataset_id', description='Dataset ID (ignored if negative)', type='integer'),
            dict(name='dataset_name', description='Dataset name', type='string'),
            dict(name='project_id', description='Project ID (optional, ignored if negative)', type='integer'),
            dict(name='project_name', description='Project name (optional)', type='string'),
        ], outputs=[])))
    
    def __init__(self, name):
        super(OmeroUpload, self).__init__(name)
    
    @staticmethod
    def description():
        return """Update files from Omero: either enter the name or the id of the dataset to create (if it does not exist) or update (if it exists). The project name or id must be specified if there are multiple datasets with the given name, and dataset id is not providen ; or if the dataset does not exist."""
    
    def getProject(self, row):
        projectId = self.getParameter('project_id', row)
        projectName = self.getParameter('project_name', row)
        return self.omero.getProject(name=projectName, uid=projectId)
    
    def execute(self):
        # Get or create dataset
        # Projects are not created by BioImageIT
        # See self.description()
        
        data = self.getDataFrame()
        for index, row in data.iterrows():
            datasetName = self.getParameter('dataset_name', row)
            
            try:
                project = self.getProject(row)
            except DoesNotExistException:
                project = None
            
            try:
                datasets = self.getDatasets(project)
            except DoesNotExistException:
                if project is None or len(datasetName) == 0:
                    raise DoesNotExistException(f'Neither the dataset nor the project were found (the project must exist to create the dataset).')
                else:
                    datasets = [self.omero.createDataset(DefaultMunch.fromDict(dict(md_uri=project.id)), datasetName)]

            for dataset in datasets:
                data: pandas.DataFrame = self.getDataFrame()
                if data is None: return
                # columnName = self.columnName if self.columnName is not None else data.columns[-1]
                metaDataColumns = self.getParameter('metadata_columns', row)
                metaDataColumns = [mdc for mdc in metaDataColumns.split(',') if len(mdc)>0]
                for metaDataName in metaDataColumns:
                    if metaDataName not in data.columns:
                        raise Exception(f'The column "{metaDataName}" does not exist in the input dataframe. The columns are: {data.columns}.')
                existingImages = []
                for index, row in data.iterrows():
                    # imagePath = row[columnName]
                    imagePath = self.getParameter('image', row)
                    if self.omero.imageInDataset(dataset, imagePath):
                        existingImages.append(str(imagePath))
                        continue
                    self.omero.importData(dataset, imagePath, 'imagetiff', key_value_pairs={md:row[md] for md in metaDataColumns if md in row}, check_image_exists=False)
                if len(existingImages) > 0:
                    raise Exception(f'Images {existingImages} already exist on dataset {dataset.getId()}.')
                
        argsList = self.getArgs()
        self.finishExecution(argsList)
    
OmeroLib.classes['OmeroDownload'] = OmeroDownload
OmeroLib.classes['OmeroUpload'] = OmeroUpload