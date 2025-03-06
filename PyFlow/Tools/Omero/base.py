from PyFlow.ConfigManager import ConfigManager
import keyring

class OmeroBase:

    def getSettings(self):
        host = ConfigManager().getPrefsValue("PREFS", "General/OmeroHost")
        port = int(ConfigManager().getPrefsValue("PREFS", "General/OmeroPort"))
        username = ConfigManager().getPrefsValue("PREFS", "General/OmeroUsername")
        password = keyring.get_password("bioif-omero", username)
        return host, port, username, password