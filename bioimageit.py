import sys
import os
import platform
import json
import time
import webbrowser
import threading
import traceback
from pathlib import Path
import logging
from importlib import import_module
import shutil
import yaml

# Bundle path is bioimageit/_internal when frozen, and bioimageit/ otherwise, only used to copy files for windows
def getBundlePath():
	return Path(sys._MEIPASS) if getattr(sys, 'frozen', False) else Path(__file__).parent

# Root path is bioimageit/ in all cases
def getRootPath():
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS).parent if platform.system() != 'Darwin' else Path(sys._MEIPASS).parent.parent.parent / 'BioImage-IT.data'
    else:
        return Path(__file__).parent

getRootPath().mkdir(exist_ok=True, parents=True)
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

# Import EnvironmentManager to make its modules available in bundle
from PyFlow import getSourcesPath
import PyFlow.ToolManagement.EnvironmentManager

projectId = 54065 # The BioImageIT Project on Gitlab
proxies = None
versionPath = Path('version.json')
versionInfo = None

gui = None

createGui = threading.Event()
guiCreated = threading.Event()
loading = threading.Event()
loading.set()

session = None

def getSession():
    global session
    if session is not None: return session
    import requests
    from requests.adapters import HTTPAdapter
    session = requests.Session()
    session.mount('http://', HTTPAdapter(max_retries=2))
    session.mount('https://', HTTPAdapter(max_retries=2))
    return session

class Gui:

    nSteps = 3

    def __init__(self):
        import tkinter as tk
        from tkinter import ttk

        # Create the install window
        self.window = tk.Tk()
        self.window.title("BioImageIT")

        width, height = 800, 500
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.window.geometry(f"{width}x{height}+{x}+{y}")

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
    import tkinter as tk
    gui.logText.insert(tk.END, message)
    gui.logText.yview(tk.END)  # Auto-scroll to the latest log entry
    gui.window.update_idletasks()

def log(message):
    if not guiCreated.is_set(): return
    gui.window.after(0, lambda: logMainThread(message + '\n'))
    
def updateLabel(message):
    logging.info(message)
    if not guiCreated.is_set(): return
    gui.window.after(0, lambda: gui.labelText.set(message))
    log(message)

def setProxies(newProxies, save=True):
    global proxies
    proxies = newProxies
    if save and proxies is not None:
        versionInfo['proxies'] = proxies
        with open(versionPath, 'w') as f:
            json.dump(versionInfo, f)

        configuration = {}
        mambaConfigPath = Path('micromamba/.mambarc')
        if mambaConfigPath.exists():
            with open(mambaConfigPath, 'r') as f:
                newConfiguration = yaml.safe_load(f)
                if newConfiguration is not None:
                    configuration = newConfiguration
            configuration['proxy_servers'] = proxies
            with open(mambaConfigPath, 'w') as f:
                yaml.safe_dump(configuration, f)
    
def getVersions():
    session = getSession()
    # gui.progressBar.step(1)
    # updateLabel('Checking BioImageIT versions...')
    logging.info('Checking BioImageIT versions...')
    r = session.get(f'https://gitlab.inria.fr/api/v4/projects/{projectId}/repository/tags', proxies=proxies, timeout=1)
    return r.json()

def getLatestVersion():
    return getVersions()[0]

def downloadSources(versionName):
    
    import zipfile, io
    url = f'https://gitlab.inria.fr/api/v4/projects/{projectId}/repository/archive.zip'
    session = getSession()
    response = session.get(url, params={'sha': versionName}, proxies=proxies, stream=True, timeout=1)
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
    
def waitGui():
    if gui is None:
        createGui.set()
    while not guiCreated.is_set():
        time.sleep(0.01)

def downloadLatestVersion():
    tag = getLatestVersion()
    versionName = tag['name']
    sources = Path(f"bioimageit-{versionName}-{tag['target']}")

    if not sources.exists():
        waitGui()

        updateLabel(f'Downloading BioImageIT {versionName}...')
        
        gui.progressBar.step(2)

        downloadSources(versionName)

        # gui.window.update_idletasks()

    return sources

class ProxyDialog:

    def __init__(self, parent):
        import tkinter as tk
        from tkinter import ttk
        top = self.top = tk.Toplevel(parent)
        top.title("Proxy Settings")
        
        self.label = ttk.Label(top, text = """Enter your proxy settings (in yaml format)""")

        self.link = tk.Label(top, text="See the conda documentation about proxy configuration for more information.", cursor="hand2")
        self.link.bind("<Button-1>", lambda e: self.browse("https://docs.conda.io/projects/conda/en/latest/user-guide/configuration/settings.html#proxy-servers-configure-conda-for-use-behind-a-proxy-server"))
        self.link.config(fg="blue")

        self.textArea = tk.Text(top, height = 5, width = 52)
        self.textArea.insert(tk.END, """#For example:
http: http://user:pass@example.com:8080
https: http://user:pass@example.com:8080
""")

        self.button = ttk.Button(top, text = "Confirm", command=self.parse)

        self.label.pack()
        self.link.pack()
        self.textArea.pack()
        self.button.pack()
        
        top.attributes('-topmost', True)
        top.update()

    def browse(self, url):
        webbrowser.open_new(url)

    def parse(self):
        import tkinter as tk
        setProxies(yaml.safe_load(self.textArea.get("1.0",tk.END)))
        
        self.top.destroy()

proxyDialogClosedEvent = threading.Event()

def openProxyDialog():
    dialog = ProxyDialog(gui.window)
    gui.window.wait_window(dialog.top)
    proxyDialogClosedEvent.set()

def getProxySettingsFromGUI():
    waitGui()
    gui.window.after(0, openProxyDialog)
    while not proxyDialogClosedEvent.is_set():
        time.sleep(0.01)
    
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
    # Add BioImageIT micromamba configurations
    condaConfigurations += [
        "micromamba/.condarc",
        "micromamba/condarc",
        "micromamba/condarc.d/",
        "micromamba/.mambarc",
    ]

    for condaConfigurationFilename in condaConfigurations:
        condaConfiguration = Path(os.path.expandvars(condaConfigurationFilename)).resolve()
        if condaConfiguration.exists():
            condaConfigurationFiles = sorted(list(condaConfiguration.glob('*.yml') + condaConfiguration.glob('*.yaml'))) if condaConfiguration.is_dir() else [condaConfiguration]
            for condaConfigurationFile in condaConfigurationFiles:
                with open(condaConfigurationFile, 'r') as f:
                    configuration = yaml.safe_load(f)
                    if 'proxy_servers' in configuration:
                        from tkinter import messagebox
                        result = condaConfigurationFilename != "micromamba/.mambarc" or messagebox.askyesno(title='Use conda proxy settings', message=f'You need to configure the proxy settings.\nBioImageIT found your conda proxy settings in {condaConfigurationFile} and will use them for this time.\nWould you like to always use your conda proxy settings?\n\nThe proxy settings are {configuration["proxy_servers"]}')
                        setProxies(configuration['proxy_servers'], save=result)
        
    # set REQUESTS_CA_BUNDLE to override the certificate bundle trusted by Requests



def tryDownloadLatestVersionOrGetProxySettingsFromGUI():
    import requests
    try:
        return downloadLatestVersion()
    except requests.exceptions.ProxyError as e:
        logging.warning(e)
        getProxySettingsFromGUI()
        try:
            return downloadLatestVersion()
        except requests.exceptions.ProxyError as e:
            from tkinter import messagebox
            logging.warning(e)
            log(str(e))
            log('Error: Unable to check BioImageIT version. Please check your proxy settings.')
            messagebox.showwarning("showwarning", "Unable to check BioImageIT version. Please check your proxy settings. Some BioImageIT features (omero connections, installation of dependencies, etc.) might not function properly.") 
            return None

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
    if guiCreated.is_set():
        gui.window.after(0, lambda: gui.progressBar.step(3))
    updateLabel('Creating BioImageIT environment...')
    with open(sources / "pyproject.toml", "rb") as f:
        projectConfiguration = tomllib.load(f)
        pythonVersion = projectConfiguration['project']['requires-python']
        pipDependencies = projectConfiguration['project']['dependencies']
        condaDependencies = [key + value for key, value in projectConfiguration['tool']['pixi']['dependencies'].items()]
    environmentManager.create(environment, dict(pip=pipDependencies, conda=condaDependencies, python=pythonVersion))

def updateVersion():
    global versionInfo

    if versionPath.exists():
        with open(versionPath, 'r') as f:
            versionInfo = json.load(f)
    else:
        versionInfo = dict(autoUpdate=True, version='unknown', proxies=None)

    sources = Path(versionInfo['version'])
    setProxies(versionInfo['proxies'] if 'proxies' in versionInfo else None)

    # If the selected version does not exist: auto update
    if versionInfo['autoUpdate']:
        try:
            newSources = tryDownloadLatestVersionOrGetProxySettingsFromConda()
            sources = newSources if newSources is not None else sources
        except Exception as e:
            logging.warning('Could not get the BioImageIT versions:')
            logging.warning(e)
            if versionInfo['version'] == 'unknown':
                sys.exit(f'The bioimageit sources could not be downloaded.')
        
    return sources

def environmentErrorDialog(condaPath, environment, title, message):
    import tkinter as tk
    from tkinter import messagebox
    result = messagebox.askyesno(title=title, message=message)
    if result:
        shutil.rmtree(condaPath / 'envs/' / environment)
    
def environmentError(condaPath, environment, title, message):
    waitGui()
    gui.window.after(0, lambda: environmentErrorDialog(condaPath, environment, title, message))

def logError(message, exception):
    logger.error(message)
    logger.error(exception)
    logger.error(exception.args)
    # logger.error(traceback.format_exc())
    for line in traceback.format_tb(exception.__traceback__):
        logger.error(line)

def launchBiit(sources):

    if sources is None or not sources.resolve().is_dir():
        message = 'Unable to find BioImageIT sources directory. Please check your Internet connection and proxy setttings and retry.'
        logging.error(message)
        log(message)
        return
    else:
        versionInfo['version'] = sources.name
        with open(versionPath, 'w') as f:
            json.dump(versionInfo, f)
        
    # Copy EnvironmentManager to avoid importing all PyFlow dependencies
    # Give it a different name so that it is imported in place of the frozen EnvironmentManager
    shutil.copyfile(sources / 'PyFlow' / 'ToolManagement' / 'EnvironmentManager.py', sources / 'NewEnvironmentManager.py')
    sys.path.append(str(sources.resolve()))
    # Imports from the Environment manager must be available now
    EnvironmentManager = import_module('NewEnvironmentManager')
    
    environmentManager = EnvironmentManager.environmentManager
    
    if platform.system() == 'Darwin' and getattr(sys, 'frozen', False):
        environmentManager.setCondaPath(getRootPath() / 'micromamba')

    arch = 'arm64' if platform.processor().lower().startswith('arm') else 'x86_64'
    environmentManager.copyMicromambaDependencies(getBundlePath() / 'data' / arch)
    environment = 'bioimageit'
    
    environmentManager.setProxies(proxies)
    condaPath, _ = environmentManager._getCondaPaths()

    if not environmentManager.environmentExists(environment):
        EnvironmentManager.attachLogHandler(log)
        try:
            createEnvironment(sources, environmentManager, environment)
        except Exception as e:
            logError('An error occured when creating the BioImageIT environment', e)
            environmentError(condaPath, environment, title='Error while creating environment', message=f"An error occured when creating the BioImageIT environment:\n{e}\n\nCheck the logs in the environment.log file for more information.\nWould you like to remove the existing environment so that it will be recreated the next time you launch BioImageIT?")
            return

    if guiCreated.is_set():
        gui.window.after(0, lambda: gui.progressBar.step(4))
    updateLabel('Launching BioImageIT...')

    executable = 'python'

    # Hack for OS X to display BioImageIT in the menu instead of python
    if platform.system() == 'Darwin':
        python = condaPath / 'envs/' / environment / 'bin' / 'python'
        pythonSymlink = sources / 'BioImageIT'
        if not pythonSymlink.exists():
            Path(pythonSymlink).symlink_to(python)
        executable = './BioImageIT'

    with environmentManager.executeCommands(environmentManager._activateConda() + [f'{environmentManager.condaBin} activate {environment}', f'cd {sources}', f'{executable} -u pyflow.py']) as process:
        
        initialized = False
        for line in process.stdout:
            log(line)
            if line.strip() == 'Initialization complete':
                initialized = True
                loading.clear()
                if gui is not None:
                    waitGui()
                    gui.window.after(0, close_window)
    if not initialized:
        environmentError(condaPath, environment, title='Initialization error', message=f"BioImageIT was not initialized properly. This might happen when the bioimageit environment was not properly created.\nWould you like to delete the BioImageIT environment ({condaPath / 'envs/' / environment})?\nJust restart BioImageIT to recreate it.") # BioImageIT will recreate it at launch time if necessary.
    
def close_window():
    """Properly close the Tkinter window."""
    global gui
    gui.window.quit()
    gui.window.destroy()
    gui.window.update()
    gui.window.update_idletasks()
    gui = None

environmentExists = Path('micromamba/envs/bioimageit').exists()
versionExists = versionPath.exists()
sourcesExist = len(list(Path.cwd().glob('bioimageit-*'))) > 0

if not (environmentExists and versionExists and sourcesExist):
    gui = Gui()

def updateVersionAndLaunchBiit():
    try:
        sources = updateVersion()
        launchBiit(sources)
    except Exception as e:
        logError('An error occured while launching BioImageIT', e)
        waitGui()
        from tkinter import messagebox
        gui.window.after(0, lambda: messagebox.showwarning("showwarning", f"An error occurred while launching BioImageIT; \n{e}\n\nCheck the logs in the initialize.log and environment.log files (in {str(getRootPath())}) for more information.") )

# Start the task in a separate thread to keep the GUI responsive
thread = threading.Thread(target=lambda: updateVersionAndLaunchBiit(), daemon=True) # deamon could be False because of thread.join() at the end
thread.start()

timeout = 5   # [seconds]
timeout_start = time.time()

# For timeout seconds: just check the createGui flag and create the gui if necessary
while time.time() < timeout_start + timeout:
    if createGui.is_set():
        gui = Gui()
        break
    time.sleep(0.1)

# If still loading after timeout seconds: create GUI
if loading.is_set() and gui is None:
    gui = Gui()

if gui is not None:
    guiCreated.set()
    gui.window.mainloop()
    gui = None

thread.join()