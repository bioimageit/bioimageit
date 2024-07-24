from pathlib import Path
import locale
import keyring
import numpy as np
import platform
from PIL import Image
from omero.gateway import BlitzGateway, DatasetWrapper, ProjectWrapper
import omero
import Ice
from omero_version import omero_version
from omero.model import NamedValue
from omero.rtypes import rstring, rbool
from omero.model import ChecksumAlgorithmI
from omero.callbacks import CmdCallbackI
from omero.model.enums import ChecksumAlgorithmSHA1160
from PyFlow.Core.Common import *
from PyFlow.ConfigManager import ConfigManager
# from bioimageit_omero import OmeroMetadataService
# from omero.cli import BaseControl, CLI

class DoesNotExistException(Exception):
    pass

# @SingletonDecorator
class OmeroService(object):
    """Holds the Omero service."""

    def __init__(self):
        self.connection = None

    def getSettings(self):
        host = ConfigManager().getPrefsValue("PREFS", "General/OmeroHost")
        port = int(ConfigManager().getPrefsValue("PREFS", "General/OmeroPort"))
        username = ConfigManager().getPrefsValue("PREFS", "General/OmeroUsername")
        return host, port, username
    
    def initializeOmero(self):
        host, port, username = self.getSettings()
        password = keyring.get_password("bioif-omero", username)

        # self.client = omero.client(host, port)

        # self.omeroService = OmeroMetadataService(host, port, username, password)

        # self.client.createSession(username, password)
        # self.connection = BlitzGateway(username, password, host=host, port=port, client_obj=self.client, secure=True)
        self.connection = BlitzGateway(username, password, host=host, port=port, secure=True)
        self.client = self.connection.c
        self.connection.connect()
    
    def getConnection(self):
        if self.connection is None or not self.connection.isConnected():
            self.initializeOmero()
        return self.connection
    
    def reset(self):
        if self.connection is not None:
            self.connection.close()
        return self.getConnection()
    
    # project = conn.getObject("Project", attributes={"name": project_name})
    # dataset = conn.getObject("Dataset", opts={"project": project.id}, attributes={"name": dataset_name})
    
    def getObjectNoReconnect(self, object:str, name:str|None=None, uid:int|None=None, opts:dict=None):
        connection = self.getConnection()
        if uid is not None:
            return connection.getObject(object.capitalize(), int(uid))
        elif name is not None and len(name)>0:
            datasets = list(connection.getObjects(object.capitalize(), attributes={"name": name}, opts=opts))
            if len(datasets)>1:
                raise Exception(f'There are more than 1 {object} with the name "{name}". Enter the {object} ID instead of its name to select the one you want.')
            elif len(datasets)==0:
                raise DoesNotExistException(f'There no {object} with the name "{name}".')
            return datasets[0]
        else:
            raise DoesNotExistException(f'Provide a name or an id to retrieve an object.')

    def getObject(self, object:str, name:str|None=None, uid:int|None=None, opts:dict=None):
        try:
            return self.getObjectNoReconnect(object, name, uid, opts)
        except Ice.ConnectionLostException as e:
            self.reset()
            return self.getObjectNoReconnect(object, name, uid, opts)
        # return self.getObjectNoReconnect(object, name, uid, opts)
    
    def getImage(self, name:str|None=None, uid:int|None=None):
        return self.getObject('image', name, uid)

    def getDataset(self, name:str|None=None, uid:int|None=None, project=None):
        return self.getObject('dataset', name, uid, opts=dict(project=project.id) if project is not None else None)
    
    def getProject(self, name:str|None=None, uid:int|None=None):
        return self.getObject('project', name, uid)
    
    def downloadImageData(self, img, c=0, t=0):
        """Get one channel and one time point of a data
        
        Parameters
        ----------
        img: omero.gateway.ImageWrapper
            Omero image wrapper
        c: int
            Channel index
        t: int
            Time point index    

        """
        size_z = img.getSizeZ()
        # get all planes we need in a single generator
        zct_list = [(z, c, t) for z in range(size_z)]
        pixels = img.getPrimaryPixels()
        plane_gen = pixels.getPlanes(zct_list)

        if size_z == 1:
            return np.array(next(plane_gen))
        else:
            z_stack = []
            for z in range(size_z):
                # print("plane c:%s, t:%s, z:%s" % (c, t, z))
                z_stack.append(next(plane_gen))
            return np.array(z_stack)

    def downloadImage(self, destination_file_path, md_uri=None, omero_image=None):
        if destination_file_path is None:
            raise Exception('Output file must be valid')
        omero_image = self.getObject("Image", md_uri) if omero_image is None else omero_image
        image_data = self.downloadImageData(omero_image)
        # imsave(destination_file_uri, image_data)                  # could use scikit-image but Pillow is lighter
        Image.fromarray(image_data).save(destination_file_path)
        return omero_image
    
    def createDataset(self, experiment, dataset_name):
        """Create a processed dataset in an experiment

        Parameters
        ----------
        experiment: Experiment
            Object containing the experiment metadata
        dataset_name: str
            Name of the dataset

        Returns
        -------
        Dataset object containing the new dataset metadata

        """
        connection = self.getConnection()
        try:
            # create dataset
            new_dataset = DatasetWrapper(connection, omero.model.DatasetI())
            new_dataset.setName(dataset_name)
            new_dataset.save()
            dataset_obj = new_dataset._obj
            
            # link dataset to project
            link = omero.model.ProjectDatasetLinkI()
            link.setChild(omero.model.DatasetI(dataset_obj.id.val, False))
            link.setParent(omero.model.ProjectI(experiment.md_uri, False))
            connection.getUpdateService().saveObject(link)

            return new_dataset
        finally:
            pass
            #self._omero_close()
    
    def createSettings(self):
        """Create ImportSettings and set some values."""
        settings = omero.grid.ImportSettings()
        settings.doThumbnails = rbool(True)
        settings.noStatsInfo = rbool(False)
        settings.userSpecifiedTarget = None
        settings.userSpecifiedName = None
        settings.userSpecifiedDescription = None
        settings.userSpecifiedAnnotationList = None
        settings.userSpecifiedPixels = None
        settings.checksumAlgorithm = ChecksumAlgorithmI()
        s = rstring(ChecksumAlgorithmSHA1160)
        settings.checksumAlgorithm.value = s
        return settings
    
    def getFilesForFileSet(self, fs_path):
        if Path(fs_path).is_file():
            files = [fs_path]
        else:
            files = [Path(fs_path) / f for f in sorted(list(Path(fs_path).iterdir())) if not f.startswith('.')]
        return files

    def createFileset(self, files):
        """Create a new Fileset from local files."""
        fileset = omero.model.FilesetI()
        for f in files:
            entry = omero.model.FilesetEntryI()
            entry.setClientPath(rstring(f))
            fileset.addFilesetEntry(entry)

        # Fill version info
        system, node, release, version, machine, processor = platform.uname()

        client_version_info = [
            NamedValue('omero.version', omero_version),
            NamedValue('os.name', system),
            NamedValue('os.version', release),
            NamedValue('os.architecture', machine)
        ]
        try:
            client_version_info.append(
                NamedValue('locale', locale.getdefaultlocale()[0]))
        except:
            pass

        upload = omero.model.UploadJobI()
        upload.setVersionInfo(client_version_info)
        fileset.linkJob(upload)
        return fileset
            
    def uploadFiles(self, proc, files):
        """Upload files to OMERO from local filesystem."""
        ret_val = []
        for i, fobj in enumerate(files):
            rfs = proc.getUploader(i)
            try:
                with open(fobj, 'rb') as f:
                    print ('Uploading: %s' % fobj)
                    offset = 0
                    block = []
                    rfs.write(block, offset, len(block))  # Touch
                    while True:
                        block = f.read(1000 * 1000)
                        if not block:
                            break
                        rfs.write(block, offset, len(block))
                        offset += len(block)
                    ret_val.append(self.client.sha1(fobj))
            finally:
                rfs.close()
        return ret_val
    
    def assertImport(self, proc, files, wait):
        """Wait and check that we imported an image."""
        hashes = self.uploadFiles(proc, files)
        print ('Hashes:\n  %s' % '\n  '.join(hashes))
        handle = proc.verifyUpload(hashes)
        cb = CmdCallbackI(self.client, handle)

        # https://github.com/openmicroscopy/openmicroscopy/blob/v5.4.9/components/blitz/src/ome/formats/importer/ImportLibrary.java#L631
        if wait == 0:
            cb.close(False)
            return None
        if wait < 0:
            while not cb.block(2000):
                sys.stdout.write('.')
                sys.stdout.flush()
            sys.stdout.write('\n')
        else:
            cb.loop(wait, 1000)
        rsp = cb.getResponse()
        if isinstance(rsp, omero.cmd.ERR):
            raise Exception(rsp)
        assert len(rsp.pixels) > 0
        return rsp
    
    def fullImport(self, fs_path, wait=-1):
        """Re-usable method for a basic import."""
        mrepo = self.client.getManagedRepository()
        files = self.getFilesForFileSet(fs_path)
        assert files, 'No files found: %s' % fs_path

        fileset = self.createFileset(files)
        settings = self.createSettings()

        proc = mrepo.importFileset(fileset, settings)
        try:
            return self.assertImport(proc, files, wait)
        finally:
            proc.close()
    
    def mainImport(self, data_path):

        connection = self.getConnection()

        print ('Importing: %s' % data_path)
        rsp = self.fullImport(data_path)
        if rsp:
            links = []
            for p in rsp.pixels:
                print ('Imported Image ID: %d' % p.image.id.val)
                # if args.dataset:
                #     link = omero.model.DatasetImageLinkI()
                #     link.parent = omero.model.DatasetI(args.dataset, False)
                #     link.child = omero.model.ImageI(p.image.id.val, False)
                #     links.append(link)
            connection.getUpdateService().saveArray(links, connection.SERVICE_OPTS)
        
        return p.image.id.val

    # Check if image is in dataset
    def imageInDataset(self, dataset, imagePath):
        # if dataset was just created (returned by createDataset()), _oid is not set: there are no images in the dataset
        if not hasattr(dataset, '_oid'): return False
        for image in dataset.listChildren():
            omero_image = self.getImage(uid=image.id)
            if omero_image.getName() == imagePath.name:
                return True
        return False
    
    def importData(self, dataset, data_path, format_, key_value_pairs=dict(), check_image_exists=True):
        """import one data to the experiment

        The data is imported to the raw dataset

        Parameters
        ----------
        dataset: Omero Dataset
            The Omero dataset object
        data_path: str
            Path of the accessible data on your local computer
        name: str
            Name of the data
        author: str
            Person who created the data
        format_: str
            Format of the data (ex: tif)
        date: str
            Date when the data where created
        key_value_pairs: dict
            Dictionary {key:value, key:value} to annotate files
        check_image_exists: bool
            Check if the image exists in the dataset, raise an Exception if it already exists
        Returns
        -------
        class RawData containing the metadata

        """
        connection = self.getConnection()

        datasetId = dataset.getId()

        if check_image_exists and self.imageInDataset(dataset, data_path):
            raise Exception(f'Image {data_path} already exists on dataset {datasetId}.')
        
        # copy the image to omero
        image_id = 0
        if format_ == 'imagetiff' or format_ == 'bioformat':
            image_id = self.mainImport(data_path)
            link = omero.model.DatasetImageLinkI()
            link.setParent(omero.model.DatasetI(datasetId, False))
            link.setChild(omero.model.ImageI(image_id, False))
            connection.getUpdateService().saveObject(link)

        else:
            raise Exception(f'OMERO service can only import tiff images (format={format_})')  

        # add key value pairs
        keys_value_list = []
        print(type(key_value_pairs))
        print(key_value_pairs)
        if len(key_value_pairs)!=0:
            for key, value in key_value_pairs.items():
                keys_value_list.append([key, value])
            if len(keys_value_list) > 0:
                map_ann = omero.gateway.MapAnnotationWrapper(connection)
                namespace = omero.constants.metadata.NSCLIENTMAPANNOTATION
                map_ann.setNs(namespace)
                map_ann.setValue(keys_value_list)
                map_ann.save()
                image = connection.getObject("Image", image_id)
                image.linkAnnotation(map_ann)      

        return
