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


from qtpy import QtCore
from qtpy.QtWidgets import QAction, QTextBrowser
from PyFlow.UI.Tool.Tool import DockTool
import logging
import os

class LoggerTool(DockTool):
    """docstring for NodeBox tool."""

    formatter = logging.Formatter(
        "[%(levelname)s %(asctime)s]:   %(message)s", "%H:%M:%S"
    )

    def __init__(self):
        super(LoggerTool, self).__init__()
        self.logView = QTextBrowser()
        self.logView.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        self.logView.setReadOnly(True)
        self.clearAction = QAction("Clear", None)
        self.clearAction.triggered.connect(self.clearView)
        self.logView.addAction(self.clearAction)
        self.setWidget(self.logView)

    #####################################################
    # Logger
    #####################################################

    def clearView(self, *args):
        self.logView.clear()

    @staticmethod
    def supportedSoftwares():
        return ["standalone"]

    def logPython(self, text, mode=0):
        colorchart = {0: "black", 1: "orange", 2: "red"}

        horScrollBar = self.logView.horizontalScrollBar()
        verScrollBar = self.logView.verticalScrollBar()
        scrollIsAtEnd = verScrollBar.maximum() - verScrollBar.value() <= 10

        for l in text.split("\n"):
            if len(l) > 0:
                splitted = l.split(",")
                if len(splitted) >= 3:
                    if (
                        "File" in splitted[0]
                        and "line" in splitted[1]
                        and "in" in splitted[2]
                    ):
                        file = splitted[0].split('"')[1]
                        line = splitted[1].split("line ")[1]
                        if os.path.exists(file):
                            file = file.replace("\\", "//")
                            errorLink = (
                                # """<a href=%s><span style=" text-decoration: underline; color:red;">%s</span></a></p>"""
                                # % (file + "::%s" % line, l)
                                """<span style=" text-decoration: underline; color:red;">%s</span>""" % l
                            )
                            self.logView.append(errorLink)
                    else:
                        self.logView.append(
                            '<span style=" color:%s;">%s<span>' % (colorchart[mode], l)
                        )
                else:
                    self.logView.append(
                        '<span style=" color:%s;">%s<span>' % (colorchart[mode], l)
                    )
        
        if scrollIsAtEnd:
            verScrollBar.setValue(verScrollBar.maximum()) # Scrolls to the bottom
            horScrollBar.setValue(0) # scroll to the left


    def update(self):
        super(LoggerTool, self).update()

    def onShow(self):
        super(LoggerTool, self).onShow()
        self.clearView()
        logger = logging.getLogger()
        for handler in logger.handlers:
            if isinstance(handler, logging.FileHandler):
                with open(handler.baseFilename, 'r') as f:
                    logs = f.read()
                    self.logPython(logs.split('Launching BioImageIT...')[-1])

    def closeEvent(self, event):
        self.hide()

    @staticmethod
    def isSingleton():
        return True

    @staticmethod
    def defaultDockArea():
        return QtCore.Qt.BottomDockWidgetArea

    @staticmethod
    def toolTip():
        return "Logger"

    @staticmethod
    def name():
        return "Logger"
