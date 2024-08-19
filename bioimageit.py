# import subprocess
# from EnvironmentManager import environmentManager
# print('The greatest test')

# environmentManager.create('bioimageit', dict(python=3.10, conda='bioimageit', pip=[]))
# commands = environmentManager._activateConda() + [f'{environmentManager.condaBin} activate bioimageit', 'python pyflow.py']
# process = environmentManager._executeCommands(commands)

import requests, zipfile, io
from pathlib import Path
import shutil
import logging
import tomllib

projectId = 54065 # The BioImageIT Project

logging.basicConfig(level=logging.INFO)


r = requests.get(f'https://gitlab.inria.fr/api/v4/projects/{projectId}/repository/tags')
tags = r.json()
tag = tags[0]

sources = Path(f'bioimageit-{tag['name']}-{tag['target']}')

if not sources.exists():
    r = requests.get(f'https://gitlab.inria.fr/api/v4/projects/{projectId}/repository/archive.zip', params={'sha': tag['name']})
    z = zipfile.ZipFile(io.BytesIO(r.content))
    z.extractall()

for file in sorted(list(sources.iterdir())):
    destination = file.parent.parent / file.name
    if destination.exists():
        if destination.is_dir():
            shutil.rmtree(destination)
        else:
            destination.unlink()
    file.rename(destination)

# Keep the empty sources folder since its name tells which version is installed

from PyFlow.ToolManagement.EnvironmentManager import environmentManager
# em = import_module('PyFlow.ToolManagement.EnvironmentManager')

with open("pyproject.toml", "rb") as f:
    projectConfiguration = tomllib.load(f)
    pythonVersion = projectConfiguration['project']['requires-python']
    pipDependencies = projectConfiguration['project']['dependencies']
    condaDependencies = [key + value for key, value in projectConfiguration['tool']['pixi']['dependencies'].items()]

environmentManager.create('bioimageit', dict(pip=pipDependencies, conda=condaDependencies, python=pythonVersion), False)
process = environmentManager.executeCommands(environmentManager._activateConda() + [f'{environmentManager.condaBin} activate bioimageit', 'python -u pyflow.py'])
for line in process.stdout:
    print(line)
print(process.wait())