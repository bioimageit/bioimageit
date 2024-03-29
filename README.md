# BioImageIT

## Contents

- [Overview](#overview)
- [Project Contents](#project-contents)
- [System Requirements](#system-requirements)
- [Installation Guide](#installation-guide)
- [Demo](#demo)
- [License](./LICENSE)
- [Issues](https://github.com/bioimageit/bioimageit/issues)

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

- Linux: Ubuntu 21.04 
- Mac OSX: Mac OS Catalina 10.15.11 for Mac with instel chip (we are working on an Apple made CPU version of BioImageIT)
- Windows: 10 

# Installation Guide

`BioImageIT` is an integration of existing open-source data management and analysis software. The install can then be very different depending on the user need. We provide a pre-packaged version that corresponds to the main usage, and a documentation to manually install `BioImageIT` components. 

## Pre-packaged install

- Windows 10: The installer available [here](https://github.com/bioimageit/bioimageit-install/raw/v0.1.2/windows/BioImageIT_install.exe) allows to install the latest version of `BioImageIT`. Detailed instructions are shown in this [video](https://www.youtube.com/watch?v=Z0DP0tMZPEY&t=1s) 

- Mac OS: The installation script available [here](https://github.com/bioimageit/bioimageit-install/raw/v0.1.2/mac/BioImageIT_install.dmg) allows to install the latest version of `BioImageIT`. Detailed instructions are shown in this [video](https://www.youtube.com/watch?v=R_dVrSbt1Ic) 

- Linux: The installation script available [here](https://raw.githubusercontent.com/bioimageit/bioimageit-install/v0.1.2/linux/install.sh) allows to install the latest version of `BioImageIT`. Detailed instructions are shown in this [video](https://www.youtube.com/watch?v=X3BJIfaIv14&t=1s) 

The typical install time in a desktop computer is 6 minutes (measured in a Macbook pro 2012, Intel core i7, 8Go RAM). The install time may vary depending on the internet connection speed.

## Custom install

All the instructions to install a custom version of the `BioImageIT API` are available with the `bioimageit_core` developers documentation: [https://bioimageit.github.io/bioimageit_core/install.html](https://bioimageit.github.io/bioimageit_core/install.html)

# Demo

## BioImageIT demo with the graphical interface 

### Tutorials
- [Experiment data management](https://bioimageit.github.io/bioimageit_gui/tutorial_data_management.html)
- [Design a data processing pipeline](https://bioimageit.github.io/bioimageit_gui/tutorial_data_analysis.html)

### Videos
- [Data management video](https://www.youtube.com/watch?v=PKXsEZ0fMxk&t)
- [Data management with OMERO video](https://www.youtube.com/watch?v=cDPn5OF9LRI)
- [Data processing video](https://www.youtube.com/watch?v=87JFlLHzsMU)

## BioImageIT API demo

- [Experiment data management](https://github.com/bioimageit/bioimageit-notebooks/blob/main/tutorial1-experiment.ipynb)
- [Run a processing tool](https://github.com/bioimageit/bioimageit-notebooks/blob/main/tutorial2-tool.ipynb)
- [Design a data processing pipeline](https://github.com/bioimageit/bioimageit-notebooks/blob/main/tutorial3-runner.ipynb)


## Run time

The image denoising demo with NDSafir is performed on a 3D image of size (``723 x 968 x 21`` pixels) and took 1 min 30 sec on a desktop (Intel Core i9 8 cores, 64Go RAM). 
Notice that an image processing tool is wrapped "as it is" in `BioImageIT` and not reimplemented. This means that the computation time does not depend on `BioImageIT` but on the original software implementation.
