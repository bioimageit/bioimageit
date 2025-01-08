import sys
import os
import platform
import json
import tkinter as tk
from tkinter import ttk
import threading
from pathlib import Path
import logging
from importlib import import_module
import shutil
import psutil

# Bundle path is _internal when frozen, and bioimageit/ otherwise
def getBundlePath():
	return Path(sys._MEIPASS) if getattr(sys, 'frozen', False) else Path(__file__).parent

# Root path is bioimageit/ in all cases
def getRootPath():
	return Path(sys._MEIPASS).parent if getattr(sys, 'frozen', False) else Path(__file__).parent

os.chdir(getRootPath())

logging.basicConfig(
    level=logging.INFO,
    handlers=[
        logging.FileHandler(getRootPath() / 'initialize.log', mode='w', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger()
logger.info('Initializing BioImageIT...')

projectId = 54065 # The BioImageIT Project on Gitlab
proxies = None
versionPath = Path('version.json')

gui = None

class Gui:

    nSteps = 3

    def __init__(self):
        # Create the install window
        self.window = tk.Tk()
        self.window.title("BioImageIT")

        # Create a StringVar to hold the label text
        self.labelText = tk.StringVar()
        self.labelText.set("Starting...")

        # Create a label widget
        self.label = tk.Label(self.window, textvariable=self.labelText)
        self.label.pack(pady=10)

        # Create a progress bar widget
        self.progressBar = ttk.Progressbar(self.window, maximum=self.nSteps)
        self.progressBar.pack(pady=10, padx=20, fill=tk.X)

        self.logText = tk.Text(self.window, height=5, width=52)
        self.logText.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)

        # Create a Scrollbar and attach it to the Text widget
        self.logScroll = tk.Scrollbar(self.window, command=self.logText.yview)
        self.logScroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.logText.config(yscrollcommand=self.logScroll.set)

def logMainThread(message):
    gui.logText.insert(tk.END, message)
    gui.logText.yview(tk.END)  # Auto-scroll to the latest log entry
    gui.window.update_idletasks()

def log(message):
    if gui is None: return
    gui.window.after(0, lambda: logMainThread(message))
    
def updateLabel(message):
    logging.info(message)
    if gui is None: return
    gui.window.after(0, lambda: gui.labelText.set(message))
    log(message + '\n')

def getVersions():
    import requests
    # gui.progressBar.step(1)
    # updateLabel('Checking BioImageIT versions...')
    logging.info('Checking BioImageIT versions...')
    r = requests.get(f'https://gitlab.inria.fr/api/v4/projects/{projectId}/repository/tags', proxies=proxies)
    return r.json()

def getLatestVersion():
    return getVersions()[0]

def downloadSources(sources:Path, versionName):
    global gui
    gui = Gui()

    updateLabel(f'Downloading BioImageIT {versionName}...')
    
    gui.progressBar.step(2)
    
    import requests, zipfile, io
    url = f'https://gitlab.inria.fr/api/v4/projects/{projectId}/repository/archive.zip'

    # r = requests.get(url, params={'sha': versionName}, proxies=proxies)
    # z = zipfile.ZipFile(io.BytesIO(r.content))
    # z.extractall()
    
    response = requests.get(url, params={'sha': versionName}, proxies=proxies, stream=True)
    totalSize = int(response.headers.get('content-length', 0))
    blockSize = 1024  # 1 Kibibyte
    downloadedData = io.BytesIO()

    gui.progressBar.configure(maximum=totalSize)

    # Download the file in chunks and update the progress bar
    for data in response.iter_content(blockSize):
        downloadedData.write(data)
        downloadedSize = downloadedData.tell()
        gui.progressBar.step(downloadedSize)
        logging.info(f"Downloaded {downloadedSize} of {totalSize} bytes")
        gui.window.update_idletasks()

    gui.progressBar.configure(maximum=gui.nSteps)
    gui.progressBar.step(1)

    # Extract the zip file from memory
    updateLabel("Extracting files...")
    downloadedData.seek(0)
    with zipfile.ZipFile(downloadedData, 'r') as z:
        z.extractall(getRootPath())

    gui.window.update_idletasks()
    

def downloadLatestVersion():
    tag = getLatestVersion()

    sources = Path(f"bioimageit-{tag['name']}-{tag['target']}")

    if not sources.exists():
        downloadSources(sources, tag['name'])
    return sources

class ProxyDialog:

    def __init__(self, parent):
        top = self.top = tk.Toplevel(parent)
        top.title("Proxy Settings")
        
        self.label = ttk.Label(top, text = """Enter your config settings in yaml format, as in https://tinyurl.com/3ta9zn6t""")

        self.textArea = tk.Text(top, height = 5, width = 52)
        self.textArea.insert(tk.END, """#For example:
    http: http://user:pass@corp.com:8080
    https: http://user:pass@corp.com:8080
    # Or
    'http://10.20.1.128': 'http://10.10.1.10:5323'
    # ...
    """)

        self.button = ttk.Button(top, text = "Confirm", command=self.parse)

        self.label.pack()
        self.textArea.pack()
        self.button.pack()

    def parse(self):
        import yaml
        global proxies
        proxies = yaml.safe_load(self.textArea.get("1.0",tk.END))
        self.top.destroy()

def getProxySettingsFromGUI():
    dialog = ProxyDialog()
    if gui is not None:
        gui.window.wait_window(dialog.top)

def getProxySettingsFromConda():

    condaConfigurations = ["/etc/conda/.condarc",
                        "/etc/conda/condarc",
                        "/etc/conda/condarc.d/",
                        "/etc/conda/.mambarc",
                        "/var/lib/conda/.condarc",
                        "/var/lib/conda/condarc",
                        "/var/lib/conda/condarc.d/",
                        "/var/lib/conda/.mambarc"] if platform.system() != 'Windows' else [
                        "C:\\ProgramData\\conda\\.condarc",
                        "C:\\ProgramData\\conda\\condarc",
                        "C:\\ProgramData\\conda\\condarc.d",
                        "C:\\ProgramData\\conda\\.mambarc"
                        ]

    condaConfigurations += [
        "$CONDA_ROOT/.condarc",
        "$CONDA_ROOT/condarc",
        "$CONDA_ROOT/condarc.d/",
        "$MAMBA_ROOT_PREFIX/.condarc",
        "$MAMBA_ROOT_PREFIX/condarc",
        "$MAMBA_ROOT_PREFIX/condarc.d/",
        "$MAMBA_ROOT_PREFIX/.mambarc",
        "$XDG_CONFIG_HOME/conda/.condarc",
        "$XDG_CONFIG_HOME/conda/condarc",
        "$XDG_CONFIG_HOME/conda/condarc.d/",
        "~/.config/conda/.condarc",
        "~/.config/conda/condarc",
        "~/.config/conda/condarc.d/",
        "~/.conda/.condarc",
        "~/.conda/condarc",
        "~/.conda/condarc.d/",
        "~/.condarc",
        "~/.mambarc",
        "$CONDA_PREFIX/.condarc",
        "$CONDA_PREFIX/condarc",
        "$CONDA_PREFIX/condarc.d/",
        "$CONDARC",
        "$MAMBARC"
    ]

    import yaml
    for condaConfiguration in condaConfigurations:
        condaConfiguration = Path(condaConfiguration).resolve()
        if condaConfiguration.exists():
            condaConfigurationFiles = sorted(list(condaConfiguration.glob('*.yml') + condaConfiguration.glob('*.yaml'))) if condaConfiguration.is_dir() else [condaConfiguration]
            for condaConfigurationFile in condaConfigurationFiles:
                with open(condaConfigurationFile, 'r') as f:
                    configuration = yaml.safe_load(f)
                    if 'proxy_servers' in configuration:
                        global proxies
                        proxies = configuration['proxy_servers']
        
    # set REQUESTS_CA_BUNDLE to override the certificate bundle trusted by Requests

def tryDownloadLatestVersionOrGetProxySettingsFromGUI():
    import requests
    try:
        return downloadLatestVersion()
    except requests.exceptions.ProxyError as e:
        logging.warning(e)
        getProxySettingsFromGUI()
        return downloadLatestVersion()

def tryDownloadLatestVersionOrGetProxySettingsFromConda():
    import requests
    try:
        return downloadLatestVersion()
    except requests.exceptions.ProxyError as e:
        logging.warning(e)
        logging.warning('Searching for proxy settings in conda, mamba or micromamba configuration files...')
        getProxySettingsFromConda()
        return tryDownloadLatestVersionOrGetProxySettingsFromGUI()

def createEnvironment(sources, environmentManager, environment):
    import tomllib
    if gui is not None:
        gui.window.after(0, lambda: gui.progressBar.step(3))
    updateLabel('Creating BioImageIT environment...')
    with open(sources / "pyproject.toml", "rb") as f:
        projectConfiguration = tomllib.load(f)
        pythonVersion = projectConfiguration['project']['requires-python']
        pipDependencies = projectConfiguration['project']['dependencies']
        condaDependencies = [key + value for key, value in projectConfiguration['tool']['pixi']['dependencies'].items()]
    environmentManager.create(environment, dict(pip=pipDependencies, conda=condaDependencies, python=pythonVersion))

def updateVersion():
    if versionPath.exists():
        with open(versionPath, 'r') as f:
            versionInfo = json.load(f)
    else:
        versionInfo = dict(autoUpdate=True, version='unknown', proxies=None)

    sources = Path(versionInfo['version'])
    proxies = versionInfo['proxies'] if 'proxies' in versionInfo else None

    # If the selected version does not exist: auto update
    if versionInfo['autoUpdate']:
        try:
            sources = tryDownloadLatestVersionOrGetProxySettingsFromConda()
        except Exception as e:
            logging.warning('Could not check the BioImageIT versions:')
            logging.warning(e)
            if versionInfo['version'] == 'unknown':
                sys.exit(f'The bioimageit sources could not be downloaded.')
        
        versionInfo['version'] = sources.name
        versionInfo['proxies'] = proxies
        with open(versionPath, 'w') as f:
            json.dump(versionInfo, f)
    return sources

def launchBiit(sources):
    
    # Do not import with 
    # from PyFlow.ToolManagement.EnvironmentManager import environmentManager, attachLogHandler
    # since PyInstaller would freeze the EnvironmentManager and we could not benefit from its updates
    # Copy EnvironmentManager to avoid importing all PyFlow dependencies
    shutil.copyfile(sources / 'PyFlow' / 'ToolManagement' / 'EnvironmentManager.py', sources / 'EnvironmentManager.py')
    sys.path.append(str(sources.resolve()))
    # Imports from the Environment manager must be available now
    from multiprocessing.connection import Client
    if sys.version_info < (3, 11):
        from typing_extensions import TypedDict, Required, NotRequired, Self
    else:
        from typing import TypedDict, Required, NotRequired, Self
    print(Client, TypedDict, Required, NotRequired, Self)

    EnvironmentManager = import_module('EnvironmentManager')
    environmentManager = EnvironmentManager.environmentManager
    arch = 'arm64' if platform.processor().lower().startswith('arm') else 'x86_64' 
    environmentManager.copyMicromambaDependencies(getBundlePath() / 'data' / arch)

    environment = 'bioimageit'

    if not environmentManager.environmentExists(environment):
        EnvironmentManager.attachLogHandler(log)
        createEnvironment(sources, environmentManager, environment)

    if gui is not None:
        gui.window.after(0, lambda: gui.progressBar.step(4))
    updateLabel('Launching BioImageIT...')

    executable = 'python'
    # Hack for OS X to display BioImageIT in the menu instead of python
    if platform.system() == 'Darwin':
        condaPath, _ = environmentManager._getCondaPaths()
        python = condaPath / 'envs/' / environment / 'bin' / 'python'
        pythonSymlink = sources / 'BioImageIT'
        if not pythonSymlink.exists():
            Path(pythonSymlink).symlink_to(python)
        executable = './BioImageIT'

    with environmentManager.executeCommands(environmentManager._activateConda() + [f'{environmentManager.condaBin} activate {environment}', f'cd {sources}', f'{executable} -u pyflow.py']) as process:

        for line in process.stdout:
            log(line)
            if line.strip() == 'Initialization complete':
                if gui is not None:
                    gui.window.after(0, close_window)
    
def close_window():
    """Properly close the Tkinter window."""
    global gui
    gui.window.quit()
    gui.window.destroy()
    gui.window.update()
    gui.window.update_idletasks()
    gui = None

sources = updateVersion()
# Start the task in a separate thread to keep the GUI responsive
thread = threading.Thread(target=lambda: launchBiit(sources), daemon=True)
thread.start()

# Start the Tkinter event loop
if gui is not None:
    gui.window.mainloop()
thread.join()