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
from qtpy import QtCore
import argparse
import os
import json
from importlib import reload
from functools import partial

def restart(app):
	PyFlow = reload(sys.modules['biit.App']).PyFlow
	app.quit()
	main()

def main():
	from biit.App import PyFlow

	QApplication.setAttribute(QtCore.Qt.AA_ShareOpenGLContexts)
	
	app = QApplication(sys.argv)
	
	instance = PyFlow.instance(software="standalone", restart=partial(restart, app))
	instance.updateCSS()
	
	if instance is not None:
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

		sys.exit(app.exec_())

if __name__ == "__main__":
	main()
