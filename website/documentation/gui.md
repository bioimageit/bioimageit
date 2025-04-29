# Graphical User Interface

## Tools tab

The "Tools" tab shows the tool library organized by categories, with a search bar to find specific tools by name, and a "Create tool" button.
To add a node to your workflow, drag a tool from the library and drop it on the canvas. You can also right-click on the canvas to access the tool library directly in your workflow.
To create a new tool, use the "Create tool" button (see [Creating and integrating tools](tool_integration.md)), enter a name and validate, and fill the template script which opens in the code editor.

## Canvas

The canvas enables to create nodes and connect them to form a workflow in the form of a Direct Acyclic Graph (DAG).

To connect two nodes, click the output pin of a node and drag it to the input of another node.
To disconnect nodes (delete a connexion), click near the end of the connexion (close to the input of the node), drag outward and drop. You can also right-click a connexion and click "disconnect".

Use the middle mouse button or `Alt + left mouse` button to drag the canvas. Use your mouse wheel or right mouse button to zoom in and out. This is default mapping, however, editor has it’s own input manager and most of the input can be remapped via properties window.

Left click and drag on the canvas to select multiple nodes.
You can copy and paste one or more nodes with the `Ctrl + c` & `Ctrl + v` keyboard shortcuts.

Go backward and foreward in the edit history using the `Ctrl + z` and `Ctrl + y` keyboard shortcuts.

Delete the selected node(s) with the Suppr key.

Rename a node by double-clicking its name and entering a new name. Node names must be unique. If another node with the same name exists, the name will be suffixed by a number to make it unique.

## Workflow tab

The "Workflow" tab provides features to create, modify and delete workflows.

To create a workflow, use the "Create workflow" button, choose a location and enter the name of the directory you want to use for your workflow. BioImageIT will create the directory and fill it will the workflow data, metadata and thumbnails.

!! note
    The dialog to create workflows can be a little counter-intuitive since it does not let you select an empty folder, but rather a location and name for BioImageIT to create the workflow folder.

Use the "Open workflow" button to open a workflow from an existing workflow folder if it is not known by BioImageIT yet. If you downloaded a zipped workflow, unzip it and select the resulting directory in the Open workflow dialog.

Select a workflow in the list of known workflows to open it.

The "Rename workflow" enables to rename the name of the workflow folder and update the BioImageIT interface accordingly.

The "Duplicate workflow" clones the workflow folder to the specified location.

The "Export workflow" creates a zip archive of the workflow folder for the user to share it.

The "Delete workflow" deletes the workflow folder and updates BioImageIT accordingly.

## Execution tab

The "Run unexecuted nodes" and "Run selected nodes" buttons are self-explicit. Once executed, most nodes will have data associated with them in their Data folder (typically in `path/to/workflow/Data/NodeName/`). This data corresponds to the node parameters after execution. However, when the user changes the node parameters, the nodes will turn orange to signify the data associated with the node does not correspond to the parameters anymore. The user will have to re-execute the nodes to generate the new data corresponding to the parameters.

The "Clear selected nodes" button removes data associated with the node; the node will then appear unexecuted (blue) on the canvas.

The "Set selected nodes executed" will set the selected nodes as executed even though the data associated with them does not correspond to their parameters.

## Properties tab

When the user selects a node, the "Properties" tab displays a GUI to edit the tool parameters, and an "Info" text describing the tool.

This GUI is divided in three parts: 
- Inputs for the common input parameters.
- Advanced for the advanced input parameters.
- Outputs for the name of the tool outputs. See the [outputs page][] for more information.

Each input parameter can either be constant or depend on a column of the input DataFrame of the node. A dropdown menu for each parameter enables that.


## Logger tab

The logger tab show all the BioImageIT logs, including the execution logs, the environment creation, and dependencies installation logs. This is useful to understand what is happening in BioImageIT.

## DataFrame tab

This tab shows the output DataFrame of the selected node. 

BioImageIT will generate thumbnails in the background to preview images when necessary (when opening images with "List files", or after the execution of a tool if it generated new images).

To open an image in Napari, click on an image preview. If Napari is not installed (or configured with the "General > Napari environment" setting in the Preferences panel) BioImageIT will install it in a dedicated environment.

To open multiple images, Shift + click on the image previews.
