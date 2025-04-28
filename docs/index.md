---
hide-toc: true
---

# BioImageIT

BioImageIT is a workflow management system designed to drastically simplify the creation, execution and duplication of data science experiments. It has sepcialized features for image analysis. Goal: Make image analysis FAIR: Findable Accessible Interoperable Reproducible.

Features :

- Interface: 
    - Nodal programming interface: easily create workflows with a simple GUI
    - Python programming interface: easily create workflows with code
- Tools & Environment management: 
    - Plenty of processing tools, each isolated in its own environment, no conflict dependencies, automatic environment creation and dependencies installation, transparent for the user
    - Easily integrate processing tools made in Java, C++, R or Python
    - Easily create custom tools, with the simple python template
    - Tool versionning (comming soon)
- Image visualization: 
    - Napari integration to display advanced imagery like 3D + time volumes
    - Automatic & parallel image thumbnails generation
- Performance: 
    - Nodes are processed in parallel, easy to run on compute clusters (coming soon)
- Data management:
    - Dataframe based data flow: data management is handled by Pandas, standard and powerful
    - Parameterize your tools based on data flow or fixed parameters
    - Omero interface: benefit from the widespread bioimage database
    - FAIR: Findable Accessible Interoperable Reproducible
- Installation and update:
    - Install with a double click, manage your versions with a dropdown



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

Generate doc with `sphinx-autobuild  docs build` (docs/ is the source directory, build/ the destination).

```{toctree}
:hidden:

download.md
documentation/getting_started.md
tutorials.md
events.md
community.md
documentation/gui.md
documentation/settings.md
documentation/api.md
documentation/nodes/list_files.md
documentation/tutorial_bonus.md
```