# BioImageIT

## Contents

- [Overview](#overview)
- [Repo Contents](#repo-contents)
- [System Requirements](#system-requirements)
- [Installation Guide](#installation-guide)
- [Demo](#demo)
- [Results](#results)
- [License](./LICENSE)
- [Issues](https://github.com/ebridge2/lol/issues)
- [Citation](#citation)

# Overview

Open science and FAIR principles are major topics in the field of modern microscopy for biology. This is due to both new data acquisition technologies like super-resolution and light sheet microscopy that generate large datasets but also to the new data analysis methodologies such as deep learning that automate data mining with high accuracy. Nevertheless data are still rarely shared and annotated because this implies a lot of manual and tedious work and software packaging. We present BioImageIT an open source framework that integrates automation of image data management with data processing. Scientists then only need to import their data once in BioImageIT, which automatically generates and manages the metadata every time an operation is performed on the data. This accelerates the data mining process with no need any more to deal with IT integration and manual analysis and annotations required to build training sets for machine learning techniques. BioImageIT then automatically implements FAIR principles. The interest of bioImageIT is thus twofold. 

# Project Contents

- [bioimageit_core](https://github.com/bioimageit/bioimageit_core): Python `API` package for `BioImageIT` python scripting.
- [bioimageit_formats](https://github.com/bioimageit/bioimageit_formats): Python `API` to wrap reader and writer for bio-imaging data.
- [bioimageit_gui](https://github.com/bioimageit/bioimageit_formats): The `BioImageIT` software (graphical interface).
- [bioimageit_viewer](https://github.com/bioimageit/bioimageit_viewer): Python Qt integration of data viewers (ex: napari for ND images).
- [bioimageit_tools](https://github.com/bioimageit/bioimageit_tools): Repository of wrappers than integrate existing data processing tools to BioImageIT.
- [bioimageit-recipies](https://github.com/bioimageit/bioimageit-recipies): Repository of Conda recipes to integrate existing data processing tools using Conda.
- [bioimageit-toolboxes](https://github.com/bioimageit/bioimageit-toolboxes): Repository to define data processing toolboxes available in BioImageIT.
- [bioimageit-notebooks](https://github.com/bioimageit/bioimageit-notebooks): Tutorials written with Jupyter notebooks to demonstrate the BioImageIT API.
- [bioimageit-package](https://github.com/bioimageit/bioimageit-package): Scripts needed to package `BioImageIT` for Linux, MacOS and Windows.
- [bioimageit-install](https://github.com/bioimageit/bioimageit-install): Scripts to automate the `BioImageIT` install for Linux, MacOS and Windows.

# System Requirements

## Hardware Requirements

The `BioImageIT` software requires only a standard computer with enough RAM to support the operations defined by a user. For minimal performance, this will be a computer with about 4 GB of RAM. For optimal performance, we recommend a computer with the following specs:

RAM: 16+ GB  
CPU: 4+ cores, 3.3+ GHz/core

`BioImageIT` data processing algorithm are wrapped versions of existing libraries. The hardware requirements will then vary depending of the data processing pipeline defined by the user. For instance, a GPU is needed when running deep learning models.

## Software Requirements

### OS Requirements

The `BioImageIT` development version is tested on *Windows 10*, *MacOS* and *Linux* operating systems. The developmental version of the package has been tested on the following systems:

Linux: Ubuntu 21.04 
Mac OSX: Mac OS Catalina 10.15.11    
Windows: 10 

# Installation Guide

`BioImageIT` is an integration of existing open-source data management and analysis software. The install can then be very different depending on the user need. We provide a pre-packaged version that corresponds to the main usage, and a documentation to manually install `BioImageIT` components. 

## Pre-packaged install

- Windows 10: The installer available [here](https://github.com/bioimageit/bioimageit-install/blob/main/windows/BioimageIT_installer.exe) allows to install the latest version of `BioImageIT`. Detailed instructions are shown in this [video](https://www.youtube.com/watch?v=917InvFkivA) 

- Mac OS: The installation script available [here](https://github.com/bioimageit/bioimageit-install/blob/main/mac/install.sh) allows to install the latest version of `BioImageIT`. Detailed instructions are shown in this [video](https://www.youtube.com/watch?v=pMD_pjPF3Y4) 

- Linux: The installation script available [here](https://github.com/bioimageit/bioimageit-install/blob/main/linux/install.sh) allows to install the latest version of `BioImageIT`. Detailed instructions are shown in this [video](https://www.youtube.com/watch?v=ohKKkMb54k4) 

## Custom install

All the instructions to install a custom version of the `BioImageIT API` are available with the `bioimageit_core` developers documentation: [https://bioimageit.github.io/bioimageit_core/install.html](https://bioimageit.github.io/bioimageit_core/install.html)

# Demo

## BioImageIT demo with the graphical interface 

### Tutorials
- [Experiment data management](https://bioimageit.github.io/bioimageit_gui/tutorial_experiment.html)
- [Find a processing tool](https://bioimageit.github.io/bioimageit_gui/tutorial_finder.html)
- [Run a processing tool](https://bioimageit.github.io/bioimageit_gui/tutorial_runner.html)
- [Design a data processing pipeline](https://bioimageit.github.io/bioimageit_gui/tutorial_pipeline.html)

### Videos
- [Data management video](https://www.youtube.com/watch?v=Ce0hLhO3Qis)
- [Data processing video](https://www.youtube.com/watch?v=cpN4dzASNu0)

## BioImageIT API demo

- [Experiment data management](https://github.com/bioimageit/bioimageit-notebooks/blob/main/tutorial1-experiment.ipynb)
- [Run a processing tool](https://github.com/bioimageit/bioimageit-notebooks/blob/main/tutorial2-runner.ipynb)
- [Design a data processing pipeline](https://github.com/bioimageit/bioimageit-notebooks/blob/main/tutorial3-pipeline.ipynb)

# Results

# Citation


