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

def isIoPath(io):
    return io.type not in ioTypeToPinType.keys()

filePathTypes = ['imagetiff', 'path']

fileTypeToExtensions = dict(imagetiff='tif', trackmatemodel='xml', imagepng='png', imagejpg='jpg', movietxt='txt', numbercsv='csv', arraycsv='csv', tablecsv='csv')

def getOutputFolderPath(nodeName):
    graphManager = GraphManagerSingleton().get()
    return Path(graphManager.workflowPath).resolve() / nodeName

def getOutputFilePath(info, nodeName, index=None):
    indexPrefix = f'_{index}' if index is not None else ''
    # return getOutputFolderPath(nodeName) / f'{info.name}{indexPrefix}.{FormatsAccess.instance().get(info.type).extension}'
    return getOutputFolderPath(nodeName) / f'{info.name}{indexPrefix}.{fileTypeToExtensions[info.type]}'
