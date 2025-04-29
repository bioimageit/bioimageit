# Settings

Use the File menu (BioImageIT menu on macOS) > Preferences... to open the preferences panel.

## *General* settings

### Common

- **External code editor**: the command to run when creating or editing a tool script (with the **Create tool** button of the **Tools** tab, or when right clicking on a node and choosing **Edit tool**). By default, the VS Code integrated to BioImageIT will open, but you can specify your own editor if you prefer. This can be useful to benefit from your editor plugins and configuration.
- **Napari environment**: the path to the Napari environment to activate when opening an image. By default, BioImageIT will automatically install Napari in a dedicated environment. However, if you already have Napari installed in an environment you can specify the path to this environment for BioImageIT to use it. This is useful to benefit from the plugins you already installed in your version of Napari, and its configuration.
- **Always install Napari dependencies**: whether to install the Napari dependencies of some nodes. For example, the ExoDeepFinder nodes have a dependency to `napari-deepfinder` to visualize and edit DeepFinder images in Napari (.h5 format).
- **History depth**: the amount of actions to store in the edit history (number of possible undo/redo).
- **BioImageIT version**: choose your version of BioImageIT, or enable auto-update. The version list is automatically retrieved from the Github repository.

### Error reports

When an error occurs, BioImageIT can send an automatic report to the developers. 
Contact the developers if you want to enable this feature and help the team fix your problems as soon as possible.

### Omero

- **Host**: the URL of your Omero server
- **Port**: the port of your Omero server
- **Username**: your Omero Username
- **Password**: your Omero Password. This will be saved in a BioImageIT keyring on your system.