import json
import pandas
from munch import DefaultMunch
# from skimage.io import imsave

from PyFlow.Core import FunctionLibraryBase
from PyFlow.Core.Common import StructureType, PinOptions
from PyFlow.Core.NodeBase import NodePinsSuggestionsHelper

from PyFlow.Core.OmeroService import OmeroService, DoesNotExistException
from PyFlow.Packages.PyFlowBase.FunctionLibraries.BiitNodeBase import BiitNodeBase
from PyFlow.Packages.PyFlowBase.FunctionLibraries.BiitUtils import getOutputFolderPath
from PyFlow.Packages.PyFlowBase.Tools.ThumbnailGenerator import thumbnailGenerator

class OmeroLib(FunctionLibraryBase):
    """doc string for OmeroLib"""
    classes = {}

class OmeroBase(BiitNodeBase):

    omero: OmeroService = OmeroService()

    def __init__(self, name, createPins=True):
        super(OmeroBase, self).__init__(name)
        self.executed = None
        self.lib = 'BiitLib'
        if createPins:
            self.createDatasetPins()
    
    def createDatasetPins(self):
        self.datasetIdPin = self.createInputPin("Dataset ID (ignored if negative)", "IntPin", -1)
        self.datasetIdPin.pinHidden = True

        self.datasetNamePin = self.createInputPin("Dataset name", "StringPin", "")
        self.datasetNamePin.pinHidden = True
        for pin in [self.datasetIdPin, self.datasetNamePin]:
            pin.pinHidden = True
            pin.dataBeenSet.connect(self.dataChanged)

    def postCreate(self, jsonTemplate=None):
        super().postCreate(jsonTemplate)
        self.setExecuted(False)
    
    def dataChanged(self, datasetName:str):
        self.dirty = True
        self.setExecuted(False)

    def getDataset(self, project=None):
        datasetId = self.datasetIdPin.currentData() if self.datasetIdPin.currentData() >= 0 else None
        datasetName = self.datasetNamePin.currentData() if len(self.datasetNamePin.currentData()) > 0 else None
        if datasetId is None and datasetName is None:
            raise Exception('Dataset name or id must be set.')
        dataset = self.omero.getDataset(name=datasetName, uid=datasetId, project=project)
        return dataset
    
class OmeroDownload(OmeroBase):

    def __init__(self, name):
        super(OmeroDownload, self).__init__(name)

        self.outArray = self.createOutputPin("DataFrame", "AnyPin")
        self.outArray.disableOptions(PinOptions.ChangeTypeOnConnection)


    
    @staticmethod
    def description():
        return """Download files from Omero: either enter the dataset name or id to download. Negative ids will be ignored."""
    
    @staticmethod
    def pinTypeHints():
        helper = NodePinsSuggestionsHelper()
        helper.addInputDataType("StringPin")
        helper.addOutputDataType("AnyPin")
        helper.addInputStruct(StructureType.Single)
        helper.addOutputStruct(StructureType.Single)
        return helper
    
    @staticmethod
    def category():
        return "Omero"
    
    def compute(self, *args, **kwargs):
        if self.dirty:
            try:
                dataset = self.getDataset()
            except DoesNotExistException as e: # Pass if dataset does not exist
                self.dirty = False
                self.setOutputAndClean(None)
                self.outputMessage = str(e)
                return
            if dataset is None: return
            # dataset = omero.get_dataset(datasetName)
            records = []
            for image in dataset.listChildren():
                image = self.omero.getImage(uid=image.id)
                path = getOutputFolderPath(self.name) / image.getName()
                records.append(dict(name=image.getName(), author=image.getAuthor(), description=image.getDescription(), dataset=dataset.name, project=image.getProject(), id=image.getId(), path=path))
            dataFrame = pandas.DataFrame.from_records(records)
            thumbnailGenerator.generateThumbnails(self.name, dataFrame)
            self.setOutputAndClean(dataFrame)
            self.dirty = False
            self.outputMessage = None

    def execute(self):
        try:
            dataset = self.getDataset()
        except DoesNotExistException: # Pass if dataset does not exist
            self.setExecuted(True)
            return
        # dataset = omero.get_dataset(datasetId)
        outputFolder = getOutputFolderPath(self.name)
        for image in dataset.listChildren():
            omero_image = self.omero.getImage(uid=image.id)
            path = outputFolder / omero_image.getName()
            path.parent.mkdir(exist_ok=True, parents=True)
            if path.exists(): continue
            self.omero.downloadImage(path, omero_image=omero_image)
        outputData = self.outArray.currentData()
        outputData.to_csv(outputFolder / 'output_data_frame.csv')
        host, port, username = OmeroService().getSettings()
        with open(outputFolder / 'parameters.json', 'w') as f:
            json.dump(dict(host=host,port=port,username=username, datasetName=dataset.name, datasetId=dataset.id), f)
        
        self.setExecuted(True)

    def clear(self):
        try:
            dataset = self.getDataset()
        except DoesNotExistException: # Pass if dataset does not exist
            return
        outputFolder = getOutputFolderPath(self.name)
        for image in dataset.listChildren():
            omero_image = self.omero.getImage(uid=image.id)
            path = outputFolder / omero_image.getName()
            if path.exists():
                path.unlink()
        super().clear()
        return
        
class OmeroUpload(OmeroBase):

    def __init__(self, name):
        super(OmeroUpload, self).__init__(name, False)

        self.inDataFrame = self.createInputPin("DataFrame", "AnyPin", None)
        self.inDataFrame.enableOptions(PinOptions.AllowAny)

        self.columnName = None
        self.metaDataColumnsPin = self.createInputPin("Metadata columns", "StringPin", "")

        self.createDatasetPins()

        self.projectIdPin = self.createInputPin("Project ID (optional, ignored if negative)", "IntPin", -1)
        self.projectNamePin = self.createInputPin("Project name (optional)", "StringPin", "")
        
        for pin in [self.metaDataColumnsPin, self.projectIdPin, self.projectNamePin]:
            pin.pinHidden = True
            pin.dataBeenSet.connect(self.dataChanged)

    def postCreate(self, jsonTemplate=None):
        super().postCreate(jsonTemplate)
        self.columnName = jsonTemplate['columnName'] if 'columnName' in jsonTemplate else None
    
    def serialize(self):
        template = super().serialize()
        template['columnName'] = self.columnName
        return template
    
    @staticmethod
    def description():
        return """Update files from Omero: either enter the name or the id of the dataset to create (if it does not exist) or update (if it exists). The project name or id must be specified if there are multiple datasets with the given name, and dataset id is not providen ; or if the dataset does not exist."""
    
    def getPreviousNodes(self):
        if not self.inDataFrame.hasConnections(): return None
        return [i.owningNode() for i in self.inDataFrame.affected_by]
    
    def getPreviousNode(self):
        if not self.inDataFrame.hasConnections(): return None
        return self.getPreviousNodes()[0]
    
    def getDataFrame(self):
        data = self.inDataFrame.currentData()
        return data if data is not None else self.inDataFrame.getData()
    
    @staticmethod
    def pinTypeHints():
        helper = NodePinsSuggestionsHelper()
        helper.addInputDataType("StringPin")
        helper.addInputStruct(StructureType.Single)
        return helper
    
    @staticmethod
    def category():
        return "Omero"
    
    def getProject(self):
        projectId = self.projectIdPin.currentData() if self.projectIdPin.currentData() >= 0 else None
        projectName = self.projectNamePin.currentData() if len(self.projectNamePin.currentData()) > 0 else None
        project = self.omero.getProject(name=projectName, uid=projectId)
        return project
    
    def execute(self):
        # Get or create dataset
        # Projects are not created by BioImageIT
        # See self.description()
        
        datasetName = self.datasetNamePin.currentData()
        
        try:
            project = self.getProject()
        except DoesNotExistException:
            project = None
        
        try:
            dataset = self.getDataset(project)
        except DoesNotExistException:
            if project is None or len(datasetName) == 0:
                raise DoesNotExistException(f'Neither the dataset nor the project were found (the project must exist to create the dataset).')
            else:
                dataset = self.omero.createDataset(DefaultMunch.fromDict(dict(md_uri=project.id)), datasetName)

        data: pandas.DataFrame = self.getDataFrame()
        if data is None: return
        columnName = self.columnName if self.columnName is not None else data.columns[-1]
        metaDataColumns = self.metaDataColumnsPin.currentData()
        metaDataColumns = [mdc for mdc in metaDataColumns.split(',') if len(mdc)>0]
        for metaDataName in metaDataColumns:
            if metaDataName not in data.columns:
                raise Exception(f'The column "{metaDataName}" does not exist in the input dataframe. The columns are: {data.columns}.')
        existingImages = []
        for index, row in data.iterrows():
            imagePath = row[columnName]
            if self.omero.imageInDataset(dataset, imagePath):
                existingImages.append(str(imagePath))
                continue
            self.omero.importData(dataset, imagePath, 'imagetiff', key_value_pairs={md:row[md] for md in metaDataColumns if md in row}, check_image_exists=False)
        if len(existingImages) > 0:
            raise Exception(f'Images {existingImages} already exist on dataset {dataset.getId()}.')
        
        self.setExecuted(True)
    
OmeroLib.classes['OmeroDownload'] = OmeroDownload
OmeroLib.classes['OmeroUpload'] = OmeroUpload