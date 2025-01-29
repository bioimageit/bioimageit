from pathlib import Path
import re
import pandas
from munch import DefaultMunch

from PyFlow.Core import FunctionLibraryBase
from PyFlow.Core.Common import StructureType, PinOptions
from PyFlow.Core import NodeBase
from PyFlow.Core.NodeBase import NodePinsSuggestionsHelper
from PyFlow.Packages.PyFlowBase.FunctionLibraries.BiitArrayNode import BiitArrayNodeBase
from PyFlow.Core.EvaluationEngine import EvaluationEngine
from PyFlow.ThumbnailManagement.ThumbnailGenerator import ThumbnailGenerator
from PyFlow.Packages.PyFlowBase.Nodes import FLOW_CONTROL_COLOR
from blinker import Signal

class PandasLib(FunctionLibraryBase):
    """doc string for PandasLib"""
    classes = {}

class PandasNodeBase(BiitArrayNodeBase):

    def __init__(self, name, pinStructureIn=StructureType.Single):
        super(PandasNodeBase, self).__init__(name, pinStructureIn)

    def setOutputColumns(self, tool, data):
        return
    
    @staticmethod
    def category():
        return "DataFrames"
    
class ListFiles(PandasNodeBase):
    
    tool = DefaultMunch.fromDict(dict(info=dict(fullname=lambda: 'list_files', inputs=[
            dict(name='folderPath', description='Folder path', type='path', auto=False),
            dict(name='filter', description='Filter', default_value='*', type='str'),
        ], outputs=[
            dict(name='columnName', description='Column name', type='str', default_value='path'),
        ])))
    
    def __init__(self, name):
        super(ListFiles, self).__init__(name)
        # self.inArray.pinHidden = True

        # self.dataFrameChanged = Signal(str)
        # self.pathPin = self.createInputPin("Folder path", "StringPin", defaultValue=Path.home())
        # self.pathPin.setInputWidgetVariant("FolderPathWidget")
        # self.pathPin.dataBeenSet.connect(self.pathBeenSet)
        
        # self.filterPin = self.createInputPin("Filter", "StringPin", '*')
        # self.filterPin.pinHidden = True
        # self.filterPin.dataBeenSet.connect(self.columnBeenSet)

        # self.columnNamePin = self.createInputPin("Column name", "StringPin", "path")
        # self.columnNamePin.pinHidden = True
        # self.columnNamePin.dataBeenSet.connect(self.columnBeenSet)

    @staticmethod
    def description():
        return """Read the files of a folder and create a pandas frames."""

    @staticmethod
    def category():
        return "Data"

    # def pathBeenSet(self, pin=None):
    #     path = self.pathPin.currentData()
    #     if self.columnNamePin.currentData() == 'path':
    #         self.columnNamePin.setData(Path(path).name)
    #     self.setExecuted(False)
    #     self.dataFrameChanged.send(path)

    # def columnBeenSet(self, pin=None):
    #     path = self.pathPin.currentData()
    #     self.setExecuted(False)
    #     self.dataFrameChanged.send(path)

    def compute(self, *args, **kwargs):
        data = self.updateDataFrameIfDirty()
        if not isinstance(data, pandas.DataFrame) or len(data)==0:
            return
        allFiles = []
        for index, row in data.iterrows():
            folderPath = self.getParameter('folderPath', row)
            if folderPath is None: continue
            path = Path(folderPath)
            if path.exists():
                filter = self.getParameter('filter', row)
                try:
                    files = sorted(list(path.glob(filter))) if filter is not None and len(filter)>0 else sorted(list(path.iterdir()))
                except ValueError as e:
                    print(e)
                    files = sorted(list(path.iterdir()))
                allFiles += [f for f in files if f.name != '.DS_Store']
        # dataFrame = pandas.DataFrame(data={self.getColumnName(self.parameters['outputs']['columnName']['value']):allFiles})
        dataFrame = pandas.DataFrame(data={self.parameters['outputs']['columnName']['value']:allFiles})
        ThumbnailGenerator.get().generateThumbnails(self.name, dataFrame)
        self.dirty = False
        self.setOutputAndClean(dataFrame)
        return dataFrame

class MergeDataFrames(PandasNodeBase):

    tool = DefaultMunch.fromDict(dict(info=dict(fullname=lambda: 'merge_data_frames', inputs=[
            dict(name='how', description='How', type='str', static=True),
            dict(name='on', description='On', type='str', static=True),
            dict(name='left_on', description='Left on', type='str', static=True),
            dict(name='right_on', description='Right on', type='str', static=True),
            dict(name='left_index', description='Left index', type='bool', static=True),
            dict(name='right_index', description='Right index', type='bool', static=True),
            dict(name='sort', description='Sort', type='bool', static=True),
            dict(name='left_suffix', description='Left suffix', type='str', static=True, default_value='_x'),
            dict(name='right_suffix', description='Right suffix', type='str', static=True, default_value='_y'),
        ], outputs=[])))
    
    def __init__(self, name):
        super(MergeDataFrames, self).__init__(name, pinStructureIn=StructureType.Multi)
        self.inArray.enableOptions(PinOptions.AllowMultipleConnections)
        
    @classmethod
    def title(cls):
        return "Merge DataFrames"

    @staticmethod
    def description():
        return """Merge multiple pandas frames."""
    # pandas.merge(left, right, how='inner', on=None, left_on=None, right_on=None, left_index=False, right_index=False, sort=False, suffixes=('_x', '_y'), copy=None, indicator=False, validate=None)

    def compute(self, *args, **kwargs):
        if not self.dirty: return
        # data = self.inArray.currentData()
        ySortedPins = sorted( self.inArray.affected_by, key=lambda pin: pin.owningNode().y )
        data = [p.getCachedDataOrEvaluatdData() for p in ySortedPins]
        data = [d for d in data if d is not None]
        if len(data)==0: return
        assert(all([isinstance(d, pandas.DataFrame) for d in data]))
        df = data[0]
        mergeArgs = { input.name: self.getParameter(input.name, None) for input in self.__class__.tool.info.inputs if self.getParameter(input.name, None) is not None and self.getParameter(input.name, None) != '' and '_suffix' not in input.name}
        mergeArgs['suffixes'] = (self.getParameter('left_suffix', None), self.getParameter('right_suffix', None))
        for i in range(len(data)-1):
            df = df.merge(data[i+1], **mergeArgs)

        self.setOutputAndClean(df)
        self.dirty = False

class ConcatDataFrames(PandasNodeBase):

    tool = DefaultMunch.fromDict(dict(info=dict(fullname=lambda: 'concat_dataframes', inputs=[], outputs=[])))
    
    def __init__(self, name):
        super(ConcatDataFrames, self).__init__(name, pinStructureIn=StructureType.Multi)
        self.inArray.enableOptions(PinOptions.AllowMultipleConnections)

    @classmethod
    def title(cls):
        return "Concat DataFrames"
     
    @staticmethod
    def description():
        return """Concat multiple pandas frames."""

    def compute(self, *args, **kwargs):
        if not self.dirty: return
        ySortedPins = sorted( self.inArray.affected_by, key=lambda pin: pin.owningNode().y )
        data = [p.getCachedDataOrEvaluatdData() for p in ySortedPins]
        data = [d for d in data if d is not None]
        if len(data)==0: return
        assert(all([isinstance(d, pandas.DataFrame) for d in data]))
        result = pandas.concat(data, axis=1)
        # Remove duplicated columns
        result = result.loc[:,~result.columns.duplicated()].copy()
        self.setOutputAndClean(result)
        self.dirty = False

class ColumnRegex(PandasNodeBase):

    tool = DefaultMunch.fromDict(dict(info=dict(fullname=lambda: 'column_regex', inputs=[
            dict(name='columnName', description='Column name', type='str', static=True),
            dict(name='regex', description='Regex', default_value=r"(?P<column1>\w+)_(?P<column2>\w+)", type='str', static=True),
        ], outputs=[])))
    
    def __init__(self, name):
        super(ColumnRegex, self).__init__(name, pinStructureIn=StructureType.Multi)

    @staticmethod
    def description():
        return """Create columns from a regex."""

    def compute(self, *args, **kwargs):
        if not self.dirty: return
        data = self.getCachedDataFrame()
        if data is None: return
        df: pandas.DataFrame = data.copy()
        regex = self.getParameter('regex', None)
        columnName = self.getParameter('columnName', None)
        columnIndex = None
        try:
            columnIndex = int(columnName)
        except ValueError as e:
            pass
        for index, row in df.iterrows():
            m = re.search(regex, str(row[columnName] if columnIndex is None else row.iloc[columnIndex]))
            if m is None: continue
            for key, value in m.groupdict().items():
                df.at[index, key] = value
        self.setOutputAndClean(df)
        self.dirty = False

PandasLib.classes['ListFiles'] = ListFiles
PandasLib.classes['MergeDataFrames'] = MergeDataFrames
PandasLib.classes['ConcatDataFrames'] = ConcatDataFrames
PandasLib.classes['ColumnRegex'] = ColumnRegex