# Changelog

## BioImageIT v0.3.*

The latest release of BioImageIT provides a nodal programming interface which enables the creation of workflows. 
This is a major update, based on PyFlow, and also comprise an evolution of the conda environment management for better performances and simplicity.

## Project history

The BioImageIT project started in 2019. It was born from the realization that data scientists in cell biology labs and microscopy facilities spend a lot of time dealing with installing software and writing scripts to glue together software developed with various languages (e.g., C++, Java, Python…), in order to create home-made image analysis pipelines.

BioImageIT is inspired by the Galaxy project which was designed to `wrap` data processing tools using conda packaging and containers with XML description files to create data processing pipelines from any command line tools. We then realized that dealing with analysis pipelines does not match the real needs of scientists in bioimaging. Data analysis pipelines need to be interactive and connected to databases (image annotations and derivative data). Accordingly, we designed the first BioImageIT API at the end of 2019 to integrate data management with analysis. Since then, the BioImageIT project became user-focused to help a given scientist to deal with a data analysis experiment, from raw data to final result interpretation.

In 2020, we developed the graphical user interface and in 2021 we selected napari as the default viewer of BioImageIT.

The first prototype of BioImageIT was funded by France-BioImaging. Since October 2021, we obtained a France-BioImaging grant to install BioImageIT within 10 microscopy facilities. In the next step, we will enlarge the set of facilities in France and Europe.

"BioImageIT" suggests that our middleware solution dedicated to bioimaging is able to adapt to any local IT infrastructure.


