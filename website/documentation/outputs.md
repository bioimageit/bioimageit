# Output templates

We often want to name the outputs of a node from its inputs. 

For example, when we segment the image `cell.tiff`, we might want to name the output `cell_segmentation.tiff`.

BioImageIT provides a template feature for this purpose. 

A few examples is worth many words:

The output `{input_image.stem}_detections{input_image.exts}` with an `input_image` equal to `cell.tiff` will become `cell_detections.tiff`. 

You can use multiple input parameters to generate your output name.

The output `{input_image.stem}_diameter_{diameter}_model_{model_type}_segmentation.png` with:
- an `input_image` parameter equal to `cell.tiff` 
- a `diameter` parameter equal to 12
- a `model_type` parameter equal to `cyto`
will become `cell_diameter_12_model_cyto_segmentation.png`.

Here are the template values you can use:
- `{input_name}` will be replaced by the value of the `input_name` parameter.
- `{input_name.stem}` will be replaced by the stem (file name without extension, see [Path.stem](https://docs.python.org/3/library/pathlib.html#pathlib.PurePath.stem)) of the `input_name` parameter (`path/to/archive.tar.gz` will become `archive.tar`).
- `{input_name.name}` will be replaced by the name of the `input_name` parameter (`path/to/archive.tar.gz` will become `archive.tar.gz`).
- `{input_name.parent.name}` will be replaced by the name of the parent of the `input_name` parameter (`/root/parentName/archive.tar.gz` will become `parentName`).
- `{input_name.ext}` will be replaced by the last file extension of the `input_name` parameter (`path/to/cell.png` will become `.png` and `path/to/mri.nii.gz` will become `.gz`).
- `{input_name.exts}` will be replaced by the extensions of the `input_name` parameter (`path/to/cell.png` will become `.png` and `path/to/mri.nii.gz` will become `.nii.gz`). Be aware that the name will be split wherever there is a dot, so the output `{input_name.stem}_segmentation{exts}` with the parameter value `cell_diameter_1.5_cyto.png` (stem is `cell_diameter_1.5_cyto` and exts is `.5_cyto.png`) will become `cell_diameter_1.5_cyto_segmentation.5_cyto.png`.

In addition, you can use the following variables:
- `[index]` will be replaced by the index of the current row.
- `[node_folder]` will be replace by the absulte path of the node folder (for example `path/to/workflow/Data/NodeName` with a workflow located at `path/to/workflow` and a node named `NodeName`).
- `[workflow_folder]` will be replace by the absulte path of the `Data/` folder in the workflow folder (for example `path/to/workflow/Data/` with a workflow located at `path/to/workflow`).
- `[ext]` will be replaced by the parameter extension defined in the tool definition, if it exists (otherwise `[ext]` will not be replaced).

Note that `[node_folder]` and `[workflow_folder]` can only be used at the beginning of your outputs since they are absolute paths.

This is useful when you need a custom folder structure for your worklfow.
For example, in the "ExoDeepFinder Training" workflow, the training dataset is organized as follow:
```
path/to/ExoDeepFinder Training/Data/dataset
├── Movie1
│   ├── detector_segmentation.h5
│   ├── expert_annotation.xml
│   ├── expert_segmentation.h5
│   ├── merged_annotation.xml
│   ├── merged_segmentation.h5
│   ├── movie.h5
│   └── tiff/
├── Movie2
│   ├── detector_segmentation.h5
│   ├── expert_annotation.xml
│   ├── ...
├── ...
```
Each node generate an output in each movie folder (the first node converts the `tiff/` folder into a `movie.h5` file, the next node generate the `detector_segmentation.h5`, the next node generates the `merged_segmentation.h5`, etc.).

In this example, the detector node have the following output value `[workflow_folder]/dataset/{movie_folder.name}/detector_segmentation.h5` which will become `path/to/ExoDeepFinder Training/Data/dataset/Movie1/detector_segmentation.h5` for the movie `Movie1`.

Finally, `(columnName)` will be replaced by the value of the column at the current row. For example `mask_(label1).png` will become `mask_52.png` when the column `label1` of the input DataFrame equals 52 at the current row. This is useful when the input parameters of the node is not related with the column you want to use for the name of your output.

Note that if your output value is relative (does not start with `/`), it will be prefixed with `[node_folder]/` so that the final path points inside the node output folder.

It is important that the outputs of a node do not end up with the same path (otherwise the last output will overwrite the previous one). For this reason, BioImageIT adds the `[index]` suffix on the output if it finds a collision (two outputs with the same path). The `[index]` suffix is added before the last file extension; and it will be replaced by the index of the row.