# Python

This repo contains a Python project that is run and tested across multiple Python versions.
This file describes expected practices for working with Python in this project, including how to manage Python versions, virtual environments, testing, and linting.

## Follow the docs

Follow [contributing.md](../../docs/source/contributing.rst).

## Python versions

The environment assumes that `pyenv` is installed and used to access different Python versions.
If `pyenv` is not installed, stop and request the user to install it for their system.
If `pyenv` fails to install a Python version, check the logs and ensure dependencies are met.

* Installed pyenv python versions can be listed with `pyenv versions`. 
* You can install new versions with `pyenv install <version>`.
* If an existing minor version (in the semantic versioning sense) of Python is not available, you can install it using `pyenv`
* If the minor version is already installed in pyenv, then you should reuse it even if it is not the latest patch version.
* Ensure that the current shell has access to the Python versions required for testing using `pyenv shell <version> <version> ...`.

## Virtual environments

Use `venv` to create virtual environments for each Python version you want to work with. This allows you to manage dependencies separately for each version.
The python venv folder should include the version number in its name, e.g., `venv-3.10`, `venv-3.11`, etc.

**IMPORTANT**: Never install into the global Python environment. Always use a virtual environment to manage dependencies for your project.

## Testing

### Pytest for testing single version

To run tests for a specific Python version, activate the corresponding virtual environment and use `pytest` to execute the tests. For example:

```bash
source venv-3.10/bin/activate
pytest
```

### Nox for testing all versions

You can run `nox` to execute tests across all specified Python versions. This will automatically create virtual environments for each version and run the tests in those environments.

### Coverage

100% code coverage is expected for all tests. Use `coverage` to measure and report on code coverage.

### Fix all warning

All warnings should be fixed. Use `pytest` with the `-W error` flag to treat warnings as errors, ensuring that they are addressed during development and testing.

## Linting

Use flake8 for linting the code.

## Temporary files

If you create a temporary file, either save it in a git ignored temp directory or ensure that it is deleted after use. Do not leave temporary files in the project directory.
