# Contributing to BioImageIT

First off, thank you for considering contributing to BioImageIT! We're excited you're interested in helping make reproducible bioimage analysis easier and more accessible for everyone. BioImageIT aims to champion the FAIR principles (Findable, Accessible, Interoperable, Reproducible), and your contributions are vital to achieving this goal.

This document provides guidelines for contributing to the project. Please read it carefully to ensure a smooth contribution process for both you and the maintainers.

## Table of Contents

* [Ways to Contribute](#ways-to-contribute)
* [Reporting Bugs](#reporting-bugs)
* [Suggesting Enhancements](#suggesting-enhancements)
* [Your First Code Contribution](#your-first-code-contribution)
    * [Finding an Issue](#finding-an-issue)
    * [Setting Up Your Development Environment](#setting-up-your-development-environment)
    * [Making Changes](#making-changes)
    * [Testing](#testing)
* [Pull Request Process](#pull-request-process)
* [Coding Style](#coding-style)
* [Documentation](#documentation)
* [Integrating New Tools](#integrating-new-tools)
* [Communication](#communication)
* [Code of Conduct](#code-of-conduct)
<!-- * [Recognition](#recognition) -->

## Ways to Contribute

There are many ways to contribute to BioImageIT, even if you don't write code:

* **Reporting Bugs:** If you find something that's not working as expected, please let us know.
* **Suggesting Enhancements:** Have an idea for a new feature or an improvement to an existing one? We'd love to hear it.
* **Writing or Improving Documentation:** Clear documentation is crucial. Help us make ours better.
* **Submitting Code Fixes or New Features:** Contribute directly to the codebase via Pull Requests.
* **Adding or Improving Tests:** Help ensure BioImageIT is robust and reliable.
* **Integrating New Analysis Tools:** Expand the ecosystem by wrapping new tools for use within BioImageIT.
* **Reviewing Pull Requests:** Lend your expertise to review contributions from others.
* **Answering Questions:** Help other users by answering questions on the issue tracker or other communication channels.

## Reporting Bugs

Before submitting a bug report, please:

1.  **Check the existing issues:** Search the [GitHub Issues](https://github.com/bioimageit/bioimageit/issues) to see if someone has already reported the same bug.
2.  **Update to the latest version:** Ensure you are using the most recent version of BioImageIT, as the bug might have already been fixed.

If the bug persists and hasn't been reported, please open a new issue. Include as much detail as possible:

* A clear and descriptive title.
* Steps to reproduce the bug consistently.
* What you expected to happen.
* What actually happened (include error messages, logs, or screenshots if possible).
* Your environment details (Operating System, BioImageIT version, Python version, relevant package versions).

## Suggesting Enhancements

We welcome suggestions for new features and improvements! To suggest an enhancement:

1.  **Check existing issues:** Search the [GitHub Issues](https://github.com/bioimageit/bioimageit/issues) to see if a similar enhancement has already been proposed.
2.  Open a new issue detailing your suggestion.
    * Provide a clear and descriptive title.
    * Explain the enhancement and why it would be valuable to BioImageIT users.
    * Describe the proposed functionality. Include mockups or examples if helpful.
    * Outline potential implementation ideas if you have them.

## Your First Code Contribution

Ready to dive into the code? Here’s how to get started:

### Finding an Issue

* Look for issues tagged with `good first issue` or `help wanted` in the [GitHub Issues](https://github.com/bioimageit/bioimageit/issues). These are typically suitable for newcomers.
* If you want to work on an issue, please leave a comment saying so. This helps avoid duplicated effort.
* If you have an idea that doesn't have an associated issue, consider creating one first to discuss the approach with the maintainers.

### Setting Up Your Development Environment

1.  **Prerequisites:** Ensure you have Git and [Pixi](https://pixi.sh) installed.
2.  **Fork the Repository:** Click the "Fork" button on the [BioImageIT GitHub page](https://github.com/bioimageit/bioimageit/) to create your own copy.
3.  **Clone Your Fork:** `git clone https://github.com/YOUR_USERNAME/bioimageit.git`
4.  **Navigate to the Directory:** `cd bioimageit`
5.  **Set up the development environment:** This will install the development dependencies and start a new shell for development
    ```bash
    pixi shell -e dev
    ```
6.  You can now start the project with `ipython` (`ipython --pdb -- pyflow.py`)  and run tests (`ipython -m unittest --pdb PyFlow/Tests/Test_Tools.py`).

### Making Changes

1.  **Create a New Branch:** Start from the main development branch `dev`. Create a descriptive branch name:
    ```bash
    # Example for a new feature:
    git checkout -b feature/my-new-feature-name
    # Example for a bug fix:
    git checkout -b fix/issue-123-fix-description
    ```
2.  **Write Your Code:** Make your changes, focusing on the specific issue or feature.
3.  **Follow Coding Style:** Ensure your code adheres to the project's coding style guidelines (see [Coding Style](#coding-style)).
4.  **Add Tests:** Include new tests for your changes or update existing ones as needed (see [Testing](#testing)).
5.  **Update Documentation:** If your changes affect user-facing functionality or APIs, update the relevant documentation.
6.  **Commit Your Changes:** Use clear and concise commit messages. Reference the issue number if applicable (e.g., `git commit -m "feat: Add feature X (closes #123)"`).
7.  **Push to Your Fork:** `git push origin your-branch-name`

### Testing

* **How to run tests:** `ipython -m unittest --pdb PyFlow/Tests/Test_Tools.py` (with the developement environment activated with `pixi shell -e dev`)
* **Test Coverage:** For now, tests are only required for the processing tools.
* **Requirement:** All new code contributions should ideadlly include relevant tests. Bug fixes should ideally include a test that reproduces the bug.

## Pull Request Process

Once your changes are ready:

1.  **Go to your fork** on GitHub.
2.  Click the "New pull request" button.
3.  Ensure the base repository is `bioimageit/bioimageit` and the base branch is the correct development branch `dev`.
4.  Ensure the head repository is your fork and the compare branch is the one with your changes.
5.  **Fill out the Pull Request Template:** Provide a clear description of your changes, why they are needed, and link any relevant issues (e.g., "Closes #123").
6.  **Ensure Checks Pass:** Verify that tests pass successfully.
7.  **Respond to Feedback:** Maintainers or other contributors may review your PR and request changes. Be responsive to feedback and push updates to your branch as needed.
8.  **Merging:** Once approved and checks pass, a maintainer will merge your Pull Request. Congratulations!

## Coding Style

* **Python:** Please follow the code style used in the codebased (loosely based on [PEP8 formatting style](https://www.python.org/dev/peps/pep-0008/)).

## Documentation

* **Location:** `website/`
* **Format:** Markdown with Sphinx
* **Building:** `sphinx-autobuild -a website build` (with the docs environment activated, `pixi shell -e docs`)

## Integrating New Tools

BioImageIT is designed to be extensible. We encourage contributions that integrate new bioimage analysis tools.

See the [Adding and creating tools](documentation/tool_integration.md) documentation for more information.

## Communication

* **GitHub Issues:** The primary channel for bug reports, feature requests, and discussion related to specific code changes.
* [**Github Discussions**](https://github.com/bioimageit/bioimageit/discussions/landing)

## Code of Conduct

All contributors are expected to follow the [Contributor Covenant](https://www.contributor-covenant.org/) [Code of Conduct](https://github.com/bioimageit/bioimageit/blob/main/CODE_OF_CONDUCT.md). Please ensure you are familiar with it. Be respectful and constructive in all interactions.

<!-- ## Recognition

We appreciate all contributions!  -->
<!-- We acknowledge contributors in release notes, and in the [contributors.md]() website page. -->

---

Thank you again for your interest in contributing to BioImageIT!