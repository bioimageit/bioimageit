from omero.gateway import BlitzGateway
from PyFlow.Tools.Omero.base import OmeroBase
from PyFlow.Tools.Omero.omero_import import full_import
import omero

class Tool(OmeroBase):

    name = "Omero Upload"
    description = "Upload data to an Omero database."
    setRowInArgs = True
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
    
    def addAnnotations(self, connection, key_value_pairs, image_ids):
        if key_value_pairs is None: return
        keys_value_list = [ [key, str(value)] for key, value in key_value_pairs.items() ]
        if len(keys_value_list) > 0:
            map_ann = omero.gateway.MapAnnotationWrapper(connection)
            namespace = omero.constants.metadata.NSCLIENTMAPANNOTATION
            map_ann.setNs(namespace)
            map_ann.setValue(keys_value_list)
            map_ann.save()
            for image_id in image_ids:
                image = connection.getObject("Image", image_id)
                image.linkAnnotation(map_ann)

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
            image_ids = [p.image.id.val for p in rsp.pixels]
            links = []
            for p in rsp.pixels:
                print ('Imported Image ID: %d' % p.image.id.val)
                if args.dataset_id:
                    link = omero.model.DatasetImageLinkI()
                    # link.parent = omero.model.DatasetI(args.dataset_id, False)
                    # link.child = omero.model.ImageI(p.image.id.val, False)
                    link.setChild(omero.model.ImageI(p.image.id.val, False))
                    link.setParent(omero.model.DatasetI(args.dataset_id, False))
                    links.append(link)
            connection.getUpdateService().saveArray(links, connection.SERVICE_OPTS)

            self.addAnnotations(connection, key_value_pairs, image_ids)

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


