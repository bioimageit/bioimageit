from pathlib import Path
import re
import pandas

from PyFlow.Core import FunctionLibraryBase
from PyFlow.Core.Common import StructureType, PinOptions
from PyFlow.Core import NodeBase
from PyFlow.Core.NodeBase import NodePinsSuggestionsHelper
from PyFlow.Packages.PyFlowBase.FunctionLibraries.BiitNodeBase import BiitNodeBase
from PyFlow.Core.EvaluationEngine import EvaluationEngine
from PyFlow.Packages.PyFlowBase.Tools.ThumbnailGenerator import thumbnailGenerator
from PyFlow.Packages.PyFlowBase.Nodes import FLOW_CONTROL_COLOR
from blinker import Signal

class PandasLib(FunctionLibraryBase):
    """doc string for PandasLib"""
    classes = {}

class PandasNodeBase(BiitNodeBase):

    def __init__(self, name):
        super(PandasNodeBase, self).__init__(name)
        self.executed = None
        self.executedChanged = Signal(bool)
        self.dataFrameChanged = Signal(str)

        self.outArray = self.createOutputPin("Data frame", "AnyPin")
        self.outArray.disableOptions(PinOptions.ChangeTypeOnConnection)
        # self.headerColor = FLOW_CONTROL_COLOR
        self.lib = 'BiitLib'

    def setExecuted(self, executed, propagate=True):
        if self.executed == executed: return
        self.executed = executed
        self.executedChanged.send(executed)
        # Propagate to following nodes is execution was unset?
        if propagate and not executed:
            nextNodes = EvaluationEngine()._impl.getEvaluationOrderIterative(self, forward=True)
            for node in [node for node in nextNodes if node != self]:
                node.setExecuted(False, propagate=False)

    @staticmethod
    def category():
        return "DataFrames"
    
class PandasNodeInOut(PandasNodeBase):

    def __init__(self, name):
        super(PandasNodeInOut, self).__init__(name)
        self.inArray = self.createInputPin("in", "AnyPin", structure=StructureType.Multi)
        self.inArray.enableOptions(PinOptions.AllowAny)
        self.inArray.dataBeenSet.connect(self.dataBeenSet)
        
    def getPinData(self, pin):
        data = pin.currentData()
        return data if data is not None else pin.getData()
    
    def dataBeenSet(self, pin=None):
        self.dirty = True
    
    @staticmethod
    def pinTypeHints():
        helper = NodePinsSuggestionsHelper()
        helper.addInputDataType("AnyPin")
        helper.addOutputDataType("AnyPin")
        helper.addInputStruct(StructureType.Single)
        helper.addOutputStruct(StructureType.Single)
        return helper

class ListFiles(PandasNodeBase):
    
    def __init__(self, name):
        super(ListFiles, self).__init__(name)
        self.pathPin = self.createInputPin("Folder path", "StringPin", defaultValue=Path.home())
        self.pathPin.setInputWidgetVariant("FolderPathWidget")
        self.pathPin.dataBeenSet.connect(self.pathBeenSet)
        self.columnNamePin = self.createInputPin("Column name", "StringPin", "path")
        self.columnNamePin.pinHidden = True
        self.columnNamePin.dataBeenSet.connect(self.columnBeenSet)

    @staticmethod
    def description():
        return """Read the files of a folder and create a pandas frames."""

    @staticmethod
    def pinTypeHints():
        helper = NodePinsSuggestionsHelper()
        helper.addInputDataType("StringPin")
        helper.addOutputDataType("AnyPin")
        helper.addInputStruct(StructureType.Single)
        helper.addOutputStruct(StructureType.Single)
        return helper

    def pathBeenSet(self, pin=None):
        path = self.pathPin.currentData()
        if self.columnNamePin.currentData() == 'path':
            self.columnNamePin.setData(Path(path).name)
        self.dirty = True
        self.dataFrameChanged.send(path)

    def columnBeenSet(self, pin=None):
        path = self.pathPin.currentData()
        self.dirty = True
        self.dataFrameChanged.send(path)

    def compute(self, *args, **kwargs):
        if not self.dirty: return
        data = self.pathPin.currentData()
        if len(data)==0:
            return
        path = Path(data)
        if path.exists():
            dataFrame = pandas.DataFrame(data={self.columnNamePin.currentData():sorted(list(path.iterdir()))})
            thumbnailGenerator.generateThumbnails(self.name, dataFrame)
            self.setOutputAndClean(dataFrame)
            self.dirty = False

class MergeDataFrames(PandasNodeInOut):

    mergeArgumentToType = dict(
        how=('StringPin', 'inner'), 
        on=('StringPin', None), 
        left_on=('StringPin', None),
        right_on=('StringPin', None),
        left_index=('BoolPin', False),
        right_index=('BoolPin', False),
        sort=('BoolPin', False),
        left_suffix=('StringPin', '_x'),
        right_suffix=('StringPin', '_y'),
    )

    def __init__(self, name):
        super(MergeDataFrames, self).__init__(name)
        self.inArray.enableOptions(PinOptions.AllowMultipleConnections)
        
        for arg, typeDefault in self.__class__.mergeArgumentToType.items():
            pinName = f'merge{arg}Pin'
            setattr(self, pinName, self.createInputPin(arg, typeDefault[0], defaultValue=typeDefault[1], structure=StructureType.Single))
            getattr(self, pinName).pinHidden = True
            getattr(self, pinName).dataBeenSet.connect(self.dataBeenSet)
    
    @classmethod
    def title(cls):
        return "Merge DataFrames"

    @staticmethod
    def description():
        return """Merge multiple pandas frames."""
    # pandas.merge(left, right, how='inner', on=None, left_on=None, right_on=None, left_index=False, right_index=False, sort=False, suffixes=('_x', '_y'), copy=None, indicator=False, validate=None)

    @staticmethod
    def pinTypeHints():
        helper = PandasNodeInOut.pinTypeHints()
        helper.addInputStruct(StructureType.Multi)
        return helper

    def compute(self, *args, **kwargs):
        if not self.dirty: return
        # data = self.inArray.currentData()
        ySortedPins = sorted( self.inArray.affected_by, key=lambda pin: pin.owningNode().y )
        data = [self.getPinData(p) for p in ySortedPins]
        assert(all([isinstance(d, pandas.DataFrame) for d in data]))
        if len(data)==0: return
        df = data[0]
        mergeArgs = { arg: getattr(self, f'merge{arg}Pin').currentData() for arg, typeDefault in self.__class__.mergeArgumentToType.items() if getattr(self, f'merge{arg}Pin').currentData() != '' }
        mergeArgs['suffixes'] = (mergeArgs['left_suffix'], mergeArgs['right_suffix'])
        del mergeArgs['left_suffix']
        del mergeArgs['right_suffix']
        for i in range(len(data)-1):
            df = df.merge(data[i+1], **mergeArgs)

        self.setOutputAndClean(df)
        self.dirty = False

class ConcatDataFrames(PandasNodeInOut):

    def __init__(self, name):
        super(ConcatDataFrames, self).__init__(name)
        self.inArray.enableOptions(PinOptions.AllowMultipleConnections)

    @classmethod
    def title(cls):
        return "Concat DataFrames"
     
    @staticmethod
    def description():
        return """Concat multiple pandas frames."""

    @staticmethod
    def pinTypeHints():
        helper = PandasNodeInOut.pinTypeHints()
        helper.addInputStruct(StructureType.Multi)
        return helper

    def compute(self, *args, **kwargs):
        ySortedPins = sorted( self.inArray.affected_by, key=lambda pin: pin.owningNode().y )
        data = [self.getPinData(p) for p in ySortedPins]
        if len(data)==0: return
        assert(all([isinstance(d, pandas.DataFrame) for d in data]))
        result = pandas.concat(data, axis=1)
        # Remove duplicated columns
        result = result.loc[:,~result.columns.duplicated()].copy()
        self.outArray.setData(result)

class ColumnRegex(PandasNodeInOut):

    def __init__(self, name):
        super(ColumnRegex, self).__init__(name)
        self.columnName = self.createInputPin("Column name", "StringPin", "-1")
        self.columnName.dataBeenSet.connect(self.dataBeenSet)
        self.regex = self.createInputPin("Regex", "StringPin", r"(?P<column1>\w+)_(?P<column2>\w+)")
        self.regex.dataBeenSet.connect(self.dataBeenSet)
        
    @staticmethod
    def description():
        return """Create columns from a regex."""

    def compute(self, *args, **kwargs):
        if not self.dirty: return
        df: pandas.DataFrame = self.getPinData(self.inArray).copy()
        regex = self.regex.currentData()
        columnName = self.columnName.currentData()
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