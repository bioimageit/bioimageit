# BioImageIT

A FAIR data management and image analysis framework. FAIR stands for Findable, Accessible, Interoperable and Reusable.

BioImageIT provides a node programming interface to create processing workflows from Conda packaged tools. Each tool is run in its own conda environment to avoid dependency conflicts. Data is transfered from node to node in the form of [pandas](https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.attrs.html) DataFrames.

This project currently heavily relies on [PyFlow](https://github.com/wonderworks-software/PyFlow).

BioImageIT was made possible thanks to [omero-py](https://github.com/ome/omero-py), [pandas](https://pandas.pydata.org/), [Qt](https://doc.qt.io/), [Conda](https://conda.anaconda.org/), and many others.

## Overview

Open science and FAIR principles are major topics in the field of modern microscopy for biology. This is due to both new data acquisition technologies like super-resolution and light sheet microscopy that generate large datasets but also to the new data analysis methodologies such as deep learning that automate data mining with high accuracy. Nevertheless data are still rarely shared and annotated because this implies a lot of manual and tedious work and software packaging. We present BioImageIT an open source framework that integrates automation of image data management with data processing. Scientists then only need to import their data once in BioImageIT, which automatically generates and manages the metadata every time an operation is performed on the data. This accelerates the data mining process with no need any more to deal with IT integration and manual analysis and annotations required to build training sets for machine learning techniques. BioImageIT then automatically implements FAIR principles. The interest of bioImageIT is thus twofold. 

## Requirements

The `BioImageIT` development version is tested on *Windows 10*, *MacOS* and *Linux* operating systems. The developmental version of the package has been tested on the following systems:

- Linux: Ubuntu 21.04 (x86_64)
- Mac OSX Intel (x86_64) and Silicon (arm64)
- Windows: 10 (x86_64)

## Usage

## Installation

The project uses both Conda and Pypi packages; thus [`pixi`](https://pixi.sh/latest/) is used to manage it.

Install `pixi` with one of the following commands:
- `curl -fsSL https://pixi.sh/install.sh | bash` on Linux and macOS,
- `iwr -useb https://pixi.sh/install.ps1 | iex` in PowerShell on Windows, 
- or `winget install prefix-dev.pixi` to use winget on Windows.

You can also install [the pixi autocompletion](https://pixi.sh/latest/#autocompletion) for your shell.

You might need to restart your terminal or source your shell for the changes to take effect.

`pixi` automatically creates a conda environment for the project and install the dependencies when necessary.

Run the project with `pixi python run pyflow.py`.

## Development

It is possible to run and debug the project with Visual Studio Code by selecting the environment interpreter (run the `Python: Select Interpreter` command and enter the path `.pixi/envs/default/`), and creating a launch file (`.vscode/launch.json`) with the following configuration:

```
{
    "configurations": [
        {
            "name": "BioImageIT",
            "type": "debugpy",
            "request": "launch",
            "program": "${workspaceFolder}/pyflow.py",
            "console": "integratedTerminal",
            "justMyCode": false,
            "autoReload": {"enable": true }
        },
    ]
}
```

## Tests

Run `python -m unittest PyFlow/Tests/Test_Tools.py` in the defaut env (run `pixi shell` to activate the default env) to execute the Tools tests.
Or use `ipython -m unittest --pdb PyFlow/Tests/Test_Tools.py` in the dev env (`pixi shell -e dev`) but ipython will not exactly break on exception when running unit tests.

## Packaging

The command `pixi run build` packages BioImageIT in the `dist/` repository. 
It runs "`pyinstaller bioimageit.spec`" in the `package` environment defined in `pyproject.toml`.
This environment only requires `requests` and `pyinstaller` with Python 3.12.

## Sign the app

Once a release is ready:
- Create an archive: `tar czf bioimageit_macOS_arm64_vVERSION_NUMBER.app.tar.gz BioImage-IT.app` with the proper version number
- Upload it on Gitlab-int with `python update_release.py -f bioimageit_macOS_arm64_vVERSION_NUMBER.app.tar.gz -pid 474 -s gitlab-int.inria.fr ` (see `Scripts/`).
- Modify the `.gitlab-ci.yml` to target the proper release file and version.
- Run the prod job tagged with codesign.inria.fr from `https://gitlab-int.inria.fr/amasson/bioimageit/-/jobs`.

## Upload a release

Once a release is signed, upload it on Gitlab with `python update_release.py -f release_name.zip -p 54065` (see `Scripts/`).

## Debug Modules

- Open ToolManagement/ in a new VSCode window: `code PyFlow/ToolManagement`
- Choose the proper python environment to debug (open a python file, then choose the env at the bottom right of the screen)
- Run Debug
- Copy the port number printed in the output: "Listening port 62996"
- Back in bioimageit: EnvironmentManager.launch, set Debug to True when the environment is the one to debug (for example), and past the port number
- Debug BioImageIT

## Distribution

BioImageIT is distributed with 3 Dlls from the VC++ 2015 redistributables provided in local deployment mode as explicitly allowed by Microsoft's [Deployment in Visual C++](https://learn.microsoft.com/en-us/cpp/windows/deployment-in-visual-cpp?view=msvc-160#local-deployment) (see [Redistributing Visual C++ Files](https://learn.microsoft.com/en-us/cpp/windows/redistributing-visual-cpp-files?view=msvc-160#redistributable-files-and-licensing) and [Microsoft software license terms for Visual Studio 2017 tools, add-ons and extensions](https://learn.microsoft.com/en-us/cpp/windows/redistributing-visual-cpp-files?view=msvc-160#redistributable-files-and-licensing)).