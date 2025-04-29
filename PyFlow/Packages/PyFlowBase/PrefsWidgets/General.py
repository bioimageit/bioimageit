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
import keyring
import requests
import sys
import json

from qtpy import QtCore
from qtpy.QtWidgets import *

from PyFlow import getRootPath
from PyFlow.UI.EditorHistory import EditorHistory
from PyFlow.UI.Widgets.PropertiesFramework import CollapsibleFormWidget
from PyFlow.UI.Widgets.PreferencesWindow import CategoryWidgetBase
from PyFlow.invoke_in_main import inmain, inthread

class GeneralPreferences(CategoryWidgetBase):
    """docstring for GeneralPreferences."""

    projectId = 54065 # The BioImageIT Project on Gitlab
    autoUpdateString = 'latest (auto update)'

    def __init__(self, parent=None):
        super(GeneralPreferences, self).__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(1, 1, 1, 1)
        self.layout.setSpacing(2)

        self.progressDialog = None

        commonCategory = CollapsibleFormWidget(headName="Common")
        self.layout.addWidget(commonCategory)

        # Code editor
        self.lePythonEditor = QLineEdit("sublime_text.exe @FILE")
        commonCategory.addWidget("External code editor", self.lePythonEditor)

        # Napari
        self.leImageViewer = QLineEdit("")
        commonCategory.addWidget("Napari environment", self.leImageViewer)

        self.alwaysInstallNapariDependencies = QCheckBox()
        self.alwaysInstallNapariDependencies.setTristate(True)
        self.alwaysInstallNapariDependencies.setCheckState(QtCore.Qt.PartiallyChecked)
        # self.alwaysInstallNapariDependencies.stateChanged.connect()
        commonCategory.addWidget("Always install Napari dependencies", self.alwaysInstallNapariDependencies)

        # History
        self.historyDepth = QSpinBox()
        self.historyDepth.setRange(10, 100)

        def setHistoryCapacity():
            EditorHistory().capacity = self.historyDepth.value()

        self.historyDepth.editingFinished.connect(setHistoryCapacity)
        commonCategory.addWidget("History depth", self.historyDepth)
        
        # Update
        self.versionSelector = QComboBox()
        self.versionSelector.currentTextChanged.connect(self.setVersion)
        self.updateVersionSelector()

        commonCategory.addWidget("BioImageIT version", self.versionSelector)

        # Error reports
        errorReportsCategory = CollapsibleFormWidget(headName="Error reports")
        self.layout.addWidget(errorReportsCategory)

        self.email = QLineEdit("")
        errorReportsCategory.addWidget("Email address", self.email)

        self.mailApiKey = QLineEdit("")
        errorReportsCategory.addWidget("Mail API Key", self.mailApiKey)

        self.mailApiSecret = QLineEdit("")
        self.mailApiSecret.setEchoMode(QLineEdit.Password)
        errorReportsCategory.addWidget("Mail API Secret", self.mailApiSecret)

        # OMERO

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
        settings.setValue("HistoryDepth", 50)
        
        settings.setValue("BioImageITVersion", self.autoUpdateString)

        settings.setValue("Email", "")
        settings.setValue("MailAPIKey", "")
        settings.setValue("MailAPISecret", "")

        settings.setValue("OmeroHost", "demo.openmicroscopy.org")
        settings.setValue("OmeroPort", 4064)
        settings.setValue("OmeroUsername", "")
        settings.setValue("OmeroPassword", "")

    def serialize(self, settings):
        settings.setValue("EditorCmd", self.lePythonEditor.text())
        settings.setValue("ImageViewerCmd", self.leImageViewer.text())
        settings.setValue("ImageViewerAlwaysInstallDependencies", 'Yes' if self.alwaysInstallNapariDependencies.checkState() == QtCore.Qt.CheckState.Checked else 'No' if self.alwaysInstallNapariDependencies.checkState() == QtCore.Qt.CheckState.Unchecked else 'Unknown')
        settings.setValue("HistoryDepth", self.historyDepth.value())

        settings.setValue("BioImageITVersion", self.versionSelector.currentText())

        settings.setValue("Email", self.email.text())
        settings.setValue("MailAPIKey", self.mailApiKey.text())
        keyring.set_password("bioif-mail-api-secret", self.email.text(), self.mailApiSecret.text())

        settings.setValue("OmeroHost", self.host.text())
        settings.setValue("OmeroPort", self.port.value())
        settings.setValue("OmeroUsername", self.username.text())
        keyring.set_password("bioif-omero", self.username.text(), self.password.text())

    def onShow(self, settings):
        
        # settings BioImageITVersion might be out of date: update it onShow (we can't do that in __init__ we have no settings)
        if settings.value("BioImageITVersion") != self.autoUpdateString:
            versionInfo = self.getInstalledVersion()
            version = versionInfo['version'].split('-')[1]
            settings.setValue("BioImageITVersion", version)

        self.lePythonEditor.setText(settings.value("EditorCmd"))
        self.leImageViewer.setText(settings.value("ImageViewerCmd"))
        self.alwaysInstallNapariDependencies.setCheckState(QtCore.Qt.CheckState.Checked if settings.value("ImageViewerAlwaysInstallDependencies") == 'Yes' else QtCore.Qt.CheckState.Unchecked if settings.value("ImageViewerAlwaysInstallDependencies") == 'No' else QtCore.Qt.CheckState.PartiallyChecked)
        username = settings.value("OmeroUsername")
        self.username.setText(username)
        self.password.setText(keyring.get_password("bioif-omero", username))

        try:
            self.historyDepth.setValue(int(settings.value("HistoryDepth")))

            self.updateVersionSelector(settings.value("BioImageITVersion"))

            email = settings.value("Email")
            self.email.setText(email)
            self.mailApiKey.setText(settings.value("MailAPIKey"))
            self.mailApiSecret.setText(keyring.get_password("bioif-mail-api-secret", email))
            
            self.redirectOutput.setChecked(settings.value("RedirectOutput") == "true")
        except:
            pass
    
    def getVersionPath(self):
        return getRootPath() / 'version.json'

    def getInstalledVersion(self):
        with open(self.getVersionPath(), 'r') as f:
            return json.load(f)
    
    def getVersions(self, proxies=None):
        proxies = self.getInstalledVersion()['proxies'] if proxies is None else proxies
        return requests.get(f'https://gitlab.inria.fr/api/v4/projects/{self.projectId}/repository/tags', proxies=proxies).json()
    
    def downloadVersion(self, autoUpdate, versionName, proxies, newSources):
        import zipfile, io
        r = requests.get(f'https://gitlab.inria.fr/api/v4/projects/{self.projectId}/repository/archive.zip', params={'sha': versionName}, proxies=proxies)
        z = zipfile.ZipFile(io.BytesIO(r.content))
        z.extractall(getRootPath())
        if not self.progressDialog.wasCanceled():
            inmain(self.setVersionJson, autoUpdate, proxies, newSources)

    def showProgressAndDownloadVersion(self, autoUpdate, versionName, proxies, newSources):
        self.progressDialog = QProgressDialog("Downloading...", "Abort", 0, 0, self)
        self.progressDialog.setValue(0)
        self.progressDialog.show()
        inthread(self.downloadVersion, autoUpdate, versionName, proxies, newSources)
    
    def setVersionJson(self, autoUpdate, proxies, newSources):
        with open(self.getVersionPath(), 'w') as f:
            json.dump(dict(autoUpdate=autoUpdate, version=newSources.name, proxies=proxies), f)
        if self.progressDialog is not None:
            self.progressDialog.hide()
        answer = QMessageBox.warning(self, "New BioImageIT version", "Please restart the application to take changes into account. Would you like to quit BioImageIT?", QMessageBox.Yes | QMessageBox.No)
        if answer == QMessageBox.Yes:
            sys.exit(0)
    
    def setVersion(self):
        versionName = self.versionSelector.currentText()
        versionTarget = self.versionSelector.currentData()
        versionInfo = self.getInstalledVersion()
        if versionInfo['autoUpdate']:
            versionName = self.versionSelector.itemText(1)
            versionTarget = self.versionSelector.itemData(1)
        newSources = (getRootPath() / f'bioimageit-{versionName}-{versionTarget}').resolve()
        if not newSources.exists():
            self.showProgressAndDownloadVersion(versionInfo['autoUpdate'], versionName, versionInfo['proxies'], newSources)
        else:
            self.setVersionJson(versionInfo['autoUpdate'], versionInfo['proxies'], newSources)
    
    def setVersionSelector(self, tags, version):
        self.versionSelector.currentTextChanged.disconnect(self.setVersion)
        while self.versionSelector.count() > 0:
            self.versionSelector.removeItem(0)
        self.versionSelector.addItem(self.autoUpdateString)
        for tag in tags:
            self.versionSelector.addItem(tag['name'], tag['target'])
        self.versionSelector.setCurrentText(version if version is not None else self.autoUpdateString)
        self.versionSelector.currentTextChanged.connect(self.setVersion)

    def getVersionsThenSetVersionSelector(self, version=None):
        try:
            tags = self.getVersions()
            inmain(lambda: self.setVersionSelector(tags, version))
        except Exception as e:
            import logging
            logging.error(f'Impossible to get BioImageIT versions: {e}')

    def updateVersionSelector(self, version=None):
        inthread(self.getVersionsThenSetVersionSelector, version)