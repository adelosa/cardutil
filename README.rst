cardutil
========
Cardutil is a python package for working with payment card systems.

* Supports python 3.6 and later.
* Pythonic interfaces
* Core library has **zero** package dependencies.
* Low memory usage
* Download from `pypi <https://pypi.org/project/cardutil/>`_
* Documentation available at  `readthedocs <https://cardutil.readthedocs.io/en/latest/>`_
* Source hosted at `Bitbucket <https://bitbucket.com/hoganman/cardutil>`_


.. image:: https://img.shields.io/pypi/l/cardutil.svg

.. image:: https://img.shields.io/pypi/v/cardutil.svg
   :target: https://pypi.org/project/cardutil
   :alt: Pypi download

.. image:: https://img.shields.io/pypi/wheel/cardutil.svg

.. image:: https://img.shields.io/pypi/implementation/cardutil.svg

.. image:: https://img.shields.io/pypi/status/cardutil.svg

.. image:: https://img.shields.io/pypi/dm/cardutil.svg

.. image:: https://img.shields.io/pypi/pyversions/cardutil.svg

.. image:: https://readthedocs.org/projects/cardutil/badge/?version=latest
   :target: https://cardutil.readthedocs.io/en/latest/?badge=latest
   :alt: Documentation Status

Features
--------
* ISO8583 message parsing
* Mastercard IPM file reader/writer/encoder
* Check digit calculator
* Visa PVV calculator

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
    $ open ./docs/build/html/index.html

release
~~~~~~~
.. note::
   Ensure that the source tree is clean before performing this process

.. code-block:: bash

    $ bumpversion (patch|minor|major)
    $ git push --follow-tags

acknowledgements
----------------
The python `hexdump` library is embedded in this package. Many thank to Anatoly Techtonik <techtonik@gmail.com>
This library is a life saver for debugging issues with binary data.
Available at `Pypi:hexdump <https://pypi.org/project/hexdump/>`_.

The iso8583 module in cardutil was inspired by the work of Igor V. Custodio from his
original ISO8583 parser. Available at `Pypi:ISO8583-Module <https://pypi.org/project/ISO8583-Module/>`_.

Mastercard is a registered trademark of Mastercard International Incorporated.
