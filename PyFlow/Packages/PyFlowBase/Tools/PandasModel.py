from PySide6.QtCore import QPersistentModelIndex
import pandas as pd
from pathlib import Path
from qtpy.QtGui import QPixmap, QIcon
from qtpy.QtCore import QAbstractTableModel, Qt, QModelIndex, QSize
from qtpy import QtCore, QtWidgets
from PyFlow.Core.GraphManager import GraphManagerSingleton
from PyFlow.Packages.PyFlowBase.Tools.ThumbnailGenerator import thumbnailGenerator

# class ImageDelegate(QtWidgets.QStyledItemDelegate):
#     def __init__(self, parent: QtCore.QObject | None = ...) -> None:
#         super().__init__(parent)
#     def initStyleOption(self, option, index):
#         super(ImageDelegate, self).initStyleOption(option, index)
#         path = thumbnailGenerator.getThumbnailPath(index.data())
#         if path is not None and path.exists() and path.is_file() and path.suffix in ['.png', '.jpg', '.jpeg', '.bmp', '.dib', '.gif', '.tiff', '.tif']:
#             self.pixmap = QPixmap(path)
#             if not self.pixmap.isNull():
#                 option.features |= QtWidgets.QStyleOptionViewItem.HasDecoration
#                 option.icon = QIcon(self.pixmap)
#                 # option.decorationSize = pixmap.size() / pixmap.devicePixelRatio()
#                 option.decorationSize = self.pixmap.size()
#                 self.option = option
        
#     def displayText(self, value, locale):
#         return str(value)

class PandasModel(QAbstractTableModel):
    """A model to interface a Qt view with pandas dataframe """
    
    # RowsThreshold = 100

    def __init__(self, dataframe: pd.DataFrame=None, parent=None):
        QAbstractTableModel.__init__(self, parent)
        self._rowCount = 0
        self.pixmaps = {}
        self.setDataFrame(dataframe)
        self.graphManager = GraphManagerSingleton().get()
    
    def setDataFrame(self, dataFrame: pd.DataFrame = None):
        self._dataframe = dataFrame if dataFrame is not None else pd.DataFrame()
        self.beginResetModel()
        self._rowCount = 0
        self.endResetModel()
        return
    
    def canFetchMore(self, parent=QModelIndex()) -> bool:
        # return False if parent.isValid() or len(self._dataframe) < PandasModel.RowsThreshold else self._rowCount < len(self._dataframe)
        return False if parent.isValid() else self._rowCount < len(self._dataframe)

    def fetchMore(self, parent: QModelIndex | QPersistentModelIndex) -> None:
        if parent.isValid(): return

        remainder = len(self._dataframe) - self._rowCount
        itemsToFetch = min(100, remainder)

        if itemsToFetch <= 0: return

        self.beginInsertRows(QModelIndex(), self._rowCount, self._rowCount + itemsToFetch - 1)
        self._rowCount += itemsToFetch
        self.endInsertRows()
    
    def rowCount(self, parent=QModelIndex()) -> int:
        """ Override method from QAbstractTableModel

        Return row count of the pandas DataFrame
        """
        if parent == QModelIndex():
            return self._rowCount
        return 0

    def columnCount(self, parent=QModelIndex()) -> int:
        """Override method from QAbstractTableModel

        Return column count of the pandas DataFrame
        """
        if parent == QModelIndex():
            return len(self._dataframe.columns)
        return 0
    
    def data(self, index: QModelIndex, role=Qt.ItemDataRole):
        """Override method from QAbstractTableModel

        Return data cell from the pandas DataFrame
        """
        if not index.isValid():
            return None
        
        value = self._dataframe.iloc[index.row(), index.column()]
        
        # if role == QtCore.Qt.DisplayRole:
        #     return value
        
        path = thumbnailGenerator.getThumbnailPath(value)
        
        if path is not None and path.exists() and path.is_file() and path.suffix in ['.png', '.jpg', '.jpeg', '.bmp', '.dib', '.gif', '.tiff', '.tif']:
    
            pixmap = self.pixmaps[str(path)] if str(path) in self.pixmaps else QPixmap(path)
            self.pixmaps[str(path)] = pixmap
            if role == Qt.DecorationRole:
                return pixmap

            if role == Qt.SizeHintRole:
                return pixmap.size()
            
            if role == Qt.DisplayRole:
                return ''
            
            if role == Qt.UserRole:
                return path

        elif role == Qt.DisplayRole:
            if ( isinstance(value, Path) or isinstance(value, str) ) and Path(self.graphManager.workflowPath) in Path(value).parents:
                return Path(value).name
            return str(value)

        if role == Qt.TextAlignmentRole:
            return Qt.AlignRight

        return None

    def headerData(
        self, section: int, orientation: Qt.Orientation, role: Qt.ItemDataRole
    ):
        """Override method from QAbstractTableModel

        Return dataframe index as vertical header data and columns as horizontal header data.
        """
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return str(self._dataframe.columns[section]) if len(self._dataframe.columns)>0 else None

            if orientation == Qt.Vertical:
                return str(self._dataframe.index[section]) if len(self._dataframe)>0 else None

        return None