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


import sys
from qtpy.QtWidgets import QApplication
from qtpy import QtCore, QtGui
import argparse
import os
import json
import logging
import logging.handlers
from pathlib import Path

bundlePath = Path(sys._MEIPASS).parent if getattr(sys, 'frozen', False) else Path(__file__).parent

logging.basicConfig(
    level=logging.INFO,
    handlers=[
        logging.handlers.RotatingFileHandler(bundlePath / 'bioimageit.log', maxBytes=5000000, backupCount=1, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

from PyFlow.App import PyFlow

def main(instance=None):

	QApplication.setAttribute(QtCore.Qt.AA_ShareOpenGLContexts)
	
	app = QApplication(sys.argv)
	icon = QtGui.QIcon()
	icon.addFile('PyFlow/UI/resources/Logo.ico', QtCore.QSize(128,128))
	app.setWindowIcon(icon)
	app.setApplicationDisplayName('BioImageIT')
	
	instance = PyFlow.instance(software="standalone")

	instance.updateCSS()
	instance.activateWindow()
	instance.show()
	
	parser = argparse.ArgumentParser(description="PyFlow CLI")
	parser.add_argument("-f", "--filePath", type=str, default="Untitled.pygraph")
	parsedArguments, unknown = parser.parse_known_args(sys.argv[1:])
	filePath = parsedArguments.filePath
	if not filePath.endswith(".pygraph"):
		filePath += ".pygraph"
	if os.path.exists(filePath):
			with open(filePath, 'r') as f:
				data = json.load(f)
				instance.loadFromData(data)
				instance.currentFileName = filePath
	app.exec_()

if __name__ == "__main__":
	main()
