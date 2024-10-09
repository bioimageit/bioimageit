import sys
import os
import platform
import json
import tkinter as tk
from tkinter import ttk
import threading
from pathlib import Path
import logging

def getBundlePath():
	return Path(sys._MEIPASS).parent if getattr(sys, 'frozen', False) else Path(__file__).parent

os.chdir(getBundlePath())

logging.basicConfig(
    level=logging.INFO,
    handlers=[
        logging.FileHandler(getBundlePath() / 'initialize.log', mode='w'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger()
logger.info('Initializing BioImageIT...')

projectId = 54065 # The BioImageIT Project on Gitlab
proxies = None
versionPath = Path('version.json')

# Create the install window
window = tk.Tk()
window.title("BioImageIT")

# Create a StringVar to hold the label text
labelText = tk.StringVar()
labelText.set("Starting...")

# Create a label widget
label = tk.Label(window, textvariable=labelText)
label.pack(pady=10)

# Create a progress bar widget
nSteps = 4
progressBar = ttk.Progressbar(window, maximum=nSteps)
progressBar.pack(pady=10, padx=20, fill=tk.X)

logText = tk.Text(window, height=5, width=52)
logText.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)

# Create a Scrollbar and attach it to the Text widget
logScroll = tk.Scrollbar(window, command=logText.yview)
logScroll.pack(side=tk.RIGHT, fill=tk.Y)
logText.config(yscrollcommand=logScroll.set)

def log(message):
    logText.insert(tk.END, message)
    logText.yview(tk.END)  # Auto-scroll to the latest log entry
    window.update_idletasks()
    
def updateLabel(message):
    logging.info(message)
    labelText.set(message)
    log(message + '\n')

def getVersions():
    import requests
    progressBar.step(1)
    updateLabel('Checking BioImageIT versions...')
    r = requests.get(f'https://gitlab.inria.fr/api/v4/projects/{projectId}/repository/tags', proxies=proxies)
    return r.json()

def getLatestVersion():
    return getVersions()[0]

def downloadSources(sources:Path, versionName):
    updateLabel(f'Downloading BioImageIT {versionName}...')
    
    progressBar.step(2)
    
    import requests, zipfile, io
    url = f'https://gitlab.inria.fr/api/v4/projects/{projectId}/repository/archive.zip'

    # r = requests.get(url, params={'sha': versionName}, proxies=proxies)
    # z = zipfile.ZipFile(io.BytesIO(r.content))
    # z.extractall()
    
    response = requests.get(url, params={'sha': versionName}, proxies=proxies, stream=True)
    totalSize = int(response.headers.get('content-length', 0))
    blockSize = 1024  # 1 Kibibyte
    downloadedData = io.BytesIO()

    progressBar.configure(maximum=totalSize)

    # Download the file in chunks and update the progress bar
    for data in response.iter_content(blockSize):
        downloadedData.write(data)
        downloadedSize = downloadedData.tell()
        progressBar.step(downloadedSize)
        logging.info(f"Downloaded {downloadedSize} of {totalSize} bytes")
        window.update_idletasks()

    progressBar.configure(maximum=nSteps)
    progressBar.step(2)

    # Extract the zip file from memory
    updateLabel("Extracting files...")
    downloadedData.seek(0)
    with zipfile.ZipFile(downloadedData, 'r') as z:
        z.extractall(getBundlePath())

    window.update_idletasks()
    

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
    window.wait_window(dialog.top)

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
    progressBar.step(3)
    updateLabel('Creating BioImageIT environment...')
    with open(sources / "pyproject.toml", "rb") as f:
        projectConfiguration = tomllib.load(f)
        pythonVersion = projectConfiguration['project']['requires-python']
        pipDependencies = projectConfiguration['project']['dependencies']
        condaDependencies = [key + value for key, value in projectConfiguration['tool']['pixi']['dependencies'].items()]
    environmentManager.create(environment, dict(pip=pipDependencies, conda=condaDependencies, python=pythonVersion), False)

def main():

    if versionPath.exists():
        with open(versionPath, 'r') as f:
            versionInfo = json.load(f)
    else:
        versionInfo = dict(autoUpdate=True, version='unknown', proxies=None)

    sources = Path(versionInfo['version'])
    proxies = versionInfo['proxies'] if versionInfo['proxies'] != 'None' else None

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

        sys.path.append(str(sources.resolve()))
        
        from PyFlow.ToolManagement.EnvironmentManager import environmentManager, attachLogHandler

        environment = 'bioimageit'

        if not environmentManager.environmentExists(environment):
            attachLogHandler(log)
            createEnvironment(sources, environmentManager, environment)

        progressBar.step(4)
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

        process = environmentManager.executeCommands(environmentManager._activateConda() + [f'{environmentManager.condaBin} activate {environment}', f'cd {sources}', f'{executable} -u pyflow.py'])

        for line in process.stdout:
            log(line)
            if line.strip() == 'Initialization complete':
                window.destroy()

        process.wait()
    

# Start the task in a separate thread to keep the GUI responsive
thread = threading.Thread(target=main, daemon=True)
thread.start()

# Start the Tkinter event loop
window.mainloop()
