# BioImageIT

[![Contributor Covenant](https://img.shields.io/badge/Contributor%20Covenant-2.1-4baaaa.svg)](CODE_OF_CONDUCT.md) 

A FAIR data management and image analysis framework. FAIR stands for Findable, Accessible, Interoperable and Reusable.

BioImageIT provides a node programming interface to create processing workflows from Conda packaged tools. Each tool is run in its own conda environment to avoid dependency conflicts. Data is transfered from node to node in the form of [pandas](https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.attrs.html) DataFrames.

See [the documentation](https://bioimageit.readthedocs.io/en/latest/index.html) for more information.

This project currently heavily relies on [PyFlow](https://github.com/wonderworks-software/PyFlow).

BioImageIT was made possible thanks to [omero-py](https://github.com/ome/omero-py), [pandas](https://pandas.pydata.org/), [Qt](https://doc.qt.io/), [Conda](https://conda.anaconda.org/), and many others.

BioImageIT is tested on Windows (x86_64 and arm64), macOS (x86_64 and arm64) and Linux (x86_64) operating systems. 

## Overview

Open science and FAIR principles are major topics in the field of modern microscopy for biology. This is due to both new data acquisition technologies like super-resolution and light sheet microscopy that generate large datasets but also to the new data analysis methodologies such as deep learning that automate data mining with high accuracy. Nevertheless data are still rarely shared and annotated because this implies a lot of manual and tedious work and software packaging. We present BioImageIT an open source framework that integrates automation of image data management with data processing. Scientists then only need to import their data once in BioImageIT, which automatically generates and manages the metadata every time an operation is performed on the data. This accelerates the data mining process with no need any more to deal with IT integration and manual analysis and annotations required to build training sets for machine learning techniques. BioImageIT then automatically implements FAIR principles. The interest of bioImageIT is thus twofold. 

## Mission statement

BioImageIT aims to be the **integration middleware to ease the interoperability between data management and data analysis software** for bio-imaging. The mission of BioImageIT is to provide a graphical user interface (GUI) that allows any scientist without coding skills to annotate and analyze datasets using various software. We hope to accomplish this by:

- Being **user-focused**. The user experience is the main objective of the BioImageIT project. GUI design, core development, software integration and documentation should be guided by the wish to make bioimage management and analysis easy for all scientists.
- Being **cross-platform**. BioImageIT should run on the most used **operating systems** (Windows, MacOS, Linux) and integrate existing tools without distinguishing their original **programming language** (C++, Java, Python…).
- **Not reinventing the wheel**. All database management systems or data analysis tools should not be developed in the core code of BioImageIT but implemented as external plugins or wrappers to connect BioImageIT with existing open source software.
- Providing **a stable API** to enable standardization of communication with data management databases and data analysis tools.
- Being **well-documented** and **accessible**. The core code and plugins have to be documented for developers and users. We expect core code and plugins to be documented with docstrings and wrappers to be documented with a tutorial that is accessible to non-data science experts using real world examples.

## Usage

### 1. Download BioImageIT

Download and extract the archive for your platform, and run the app or executable inside.

- [Windows x86_64](https://gitlab.inria.fr/amasson/bioimageit/-/package_files/157283/download)
- [Linux x86_64](https://gitlab.inria.fr/amasson/bioimageit/-/package_files/157283/download)
- [macOS x86_64](https://gitlab.inria.fr/amasson/bioimageit/-/package_files/157283/download), [macOS arm64](https://gitlab.inria.fr/amasson/bioimageit/-/package_files/157283/download)

This will automatically download the latest BioImageIT sources, create a Conda environment and install its dependencies, and run the BioImageIT app. 

You will be able to select the BioImageIT version to use in the preferences panel (File menu > Preferences... > BioImageIT version), and whether to auto-update or not.

### 2. Create a workflow

When BioImageIT opens for the first time, you will be asked to choose a folder path for your first workflow. Choose a location and enter a name for your workflow, BioImageIT will create the workflow folder for you and populate it with the workflow files.

### 3. Add and connect some nodes

Use the "Tools" tab to add node to your workflow by drag-n-droping any tool on the canvas.

For example, add a "List files" node and a "Cellpose_segmentation" node, and connect them by drag-n-dropping the output pin of the first to the input pin of the second.

Then, select the "List files" and use the browse button of the `folderPath` parameter in the "Properties" tab to select a folder containing cell images on your computer.

### 4. Execute the workflow

Finally, execute the workflow with the "Run unexecuted nodes" from the "Execution" tab to compute your segmentations. BioImageIT will create an environment for Cellpose, install its dependencies, and run the segmentation on the images you selected.

To go further, see [the documentation](https://bioimageit.readthedocs.io/en/latest/index.html).

## Development 

### Installation
The project uses both Conda and Pypi packages; thus [`pixi`](https://pixi.sh/latest/) is used to manage it.

Install `pixi` with one of the following commands:
- `curl -fsSL https://pixi.sh/install.sh | bash` on Linux and macOS,
- `iwr -useb https://pixi.sh/install.ps1 | iex` in PowerShell on Windows, 
- or `winget install prefix-dev.pixi` to use winget on Windows.

You can also install [the pixi autocompletion](https://pixi.sh/latest/#autocompletion) for your shell.

You might need to restart your terminal or source your shell for the changes to take effect.

`pixi` automatically creates a conda environment for the project and install the dependencies when necessary.

Run the project with `pixi python run pyflow.py`.

### Run & debug

Run and debug the project with Visual Studio Code by selecting the environment interpreter (run the `Python: Select Interpreter` command and enter the path `.pixi/envs/default/`) and click *Start Debugging* in the *Run & Debug* view.

### Tests

Run `pixi run test` to run the tests with ipython in the dev env.

Alternatively, run `python -m unittest PyFlow/Tests/Test_Tools.py` in the defaut env (run `pixi shell` to activate the default env) to execute the Tools tests.
Or use `ipython -m unittest --pdb PyFlow/Tests/Test_Tools.py` in the dev env (`pixi shell -e dev`) but ipython will not exactly break on exception when running unit tests.

### Packaging

The command `pixi run build` packages BioImageIT in the `dist/` repository. 
It runs "`pyinstaller bioimageit.spec`" in the `package` environment defined in `pyproject.toml`.
This environment only requires `requests` and `pyinstaller` with Python 3.12.

### Sign the app

Once a release is ready:
- Unsign the app with `python unsign_bioimageit.py --app path/to/BioImageIT.app` (in `Scripts/`).
- Create an archive: `tar czf bioimageit_macOS_arm64_vVERSION_NUMBER.app.tar.gz BioImage-IT.app` with the proper version number
- Upload it on Gitlab-int with `python updload_release.py -f bioimageit_macOS_arm64_vVERSION_NUMBER.app.tar.gz -pid 474 -s gitlab-int.inria.fr ` (see `Scripts/`).
- Modify the `.gitlab-ci.yml` to target the proper release file and version.
- Run the prod job tagged with codesign.inria.fr from `https://gitlab-int.inria.fr/amasson/bioimageit/-/jobs`.

### Upload a release

Once a release is signed, upload it on Gitlab with `python updload_release.py -f release_name.zip -pid 54065` (see `Scripts/`).

### Debug Modules

- Open ToolManagement/ in a new VSCode window: `code PyFlow/ToolManagement`
- Choose the proper python environment to debug (open a python file, then choose the env at the bottom right of the screen)
- Run Debug
- Copy the port number printed in the output: "Listening port 62996"
- Back in bioimageit: EnvironmentManager.launch, set Debug to True when the environment is the one to debug (for example), and past the port number
- Debug BioImageIT

### Documentation

Generate doc with `sphinx-autobuild -a website build` (website/ is the source directory, build/ the destination, `-a` disables cache).


## Steering Council

The steering council is the group of people responsible for the BioImageIT project. It consists of core developers and users whose role is to ensure the proper direction of the project with respect to the mission statement, to make decisions concerning funding and maintenance. Together with the community they design the future of the project (roadmap).

**Previous and current members:**

- **Sylvain Prigent**: BioImageIT project manager – Inria  
- **Ludovic Leconte**: Engineer responsible of the pilot study – CNRS/Curie  
- **Cesar Augusto Valades-Cruz**: Engineer – Institut Curie  
- **Léo Maury**: PHD Student – Inria
- **Jean Salamero**: Co-Head of Serpico/STED research team – CNRS/Curie site  
- **Charles Kervrann**: Head of Serpico/STED research team – Inria site
- **Arthur Masson**: BioImageIT project manager - Research Engineer – Inria

## Licensing

BioImageIT is distributed under the BSD-4-clause license, a copy is available [here](https://raw.githubusercontent.com/bioimageit/bioimageit/main/LICENSE). We notice that BioImageIT plugins or wrapped tools may use different licenses. Please refer to the repositories of each plugin and wrapper to verify their license.

## Acknowledgements

BioImageIT project is highly connected to Python imaging open-source projects like **scikit-image** and **napari**. We then acknowledge the influence of their mission and values statement on this document.
