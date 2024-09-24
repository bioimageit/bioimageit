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

from qtpy import QtCore, QtWidgets, QtGui

class WelcomeDialog(QtWidgets.QDialog):
    
    def __init__(self, parent: QtWidgets.QWidget=None, workflowTool=None) -> None:
        super().__init__(parent)
        self.workflowTool = workflowTool
        self.workflowPath = None
        self.setModal(True)
        self.setWindowTitle("Welcome to BioImageIT")

        welcomeMessage = QtWidgets.QLabel(
            "Welcome to BioImageIT!\n\n"
            "To get started, you need to define the folder where your first workflow will be stored."
        )

        self.createButton = QtWidgets.QPushButton("Create workflow")
        self.createButton.clicked.connect(lambda: self.validatePath(self.workflowTool.createWorkflow()))

        self.openButton = QtWidgets.QPushButton("Open workflow")
        self.openButton.clicked.connect(lambda: self.validatePath(self.workflowTool.openWorkflow()))

        buttonLayout = QtWidgets.QHBoxLayout()
        buttonLayout.addWidget(self.createButton)
        buttonLayout.addWidget(self.openButton)

        self.workflowNameEdit = QtWidgets.QLineEdit()
        self.workflowNameEdit.setPlaceholderText("Workflow directory will appear here")
        self.workflowNameEdit.setReadOnly(True)  # Make it read-only, the user can only fill it via the dialog

        preferenceMessage = QtWidgets.QLabel(
            "You can also set your favorite code editor, image viewer and OMERO settings in the preference panel."
        )

        # self.prefsButton = QtWidgets.QPushButton("Close and set preferences")
        self.prefsButton = QtWidgets.QPushButton("Next")
        self.prefsButton.setEnabled(False)  # Initially disabled
        self.prefsButton.clicked.connect(self.openPreferencesAndClose)

        # self.closeButton = QtWidgets.QPushButton("Close")
        # self.closeButton.setEnabled(False)  # Initially disabled
        # self.closeButton.clicked.connect(self.accept)

        # buttonLayout2 = QtWidgets.QHBoxLayout()
        # buttonLayout2.addWidget(self.prefsButton)
        # buttonLayout2.addWidget(self.closeButton)

        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.addWidget(welcomeMessage)
        mainLayout.addLayout(buttonLayout)
        mainLayout.addWidget(self.workflowNameEdit)
        mainLayout.addWidget(preferenceMessage)
        mainLayout.addWidget(self.prefsButton)
        # mainLayout.addLayout(buttonLayout2)

        self.setLayout(mainLayout)

    def centerWindow(self):
        # Get current screen size
        screenRect = QtGui.QGuiApplication.screenAt(self.pos()).geometry()

        # Using minimum size of window
        size = self.minimumSize()

        # Set top left point
        topLeft = QtCore.QPoint((screenRect.width() / 2) - (size.width() / 2), (screenRect.height() / 2) - (size.height() / 2))

        # set window position
        self.setGeometry(QtCore.QRect(topLeft, size))

    def validatePath(self, path):
        if path:
            self.workflowNameEdit.setText(str(path))
            self.workflowPath = path
            # self.closeButton.setEnabled(True)
            self.prefsButton.setEnabled(True)
    
    def openPreferencesAndClose(self):
        self.workflowTool.pyFlowInstance.showPreferencesWindow()
        self.accept()