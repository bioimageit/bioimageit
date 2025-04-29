import argparse
import json
import pandas
import keyring
from pathlib import Path
from skimage.io import imsave
from munch import DefaultMunch

from bioimageit_omero import OmeroMetadataService

parser = argparse.ArgumentParser('NF Omero', description='Download or upload datasets from Omero.', formatter_class=argparse.ArgumentDefaultsHelpFormatter)

parser.add_argument('--omero_host', '-oh', help='Omero host', required=True)
parser.add_argument('--omero_port', '-op', help='Omero port', required=True)
parser.add_argument('--omero_user', '-ou', help='Omero username', required=True)
parser.add_argument('--omero_password', '-opd', help='Omero password', default=None)

subparsers = parser.add_subparsers(help='Choose download or upload')

parser_download = subparsers.add_parser('download', help='Download datasets')

parser_download.add_argument('--dataset_name', '-dn', help='The dataset name or id', required=True)
parser_download.add_argument('--node_name', '-nn', help='The node name', required=True)
parser_download.add_argument('--output_path', '-op', help='The output folder path', default=Path())

parser_upload = subparsers.add_parser('upload', help='Upload datasets')

parser_upload.add_argument('--dataset_name', '-dn', help='The dataset name or id', required=True)
parser_upload.add_argument('--project_name', '-pn', help='Name of the project to create', default=None)
parser_upload.add_argument('--data_frame', '-df', help='The input data frame path (.csv file)', required=True)
parser_upload.add_argument('--column_name', '-cn', help='Column name', default=None)
parser_upload.add_argument('--meta_data_columns', '-mdc', help='Name of the meta-data columns', default=None)


def initializeOmero(host, port, username, password=None):
    password = keyring.get_password("bioif-omero", username) if password is None else password
    omeroService = OmeroMetadataService(host, int(port), username, password)
    return omeroService

def getObject(omero, nameOrId, object='dataset'):
    if nameOrId is None or len(nameOrId)==0: return None
    try:
        return omero._conn.getObject(object.capitalize(), int(nameOrId))
    except ValueError:
        datasets = list(omero._conn.getObjects(object.capitalize(), attributes={"name": nameOrId}))
        if len(datasets)>1:
            raise Exception(f'There are more than 1 {object} with the name "{nameOrId}". Enter the {object} ID instead of its name to select the one you want.')
        elif len(datasets)==0:
            raise Exception(f'There no {object} with the name "{nameOrId}".')
        return datasets[0]

def getDataset(omero, nameOrId):
    return getObject(omero, nameOrId, 'dataset')

def getProject(omero, nameOrId):
    return getObject(omero, nameOrId, 'project')

def getOutputFolderPath(outputPath, nodeName):
    return Path(outputPath).resolve() / nodeName

def download(outputPath, nodeName, omero, datasetNameOrId):
    dataset = getDataset(omero, datasetNameOrId)
    if dataset is None: 
        Exception(f'Dataset {datasetNameOrId} not found.')
        return

    records = []
    for image in dataset.listChildren():
        image = omero._conn.getObject("Image", image.id)
        path = Path(outputPath).resolve() / image.getName()
        records.append(dict(name=image.getName(), author=image.getAuthor(), description=image.getDescription(), dataset=dataset.name, project=image.getProject(), id=image.getId(), path=path))
        
        image_data = omero._download_data(image, 0, 0)
        if path.exists(): continue
        path.parent.mkdir(exist_ok=True, parents=True)
        imsave(path, image_data)

    dataFrame = pandas.DataFrame.from_records(records)

    dataFrame.to_csv(Path(outputPath) / 'output_data_frame.csv', index=False)

def upload(omero, datasetName, projectName, dataFramePath, columnName, metaDataColumns):
    
    # Get or create dataset
    # Projects are not created by BioImageIT
    datasetId = None
    try:
        dataset = getDataset(omero, datasetName)
        if dataset is None:
            return
        datasetId = dataset.id
    except Exception as e:
        project = getProject(omero, projectName)
        if project is None:
            raise Exception('Neither the dataset "{datasetName}" nor the project "{projectName}" exist.')
        dataset_container = omero.create_dataset(DefaultMunch.fromDict(dict(md_uri=project.id)), datasetName)
        datasetId = dataset_container.md_uri
    
    data = pandas.read_csv(dataFramePath)

    columnName = columnName if columnName is not None else data.columns[-1]
    metaDataColumns = [mdc for mdc in json.loads(metaDataColumns) if len(mdc)>0] if metaDataColumns is not None and len(metaDataColumns)>0 else []
    for metaDataName in metaDataColumns:
        if len(metaDataName)>0 and metaDataName not in data.columns:
            raise Exception(f'The column "{metaDataName}" does not exist in the input dataframe. The columns are: {data.columns}.')
    for index, row in data.iterrows():
        experiment = DefaultMunch.fromDict(dict(raw_dataset=dict(url=datasetId)))
        name = Path(row[columnName]).name
        omero.import_data(experiment, row[columnName], name, 'amasson', 'imagetiff', key_value_pairs={md:row[md] for md in metaDataColumns if md in row})

omeroService = None
parser_download.set_defaults(func=lambda args: download(Path(args.output_path), args.node_name, omeroService, args.dataset_name))
parser_upload.set_defaults(func=lambda args: upload(omeroService, args.dataset_name, args.project_name, args.data_frame, args.column_name, args.meta_data_columns))

args = parser.parse_args()
omeroService = initializeOmero(args.omero_host, args.omero_port, args.omero_user, args.omero_password)
args.func(args)

