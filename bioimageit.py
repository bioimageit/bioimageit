import sys
from pathlib import Path

projectId = 54065 # The BioImageIT Project on Gitlab

def getVersions():
    import requests
    print('Checking BioImageIT versions...')
    r = requests.get(f'https://gitlab.inria.fr/api/v4/projects/{projectId}/repository/tags')
    return r.json()

def getLatestVersion():
    return getVersions()[0]

def downloadSources(versionName):
    import requests, zipfile, io
    print(f'Downloading BioImageIT {versionName}...')
    r = requests.get(f'https://gitlab.inria.fr/api/v4/projects/{projectId}/repository/archive.zip', params={'sha': versionName})
    z = zipfile.ZipFile(io.BytesIO(r.content))
    z.extractall()

def downloadLatestVersion(selected, latest):
    try:
        tag = getLatestVersion()

        sources = Path(f'bioimageit-{tag['name']}-{tag['target']}')

        if not sources.exists():
            downloadSources(tag['name'])
            latest.unlink(missing_ok=True)
            if not selected.exists():
                latest.symlink_to(sources, True)
    except Exception as e:
        print('Could not check the BioImageIT versions:')
        print(e)
    if not selected.exists() and not latest.exists():
        sys.exit('The bioimageit sources could not be downloaded.')
    
    return selected if selected.exists() else latest

def createEnvironment(sources, environmentManager, environment):
    import tomllib, logging
    print('Creating BioImageIT environment...')
    with open(sources / "pyproject.toml", "rb") as f:
        projectConfiguration = tomllib.load(f)
        pythonVersion = projectConfiguration['project']['requires-python']
        pipDependencies = projectConfiguration['project']['dependencies']
        condaDependencies = [key + value for key, value in projectConfiguration['tool']['pixi']['dependencies'].items()]
    logging.basicConfig(level=logging.INFO)
    environmentManager.create(environment, dict(pip=pipDependencies, conda=condaDependencies, python=pythonVersion), False)

latest = Path(f'bioimageit-latest')                 # exists by default or if user wants to auto update
selected = Path(f'bioimageit-selected-version')     # exists if user has selected a specific version

# If the selected version does not exist: auto update
if not selected.exists():
    sources = downloadLatestVersion(selected, latest)

# Does not work, but path is added when freezing
if getattr(sys, 'frozen', False):
    sys.path.append(sources.resolve())

from PyFlow.ToolManagement.EnvironmentManager import environmentManager

# from importlib import import_module
# environmentManager = import_module('PyFlow.ToolManagement.EnvironmentManager').environmentManager

# import importlib
# if spec:=importlib.util.spec_from_file_location('EnvironmentManager', f'{sources.name}/PyFlow/ToolManagement/EnvironmentManager.py'):
#         dependency = importlib.util.module_from_spec(spec)
#         sys.modules['EnvironmentManager'] = dependency
#         spec.loader.exec_module(dependency)
#         environmentManager = dependency.environmentManager

environment = 'bioimageit'

if not environmentManager.environmentExists(environment):
    createEnvironment(sources, environmentManager, environment)

print('Launching BioImageIT...')
process = environmentManager.executeCommands(environmentManager._activateConda() + [f'{environmentManager.condaBin} activate {environment}', f'cd {sources}', f'python -u pyflow.py'])
for line in process.stdout:
    print(line)
print(process.wait())