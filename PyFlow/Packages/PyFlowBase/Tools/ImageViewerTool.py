## Copyright 2015-2019 Ilgar Lunin, Pedro Cabrera

## Licensed under the Apache License, Version 2.0 (the "License");
## you may not use this file except in compliance with the License.
## You may obtain a copy of the License at

##     http://www.apache.org/licenses/LICENSE-2.0

## Unless required by applicable law or agreed to in writing, software
## distributed under the License is distributed on an "AS IS" BASIS,
## WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
## See the License for the specific language governing permissions and
## limitations under the License.

from pathlib import Path
import sys
sys.path.append('napari_main')
import napari

from qtpy import QtCore

from PyFlow.UI.Tool.Tool import DockTool

class ImageViewerTool(DockTool):
    """docstring for ImageViewer tool."""

    def __init__(self):
        super(ImageViewerTool, self).__init__()
        self.content = None

    def onShow(self):
        super(ImageViewerTool, self).onShow()
        self.setMinimumSize(QtCore.QSize(200, 50))
        self.viewer = napari.Viewer(show=False)
        self.content = self.viewer.window._qt_window
        self.content.menuBar().deleteLater()
        self.content.setObjectName("ImageViewerToolContent")
        self.setWidget(self.content)

    def open(self, path):
        if isinstance(path, Path):
            self.viewer.open(path)

    def clear(self):
        self.viewer.layers.clear()
    
    @staticmethod
    def isSingleton():
        return True

    @staticmethod
    def defaultDockArea():
        return QtCore.Qt.RightDockWidgetArea

    @staticmethod
    def toolTip():
        return "Image viewer"

    @staticmethod
    def name():
        return "Image viewer"
