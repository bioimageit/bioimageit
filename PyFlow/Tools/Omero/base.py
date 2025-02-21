from PyFlow.Core.OmeroService import OmeroService

class OmeroBase:

    omero: OmeroService = OmeroService()

    def getDataset(self, args, project=None):
        return self.omero.getDataset(name=args.dataset_name, uid=args.dataset_id, project=project)
    
    def getDatasets(self, argsList, project=None):
        datasets = [self.getDataset(args, project) for args in argsList]
        return [d for d in datasets if d is not None]
