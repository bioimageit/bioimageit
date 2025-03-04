from PyFlow.Core.OmeroService import OmeroService
from PyFlow.ConfigManager import ConfigManager
import keyring

class DoesNotExistException(Exception):
    pass

class OmeroBase:

    # omero: OmeroService = OmeroService()

    # def getDataset(self, args, project=None):
    #     return self.omero.getDataset(name=args.dataset_name, uid=args.dataset_id, project=project)
    
    # def getDatasets(self, argsList, project=None):
    #     datasets = [self.getDataset(args, project) for args in argsList]
    #     return [d for d in datasets if d is not None]

    def getSettings(self):
        host = ConfigManager().getPrefsValue("PREFS", "General/OmeroHost")
        port = int(ConfigManager().getPrefsValue("PREFS", "General/OmeroPort"))
        username = ConfigManager().getPrefsValue("PREFS", "General/OmeroUsername")
        password = keyring.get_password("bioif-omero", username)
        return host, port, username, password