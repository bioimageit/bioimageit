from PyFlow.ConfigManager import ConfigManager
import keyring

class OmeroBase:
    
    environment = 'omero'
    dependencies = dict(python='3.10.8', conda=['omero-py==5.15.0'])
    categories = ['Omero']

    def getSettings(self):
        host = ConfigManager().getPrefsValue("PREFS", "General/OmeroHost")
        port = int(ConfigManager().getPrefsValue("PREFS", "General/OmeroPort"))
        username = ConfigManager().getPrefsValue("PREFS", "General/OmeroUsername")
        password = keyring.get_password("bioif-omero", username)
        return host, port, username, password