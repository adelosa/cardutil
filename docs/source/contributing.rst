Contributing
------------

install
~~~~~~~

::

    $ git clone https://bitbucket.org/hoganman/cardutil.git
    $ pip install -e ".[test]"

unit test
~~~~~~~~~

::

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

release
~~~~~~~
.. note::
   Ensure that the source tree is clean before performing this process

.. code-block:: bash

    $ bumpversion (patch|minor|major)
    $ git push --follow-tags
