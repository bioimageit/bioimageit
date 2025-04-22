# BioImageIT Community

This document is devoted to guide decisions about the future of BioImageIT, whether to accept new functionalities, change the code architecture or modify the graphical user interface (GUI), among other things. It serves as a reference point for developers and users, who are actively working on the project, and as an introduction for newcomers who want to learn more about the project’s direction, its road map for the forthcoming years and the team’s values.

## Mission statement

BioImageIT aims to be the **integration middleware to ease the interoperability between data management and data analysis software** for bio-imaging. The mission of BioImageIT is to provide a graphical user interface (GUI) that allows any scientist without coding skills to annotate and analyze datasets using various software. We hope to accomplish this by:

- Being **user-focused**. The user experience is the main objective of the BioImageIT project. GUI design, core development, software integration and documentation should be guided by the wish to make bioimage management and analysis easy for all scientists.
- Being **cross-platform**. BioImageIT should run on the most used **operating systems** (Windows, MacOS, Linux) and integrate existing tools without distinguishing their original **programming language** (C++, Java, Python…).
- **Not reinventing the wheel**. All database management systems or data analysis tools should not be developed in the core code of BioImageIT but implemented as external plugins or wrappers to connect BioImageIT with existing open source software.
- Providing **a stable API** to enable standardization of communication with data management databases and data analysis tools.
- Being **well-documented** and **accessible**. The core code and plugins have to be documented for developers and users. We expect core code and plugins to be documented with docstrings and wrappers to be documented with a tutorial that is accessible to non-data science experts using real world examples.

## About (the project and team)

BioImageIT is an open-source community-based project. Anyone interested in the project can join the community and contribute to the project. See the “Governance model” and “How to contribute” sections for more information on the project management.

### Project history

The BioImageIT project started in 2019. It was born from the realization that data scientists in cell biology labs and microscopy facilities spend a lot of time dealing with installing software and writing scripts to glue together software developed with various languages (e.g., C++, Java, Python…), in order to create home-made image analysis pipelines.

BioImageIT is inspired by the Galaxy project which was designed to `wrap` data processing tools using conda packaging and containers with XML description files to create data processing pipelines from any command line tools. We then realized that dealing with analysis pipelines does not match the real needs of scientists in bioimaging. Data analysis pipelines need to be interactive and connected to databases (image annotations and derivative data). Accordingly, we designed the first BioImageIT API at the end of 2019 to integrate data management with analysis. Since then, the BioImageIT project became user-focused to help a given scientist to deal with a data analysis experiment, from raw data to final result interpretation.

In 2020, we developed the graphical user interface and in 2021 we selected napari as the default viewer of BioImageIT.

The first prototype of BioImageIT was funded by France-BioImaging. Since October 2021, we obtained a France-BioImaging grant to install BioImageIT within 10 microscopy facilities. In the next step, we will enlarge the set of facilities in France and Europe.

"BioImageIT" suggests that our middleware solution dedicated to bioimaging is able to adapt to any local IT infrastructure.

### Road map

BioImageIT is being developed within the framework of the France BioImaging National Research Infrastructure (FBI). In the first step of deployment, this project is supported by the Research Infrastructure until end of 2023. During the next 2 years, two engineers will focus on the deployment and maintenance of BioImageIT, as well as the integration of new software. BioImageIT is being deployed within ten imaging platforms which are components of the France-BioImaging national infrastructure. A plan and schedule have been validated by the FBI steering committee for funding [here](https://france-bioimaging.org/france-bioimaging-funding-decision/fbi-internal-call-2021-technology-transfer-results/) and can be accessed through [this link](https://github.com/bioimageit/bioimageit.github.io/raw/master/src/components/AO-FBI-tech-transfer-BioImage-ITbis.pdf).

### Governance model

The purpose of this section is to formalize the governance process used by the BioImageIT project.

This is a community-based project based on consensus. Anyone interested can join the community, contribute to the project design, and participate in the decision making process. This document describes how this participation takes place.

The BioImageIT community is composed of anyone using or working on the project in any way.

### How to contribute?

A community member can become a contributor by interacting directly with the project in concrete ways, such as:

- Proposing a change to the code using GitHub pull request in any repository of the BioImageIT project:
  - [bioimageit_core pull request](https://github.com/bioimageit/bioimageit_core/pulls)
  - [bioimageit_gui pull request](https://github.com/bioimageit/bioimageit_gui/pulls)
  - [bioimageit_formats pull request](https://github.com/bioimageit/bioimageit_formats/pulls)
  - [bioimageit_viewer pull request](https://github.com/bioimageit/bioimageit_viewer/pulls)
- Reporting issues on the BioImageIT project [issue page](https://github.com/bioimageit/bioimageit/issues)
- Discussing design and new features on the [issue page](https://github.com/bioimageit/bioimageit/issues)
- Developing BioImageIT plugins ([runner plugins](https://bioimageit.github.io/bioimageit_core/tutorial_write_a_runner_plugin.html), [data plugins](https://bioimageit.github.io/bioimageit_core/tutorial_write_a_data_plugin.html))
- Developing [data processing wrappers](https://bioimageit.github.io/bioimageit_core/tutorial_wrap_a_tool.html)

### Core developers

Core developers are community members who have demonstrated a continuing commitment to the project through ongoing contributions. They have shown that they can be trusted to maintain BioImageIT with care. Becoming a core developer allows contributors to merge approved pull requests, cast votes for and against merging a pull-request, and be involved in deciding major changes to the API, and thereby making it easier to continue their project related activities. Core developers appear as organization members on the [BioImageIT GitHub organization](https://github.com/orgs/bioimageit/people). New core developers can be nominated by any existing core developer.

### Steering Council

The steering council is the group of people responsible for the BioImageIT project. It consists of core developers and users whose role is to ensure the proper direction of the project with respect to the mission statement, to make decisions concerning funding and maintenance. Together with the community they design the future of the project (roadmap).

**Current council members:**

- **Sylvain Prigent**: BioImageIT project manager – Inria  
- **Ludovic Leconte**: Engineer responsible of the pilot study – CNRS/Curie  
- **Cesar Augusto Valades-Cruz**: Engineer – Institut Curie  
- **Léo Maury**: Deployment Engineer – CNRS  
- **Jean Salamero**: Co-Head of Serpico/STED research team – CNRS/Curie site  
- **Charles Kervrann**: Head of Serpico/STED research team – Inria site

## Licensing

BioImageIT is distributed under the BSD-4-clause license, a copy is available [here](https://raw.githubusercontent.com/bioimageit/bioimageit/main/LICENSE). We notice that BioImageIT plugins or wrapped tools may use different licenses. Please refer to the repositories of each plugin and wrapper to verify their license.

## Acknowledgements

BioImageIT project is highly connected to Python imaging open-source projects like **scikit-image** and **napari**. We then acknowledge the influence of their mission and values statement on this document.
