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

