============
Contributing
============

All contributions are most welcome and should be submitted via a pull request on GitHub.
https://github.com/adelosa/cardutil/pulls


Pull Request Guidelines
=======================

Before you submit a pull request, check that it meets these guidelines:

1. The pull request should include tests and documentation.
2. If the pull request adds functionality, the docs should be updated. Put
   your new functionality into a function with a docstring.
3. The pull request should target all supported python 3 versions. No Py2 compatibility is required
   and additional code related to py2 compatibility should be removed.

Types of Contributions
======================

Report Bugs
-----------

Report bugs at https://github.com/adelosa/cardutil/issues

If you are reporting a bug, please include:

* Your operating system name, python version and cardutil version.
* Any details about your local setup that might be helpful in troubleshooting.
* Detailed steps to reproduce the bug.

Fix Bugs
--------

Look through the issues for bugs. Anything tagged with "bug"
is open to whoever wants to implement it.

Implement Features
------------------

The project is open to new contributions that fit into the cardutil domain - that is modules and tools that
will help people who work on payment card systems.


Development commands
====================

install
-------

.. note:: It is assumed that you will fork the cardutil repository.
          Substitute your fork location.
.. warning:: Always use virtualenv, pipenv or your preferred python environment manager rather than installing
             packages into your system python installation.

::

    $ git clone https://github.com/adelosa/cardutil.git
    $ pip install -e ."[test]"


unit test
---------

::

    $ pytest

If you want to run with debug messages displayed::

    $ pytest --log-cli-level=10


coverage
--------

::

    $ coverage run -m pytest
    $ coverage report -m
    $ coverage html
    $ open htmlcov/index.html

docs
----

::

    $ pip install -e ".[docs]"
    $ make html -C ./docs
    WINDOWS> docs\make.bat html -C docs
    $ open ./docs/build/html/index.html

.. warning:: If you are updating documentation and want changes in source code reflected
          in the documentation then you must install using `python -m pip install -e ."[test]"`.

          If you don't use the `-e` option then it will use lib/site_packages code to generate.

release
-------
.. note::
   Ensure that the source tree is clean before performing this process

.. code-block:: bash

    $ bumpversion (patch|minor|major)
    $ git push --follow-tags
