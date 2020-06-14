Contributing
------------

install
~~~~~~~

::

    $ git clone https://bitbucket.org/hoganman/cardutil.git
    $ python setup.py develop


unit test
~~~~~~~~~

::

    $ pip install -e ".[test]"
    $ pytest

coverage
~~~~~~~~

::

    $ coverage run -m pytest
    $ coverage report -m
    $ coverage html
    $ open htmlcov/index.html

docs
~~~~

::

    $ pip install -e ".[docs]"
    $ make html -C ./docs
    WINDOWS> docs\make.bat html -C docs
    $ open ./docs/build/html/index.html

.. note:: If you are updating documentation and want changes in source code reflected
          in the documentation then you must install using `python setup.py develop`.

          If you install cardutil package using pip, or don't use the develop command then
          it will use lib/site_packages code to generate.

release
~~~~~~~
.. note::
   Ensure that the source tree is clean before performing this process

.. code-block:: bash

    $ bumpversion (patch|minor|major)
    $ git push --follow-tags
