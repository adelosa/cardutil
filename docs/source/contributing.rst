============
Contributing
============

All contributions are most welcome and should be submitted via a pull request on Bitbucket.
https://bitbucket.org/hoganman/cardutil/pull-requests


Pull Request Guidelines
=======================

Before you submit a pull request, check that it meets these guidelines:

1. The pull request should include tests and documentation.
2. If the pull request adds functionality, the docs should be updated. Put
   your new functionality into a function with a docstring.
3. The pull request should target python 3.6 and above. No Py2 compatibility is required
   and additional code related to py2 compatibility should be removed.

Types of Contributions
======================

Report Bugs
-----------

Report bugs at https://bitbucket.org/hoganman/cardutil/issues

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

    $ git clone https://bitbucket.org/hoganman/cardutil.git
    $ python setup.py develop


unit test
---------

::

    $ pip install -e ".[test]"
    $ pytest

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
          in the documentation then you must install using `python setup.py develop`.

          If you install cardutil package using pip, or don't use the develop command then
          it will use lib/site_packages code to generate.

release
-------
.. note::
   Ensure that the source tree is clean before performing this process

.. code-block:: bash

    $ bumpversion (patch|minor|major)
    $ git push --follow-tags
