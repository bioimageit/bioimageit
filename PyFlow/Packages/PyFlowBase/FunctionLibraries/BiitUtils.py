from pathlib import Path
# from bioimageit_formats import FormatsAccess
from PyFlow.Core.GraphManager import GraphManagerSingleton

ioTypeToPinType = dict(
    string='StringPin',
    float='FloatPin',
    integer='IntPin',
    boolean='BoolPin',
    select='StringPin'
)

def getPinTypeFromIoType(ioType):
    return ioTypeToPinType[ioType] if ioType in ioTypeToPinType else 'StringPin'

def isIoPath(inputType):
    return inputType not in ioTypeToPinType.keys()

filePathTypes = ['imagetiff', 'path']

fileTypeToExtensions = dict(imagetiff='tif', trackmatemodel='xml', imagepng='png', imagejpg='jpg', movietxt='txt', numbercsv='csv', arraycsv='csv', tablecsv='csv')

def getOutputDataFolderPath(nodeName):
    graphManager = GraphManagerSingleton().get()
    return Path(graphManager.workflowPath).resolve() / 'Data' / nodeName

def getOutputMetadataFolderPath(nodeName):
    graphManager = GraphManagerSingleton().get()
    return Path(graphManager.workflowPath).resolve() / 'Metadata' / nodeName
