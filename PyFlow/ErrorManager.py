import json
from mailjet_rest import Client
from PyFlow import getRootPath
from PyFlow.ConfigManager import ConfigManager
from PyFlow.Core.GraphManager import GraphManagerSingleton

class ErrorManager:
    
    reportedErrors = set()

    @staticmethod
    def getGraph():
        saveData = GraphManagerSingleton().get().serialize()
        return '\n\nGraph:\n\n' + json.dumps(saveData, indent=4)
    
    @staticmethod
    def getDataFrames():
        nodes = GraphManagerSingleton().get().getAllNodes()

        dataFrames = '\n\nDataFrames:\n\n'
        for node in nodes:
            if hasattr(node, 'getDataFrame'):
                df = node.getDataFrame()
                dataFrames += f'\n\n{node.name} DataFrame:\n\n' + df[:100].to_csv()

        return dataFrames
    
    @staticmethod
    def getLogs():
        logs = ''
        try:
            with open(getRootPath() / 'bioimageit.log', 'r') as f:
                lines = f.readlines()
                logs += '\n\nLogs:\n\n'
                logs += lines[len(lines)-500:] # Send the 100 last lines of the logs
            with open(getRootPath() / 'environment.log', 'r') as f:
                lines = f.readlines()
                logs += '\n\nEnvironment logs:\n\n'
                logs += lines[len(lines)-500:] # Send the 100 last lines of the logs
        finally:
            return logs
    
    @staticmethod
    def report(errorMessage: str):
        api_key = ConfigManager().getPrefsValue("PREFS", "General/MailAPIKey")
        api_secret = ConfigManager().getPrefsValue("PREFS", "General/MailAPISecret")
        emailAddress = ConfigManager().getPrefsValue("PREFS", "General/Email")
        if len(api_key) == 0 or len(api_secret) == 0 or len(emailAddress) == 0: return
        if errorMessage in ErrorManager.reportedErrors: return
        try:
            errorMessage += ErrorManager.getGraph()
            errorMessage += ErrorManager.getDataFrames()
            errorMessage += ErrorManager.getLogs()
        except:
            pass
        mailjet = Client(auth=(api_key, api_secret), version='v3.1')
        data = {
        'Messages': [
            {
            "From": {
                "Email": emailAddress,
                "Name": emailAddress.split('@')[0]
            },
            "To": [
                {
                "Email": "arthur.masson@inria.fr",
                "Name": "Arthur"
                }
            ],
            "Subject": f"Error report",
            "TextPart": errorMessage
            }
        ]
        }
        result = mailjet.send.create(data=data)
        print(result.status_code)
        print(result.json())
        ErrorManager.reportedErrors.add(errorMessage)
