import shutil
from PyFlow.invoke_in_main import inmain, inthread
from pathlib import Path
import urllib.request
import xml.etree.ElementTree as ET
from send2trash import send2trash
from blinker import Signal
from threading import Timer, Event

from PyFlow import GET_PACKAGES
from PyFlow.ToolManagement.EnvironmentManager import environmentManager
from PyFlow import getRootPath
from PyFlow.ConfigManager import ConfigManager

class UpdateManager:

	instance = None	
	versionsUpdated = Signal(list)
	versionInstalled = Signal(str)

	def __init__(self):
		self.updatingVersion = Event()
		self.updateTimer = None
		self.currentBioImageITVersion = ConfigManager().getPrefsValue("PREFS", "General/BioImageITVersion")
		self.initializeAutoUpdate()
	
	def setVersion(self, version):
		print('set version', version)
		# subprocess.run(['pip', 'download', '--no-deps', '--no-binary', ':all:', f'bioimageit=={latest_version}'])
		process = environmentManager._executeCommands(environmentManager._activateConda() + [f'micromamba run pip download --python-version 3.10.2 --no-deps --no-binary :all: bioimageit=={version}'])
		environmentManager._getOutput(process)

		bioimageitName = Path(f'bioimageit-{version}')
		shutil.unpack_archive(bioimageitName.name + '.tar.gz')
		destinationPath = getRootPath() / 'PyFlow'
		send2trash(destinationPath)
		shutil.copytree(bioimageitName / 'PyFlow', destinationPath)
		send2trash(bioimageitName)
		send2trash(bioimageitName.name + '.tar.gz')
		inmain(lambda: self.versionInstalled.send(version))
	
	def checkVersions(self):
		print('checkVersions')
		xmlFeed = urllib.request.urlopen("https://pypi.org/rss/project/bioimageit/releases.xml").read()
		root = ET.fromstring(xmlFeed)
		versions = [title.text for title in root.findall('./channel/item/title')]
		GET_PACKAGES()['PyFlowBase'].PrefsWidgets()['General'].versions = versions
		self.versionsUpdated.send(versions)
		return versions

	def autoUpdate(self):
		print('preAutoUpdate')
		if self.updatingVersion.is_set():
			return
		self.updatingVersion.set()
		
		# Parse the XML data
		print('autoUpdate')
		versions = self.checkVersions()
		latest_version = versions[0]
		if latest_version > self.currentBioImageITVersion:
			self.setVersion(latest_version)
		self.updatingVersion.clear()
		return

	def initializeAutoUpdate(self):
		print('initializeAutoUpdate')
		currentBioImageITVersion = ConfigManager().getPrefsValue("PREFS", "General/BioImageITVersion")
		if self.updateTimer is not None:
			self.updateTimer.cancel()
		if self.currentBioImageITVersion != currentBioImageITVersion:
			self.setVersion(currentBioImageITVersion)
			self.currentBioImageITVersion = currentBioImageITVersion
			return
		autoUpdate = bool(ConfigManager().getPrefsValue("PREFS", "General/AutoUpdate"))
		if not autoUpdate:
			return
		updateFrequency = int(ConfigManager().getPrefsValue("PREFS", "General/UpdateFrequency"))
		if updateFrequency > 0:
			self.updateTimer = Timer(updateFrequency, lambda: inthread(self.autoUpdate))
			self.updateTimer.start()

	@classmethod
	def get(cls):
		if cls.instance is None:
			cls.instance = UpdateManager()
		return cls.instance