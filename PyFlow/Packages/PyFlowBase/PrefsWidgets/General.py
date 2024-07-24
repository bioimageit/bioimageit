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


import os
import keyring

from qtpy import QtCore
from qtpy.QtWidgets import *

from PyFlow.UI.EditorHistory import EditorHistory
from PyFlow.UI.Widgets.PropertiesFramework import CollapsibleFormWidget
from PyFlow.UI.Widgets.PreferencesWindow import CategoryWidgetBase


class GeneralPreferences(CategoryWidgetBase):
    """docstring for GeneralPreferences."""

    def __init__(self, parent=None):
        super(GeneralPreferences, self).__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(1, 1, 1, 1)
        self.layout.setSpacing(2)

        commonCategory = CollapsibleFormWidget(headName="Common")
        defaultTempFolder = os.path.join(os.path.expanduser("~"), "PyFlowTemp")
        defaultTempFolder = os.path.normpath(defaultTempFolder)
        self.tempFilesDir = QLineEdit(defaultTempFolder)
        commonCategory.addWidget("TempFilesDir", self.tempFilesDir)
        self.additionalPackagePaths = QLineEdit("")
        commonCategory.addWidget(
            "Additional package locations", self.additionalPackagePaths
        )
        self.layout.addWidget(commonCategory)

        self.lePythonEditor = QLineEdit("sublime_text.exe @FILE")
        commonCategory.addWidget("External text editor", self.lePythonEditor)

        self.leImageViewer = QLineEdit("")
        # commonCategory.addWidget("External image viewer", self.leImageViewer)
        commonCategory.addWidget("Napari environment", self.leImageViewer)

        self.historyDepth = QSpinBox()
        self.historyDepth.setRange(10, 100)

        def setHistoryCapacity():
            EditorHistory().capacity = self.historyDepth.value()

        self.historyDepth.editingFinished.connect(setHistoryCapacity)
        commonCategory.addWidget("History depth", self.historyDepth)

        self.redirectOutput = QCheckBox(self)
        commonCategory.addWidget("Redirect output", self.redirectOutput)

        omeroCategory = CollapsibleFormWidget(headName="Omero")
        self.layout.addWidget(omeroCategory)
        
        self.host = QLineEdit("demo.openmicroscopy.org")
        omeroCategory.addWidget("Host", self.host)

        self.port = QSpinBox()
        self.port.setRange(0, 100000)
        self.port.setValue(4064)
        omeroCategory.addWidget("Port", self.port)

        self.username = QLineEdit("")
        omeroCategory.addWidget("Username", self.username)

        self.password = QLineEdit("")
        self.password.setEchoMode(QLineEdit.Password)
        omeroCategory.addWidget("Password", self.password)

        spacerItem = QSpacerItem(10, 10, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.layout.addItem(spacerItem)

    def initDefaults(self, settings):
        settings.setValue("EditorCmd", "sublime_text.exe @FILE")
        settings.setValue("TempFilesDir", os.path.expanduser("~/PyFlowTemp"))
        settings.setValue("HistoryDepth", 50)
        settings.setValue("RedirectOutput", True)

        settings.setValue("OmeroHost", "demo.openmicroscopy.org")
        settings.setValue("OmeroPort", 4064)
        settings.setValue("OmeroUsername", "")
        settings.setValue("OmeroPassword", "")

    def serialize(self, settings):
        settings.setValue("EditorCmd", self.lePythonEditor.text())
        settings.setValue("ImageViewerCmd", self.leImageViewer.text())
        settings.setValue("TempFilesDir", self.tempFilesDir.text())
        settings.setValue("ExtraPackageDirs", self.additionalPackagePaths.text())
        settings.setValue("HistoryDepth", self.historyDepth.value())
        settings.setValue(
            "RedirectOutput", self.redirectOutput.checkState() == QtCore.Qt.Checked
        )

        settings.setValue("OmeroHost", self.host.text())
        settings.setValue("OmeroPort", self.port.value())
        settings.setValue("OmeroUsername", self.username.text())
        keyring.set_password("bioif-omero", self.username.text(), self.password.text())


    def onShow(self, settings):
        self.lePythonEditor.setText(settings.value("EditorCmd"))
        self.leImageViewer.setText(settings.value("ImageViewerCmd"))
        username = settings.value("OmeroUsername")
        self.username.setText(username)
        self.password.setText(keyring.get_password("bioif-omero", username))
        path = settings.value("TempFilesDir")
        path = os.path.normpath(path)
        self.tempFilesDir.setText(path)
        self.additionalPackagePaths.setText(settings.value("ExtraPackageDirs"))

        try:
            self.historyDepth.setValue(int(settings.value("HistoryDepth")))
        except:
            pass

        try:
            self.redirectOutput.setChecked(settings.value("RedirectOutput") == "true")
        except:
            pass
