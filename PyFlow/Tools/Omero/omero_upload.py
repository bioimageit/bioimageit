import sys
import keyring
from munch import DefaultMunch
from pathlib import Path
# from PyFlow.Core.OmeroService import BlitzGateway, DoesNotExistException
from omero.gateway import BlitzGateway
from PyFlow.Tools.Omero.base import OmeroBase
from PyFlow.Tools.Omero.omero_import import full_import
from PyFlow.ConfigManager import ConfigManager
from omero.callbacks import CmdCallbackI
import omero
from omero.rtypes import rstring, rbool
from omero.model import ChecksumAlgorithmI
from omero.model.enums import ChecksumAlgorithmSHA1160

class Tool(OmeroBase):

    name = "Omero Upload"
    description = "Upload data to an Omero database."
    categories = ['Omero']
    inputs = [
            dict(
            name = 'image',
            help = 'Image to upload',
            type = 'Path',
            required = True,
        ),
        dict(
            name = 'metadata_columns',
            help = 'Metadata columns (for example ["column 1", "column 2"])',
            type = 'str',
            default = None,
        ),
        dict(
            name = 'dataset_id',
            help = 'Dataset ID (ignored if negative)',
            type = 'int',
            default = None,
            required = True,
        )
    ]
    outputs = [
    ]
    
    # def processData2(self, args):
    #     # Get or create dataset
    #     # Projects are not created by BioImageIT
    #     # See self.description()
        
    #     try:
    #         project = self.omero.getProject(name=args.project_name, uid=args.project_id)
    #     except DoesNotExistException:
    #         project = None
        
    #     try:
    #         dataset = self.getDataset(args, project)
    #     except DoesNotExistException:
    #         if project is None or args.dataset_name is None:
    #             raise DoesNotExistException(f'Neither the dataset nor the project were found (the project must exist to create the dataset).')
    #         else:
    #             dataset = self.omero.createDataset(DefaultMunch.fromDict(dict(md_uri=project.id)), args.dataset_name)

    #     metaDataColumns = [mdc for mdc in args.metadata_columns.split(',') if len(mdc)>0] if args.metadata_columns is not None else []
    #     for metaDataName in metaDataColumns:
    #         if metaDataName not in args.idf_row.index:
    #             raise Exception(f'The column "{metaDataName}" does not exist in the input dataframe. The columns are: {args.idf_row.index}.')

    #     self.omero.importData(dataset, args.image, 'imagetiff', key_value_pairs={md:args.idf_row[md] for md in metaDataColumns if md in args.idf_row})

    # def processData3(self, args):
    #     # Get or create dataset
    #     # Projects are not created by BioImageIT
    #     # See self.description()
        
    #     # Code comes from https://gitlab.com/openmicroscopy/incubator/omero-python-importer/-/blob/master/import.py
    #     with BlitzGateway() as connection:
    #         dataset = connection.getObject('DATASET', int(args.dataset_id))

    #         images = list(dataset.listChildren())
    #         for image in images:
    #             image = connection.getObject('IMAGE', int(image.id))
    #             if image.getName() == args.image.name:
    #                 raise Exception(f'Images {args.image} already exist on dataset {dataset.getId()}.')
            
    #         # self.omero.importData(dataset, args.image, 'imagetiff', key_value_pairs={}, check_image_exists=False)

    #         format_ = 'imagetiff'
    #         # copy the image to omero
    #         image_id = 0
    #         if format_ == 'imagetiff' or format_ == 'bioformat':
    #             # image_id = self.mainImport(data_path)

    #             # rsp = self.fullImport(data_path)

    #             mrepo = self.client.getManagedRepository()
    #             # files = self.getFilesForFileSet(args.image)
    #             if Path(args.image).is_file():
    #                 files = [args.image]
    #             else:
    #                 files = [Path(args.image) / f for f in sorted(list(Path(args.image).iterdir())) if not f.startswith('.')]
    #             assert files, 'No files found: %s' % args.image

    #             # fileset = self.createFileset(files)
    #             fileset = omero.model.FilesetI()
    #             for f in files:
    #                 entry = omero.model.FilesetEntryI()
    #                 entry.setClientPath(rstring(f))
    #                 fileset.addFilesetEntry(entry)
                
    #             # settings = self.createSettings()
    #             settings = omero.grid.ImportSettings()
    #             settings.doThumbnails = rbool(True)
    #             settings.noStatsInfo = rbool(False)
    #             settings.userSpecifiedTarget = None
    #             settings.userSpecifiedName = None
    #             settings.userSpecifiedDescription = None
    #             settings.userSpecifiedAnnotationList = None
    #             settings.userSpecifiedPixels = None
    #             settings.checksumAlgorithm = ChecksumAlgorithmI()
    #             s = rstring(ChecksumAlgorithmSHA1160)
    #             settings.checksumAlgorithm.value = s

    #             proc = mrepo.importFileset(fileset, settings)
    #             try:
    #                 # return self.assertImport(proc, files, wait)
                    
    #                 # hashes = self.uploadFiles(proc, files)
    #                 ret_val = []
    #                 for i, fobj in enumerate(files):
    #                     rfs = proc.getUploader(i)
    #                     try:
    #                         with open(fobj, 'rb') as f:
    #                             print ('Uploading: %s' % fobj)
    #                             offset = 0
    #                             block = []
    #                             rfs.write(block, offset, len(block))  # Touch
    #                             while True:
    #                                 block = f.read(1000 * 1000)
    #                                 if not block:
    #                                     break
    #                                 rfs.write(block, offset, len(block))
    #                                 offset += len(block)
    #                             ret_val.append(self.client.sha1(fobj))
    #                     finally:
    #                         rfs.close()
    #                 hashes = ret_val
                    
                    
    #                 print ('Hashes:\n  %s' % '\n  '.join(hashes))
    #                 handle = proc.verifyUpload(hashes)
    #                 cb = CmdCallbackI(self.client, handle)

    #                 wait = -1

    #                 # https://github.com/openmicroscopy/openmicroscopy/blob/v5.4.9/components/blitz/src/ome/formats/importer/ImportLibrary.java#L631
    #                 if wait == 0:
    #                     cb.close(False)
    #                     return None
    #                 if wait < 0:
    #                     while not cb.block(2000):
    #                         sys.stdout.write('.')
    #                         sys.stdout.flush()
    #                     sys.stdout.write('\n')
    #                 else:
    #                     cb.loop(wait, 1000)
    #                 rsp = cb.getResponse()
    #                 if isinstance(rsp, omero.cmd.ERR):
    #                     raise Exception(rsp)
    #                 assert len(rsp.pixels) > 0
    #             finally:
    #                 proc.close()
                
    #             if rsp:
    #                 links = []
    #                 for p in rsp.pixels:
    #                     print ('Imported Image ID: %d' % p.image.id.val)
    #                     # if args.dataset:
    #                     #     link = omero.model.DatasetImageLinkI()
    #                     #     link.parent = omero.model.DatasetI(args.dataset, False)
    #                     #     link.child = omero.model.ImageI(p.image.id.val, False)
    #                     #     links.append(link)
    #                 connection.getUpdateService().saveArray(links, connection.SERVICE_OPTS)
                
                
    #             link = omero.model.DatasetImageLinkI()
    #             link.setParent(omero.model.DatasetI(datasetId, False))
    #             link.setChild(omero.model.ImageI(image_id, False))
    #             connection.getUpdateService().saveObject(link)

    #         else:
    #             raise Exception(f'OMERO service can only import tiff images (format={format_})')  

    def importImage(self, connection, args, key_value_pairs):

        dataset = connection.getObject('Dataset', args.dataset_id)
        if not dataset:
            raise Exception(f'Dataset {args.dataset_id} does not exist.')

        images = list(dataset.listChildren())
        for image in images:
            image = connection.getObject('image', int(image.id))
            if image.getName() == args.image.name:
                raise Exception(f'Images {args.image} already exist on dataset {dataset.getId()}.')
        
        print ('Importing: %s' % args.image)
        rsp = full_import(connection.c, args.image, -1)

        if rsp:
            links = []
            for p in rsp.pixels:
                print ('Imported Image ID: %d' % p.image.id.val)
                if args.dataset_id:
                    link = omero.model.DatasetImageLinkI()
                    link.parent = omero.model.DatasetI(args.dataset_id, False)
                    link.child = omero.model.ImageI(p.image.id.val, False)

                    # add key value pairs
                    keys_value_list = []
                    if len(key_value_pairs)!=0:
                        for key, value in key_value_pairs.items():
                            keys_value_list.append([key, value])
                        if len(keys_value_list) > 0:
                            map_ann = omero.gateway.MapAnnotationWrapper(connection)
                            namespace = omero.constants.metadata.NSCLIENTMAPANNOTATION
                            map_ann.setNs(namespace)
                            map_ann.setValue(keys_value_list)
                            map_ann.save()
                            p.image.linkAnnotation(map_ann)
                            # image = connection.getObject("Image", image_id)
                            # image.linkAnnotation(map_ann)
                    links.append(link)
            connection.getUpdateService().saveArray(links, connection.SERVICE_OPTS)

    def processAllData(self, argsList):
        
        host, port, username, password = self.getSettings()

        with BlitzGateway(username, password, host=host, port=port, secure=True) as connection:
            for args in argsList:

                metaDataColumns = [mdc for mdc in args.metadata_columns.split(',') if len(mdc)>0] if args.metadata_columns is not None else []
                
                if hasattr(args, 'idf_row'):
                    for metaDataName in metaDataColumns:
                        if metaDataName not in args.idf_row.index:
                            raise Exception(f'The column "{metaDataName}" does not exist in the input dataframe. The columns are: {args.idf_row.index}.')
                elif len(metaDataColumns) > 0:
                    raise Exception(f'The column "{metaDataName}" does not exist.')
                
                key_value_pairs = { md:args.idf_row[md] for md in metaDataColumns if md in args.idf_row }
                self.importImage(connection, args, key_value_pairs)


