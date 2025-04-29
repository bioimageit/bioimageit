---
hide-toc: true
---

# BioImageIT

<!-- ---


**BioImageIT: Streamline Your Bioimage Analysis & Make it FAIR**

BioImageIT is a powerful yet user-friendly workflow management system specifically designed for bioimage analysis. It radically simplifies creating, running, and reproducing complex data science experiments.

**Core Goal:** Make image analysis **FAIR** (Findable, Accessible, Interoperable, Reproducible).

**Highlights:**
*   **Easy Workflow Building:** Use a visual node-based GUI or Python scripting.
*   **Hassle-Free Tools:** Access numerous tools (Python, Java, C++, R) in isolated environments – no dependency conflicts! Auto-setup included.
*   **Advanced Visualization:** Integrated Napari viewer for complex (3D+t) images & auto-thumbnails.
*   **Robust Data Handling:** Pandas-based data flow, Omero integration.
*   **Performance:** Parallel processing built-in (cluster support coming soon).
*   **Simple Setup:** Install with a double-click.

Focus on your science, not the setup, with BioImageIT!

---


**BioImageIT: Simplifying Complex Bioimage Analysis Workflows**

BioImageIT is a workflow management system designed to drastically simplify the creation, execution, and duplication of data science experiments, with specialized features tailored for image analysis. Our primary goal is to make bioimage analysis truly **FAIR**: Findable, Accessible, Interoperable, and Reproducible.

**Key Features:**

*   **Flexible Workflow Creation:** Choose between an intuitive drag-and-drop nodal programming interface or a powerful Python API to build your analysis pipelines.
*   **Effortless Tool Management:**
    *   Leverage a rich library of processing tools, each isolated in its own environment to prevent dependency conflicts.
    *   Automatic environment creation and dependency installation – transparent for the user.
    *   Easily integrate tools written in Java, C++, R, or Python, or create custom tools using a simple template. (Tool versioning coming soon).
*   **Advanced Image Visualization:** Integrated Napari support allows viewing complex datasets like 3D + time volumes. Enjoy automatic and parallel thumbnail generation for quick previews.
*   **Performance & Scalability:** Workflows run with parallel node processing for speed. (Easy deployment on compute clusters coming soon).
*   **Robust Data Management:**
    *   Utilizes Pandas DataFrames for standardized and powerful data flow management.
    *   Parameterize tools based on data flow or fixed inputs.
    *   Includes an Omero interface for seamless integration with the popular bioimage database.
*   **Simple Installation & Updates:** Get started with a double-click installer and manage versions easily with a dropdown menu.

BioImageIT empowers you to build, run, and share reproducible bioimage analysis workflows with unprecedented ease.

--- -->

<!-- ---

**Unlock Reproducible Bioimage Analysis with BioImageIT**

Struggling with complex setups, dependency nightmares, and reproducing image analysis results? BioImageIT is here to help. It's a dedicated workflow management system that radically simplifies how you create, run, and share your bioimage analysis pipelines, championing the **FAIR** principles (Findable, Accessible, Interoperable, Reproducible).

--- -->

**BioImageIT: Streamline Your Bioimage Analysis & Make it FAIR**


BioImageIT is a workflow management system designed to drastically simplify the creation, execution, and duplication of data science experiments, with specialized features tailored for image analysis. Our primary goal is to make bioimage analysis truly **FAIR**: Findable, Accessible, Interoperable, and Reproducible.

**With BioImageIT, you can:**

*   **Build Workflows Your Way:** Whether you prefer a visual, node-based graphical interface or coding in Python, BioImageIT offers flexible options for pipeline creation.
*   **Forget Dependency Headaches:** Access a wide array of tools (Python, Java, C++, R) that run in isolated environments. BioImageIT handles the setup and installation automatically, ensuring tools work without conflicts.
*   **Integrate & Extend Easily:** Bring your own tools into the framework or create new ones quickly using our provided Python template.
*   **Visualize Complex Data:** Explore multi-dimensional images (3D+t) seamlessly with built-in Napari integration.
*   **Manage Data Effectively:** Leverage the power of Pandas for data handling within your workflows and connect directly to Omero repositories.
*   **Boost Performance:** Speed up your analysis with automatic parallel processing of workflow steps (cluster computing support coming soon).
*   **Get Started Instantly:** Install with a simple double-click and manage updates effortlessly.

BioImageIT lets you focus on scientific discovery by making powerful bioimage analysis accessible, manageable, and truly reproducible.


<!-- ---


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

--- -->

This project currently heavily relies on [PyFlow](https://github.com/wonderworks-software/PyFlow).

BioImageIT was made possible thanks to [omero-py](https://github.com/ome/omero-py), [pandas](https://pandas.pydata.org/), [Qt](https://doc.qt.io/), [Conda](https://conda.anaconda.org/), and many others.

BioImageIT is tested on *Windows*, *macOS* and *Linux* operating systems. 

## Overview

Open science and FAIR principles are major topics in the field of modern microscopy for biology. This is due to both new data acquisition technologies like super-resolution and light sheet microscopy that generate large datasets but also to the new data analysis methodologies such as deep learning that automate data mining with high accuracy. Nevertheless data are still rarely shared and annotated because this implies a lot of manual and tedious work and software packaging. We present BioImageIT an open source framework that integrates automation of image data management with data processing. Scientists then only need to import their data once in BioImageIT, which automatically generates and manages the metadata every time an operation is performed on the data. This accelerates the data mining process with no need any more to deal with IT integration and manual analysis and annotations required to build training sets for machine learning techniques. BioImageIT then automatically implements FAIR principles. The interest of bioImageIT is thus twofold. 

```{toctree}
    :hidden:

get_started.md
documentation/documentation.md
```


```{toctree}
    :hidden:
    :caption: Project

Download <download.md>
Contributing <contributing.md>
License <license.md>
changelog.md
```

<!-- Download <get_started.md:#1-download-bioimageit> -->
<!-- support.md -->


```{toctree}
    :hidden:
    :caption: Useful links

BioImageIT @ Github <https://github.com/bioimageit/bioimageit>
Issue Tracker <https://github.com/bioimageit/bioimageit/issues>
Discussions <https://github.com/bioimageit/bioimageit/discussions>
```