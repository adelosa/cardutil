cardutil
========
Cardutil is a python package for working with payment card systems.

* Supports python 3.6 and later.
* The core library has **zero** package dependencies.
* Low memory usage
* Documentation available at  `readthedocs <https://cardutil.readthedocs.io/en/latest/>`_


.. image:: https://img.shields.io/pypi/l/cardutil.svg

.. image:: https://img.shields.io/pypi/v/cardutil.svg

.. image:: https://img.shields.io/pypi/wheel/cardutil.svg

.. image:: https://img.shields.io/pypi/implementation/cardutil.svg

.. image:: https://img.shields.io/pypi/status/cardutil.svg

.. image:: https://img.shields.io/pypi/dm/cardutil.svg

.. image:: https://img.shields.io/pypi/pyversions/cardutil.svg

.. image:: https://readthedocs.org/projects/cardutil/badge/?version=latest
   :target: https://cardutil.readthedocs.io/en/latest/?badge=latest
   :alt: Documentation Status

Contributing
------------

install
~~~~~~~

::

    $ git clone https://bitbucket.org/hoganman/cardutil.git
    $ pip install -e ".[test]"

test
~~~~

::

    $ pytest

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

::

    $ bumpversion (patch|minor|major)
    $ git push --follow-tags

acknowledgements
----------------
The python `hexdump` library is embedded in this package. Many thank to Anatoly Techtonik <techtonik@gmail.com>
This library is a life saver for debugging issues with binary data.
Available at `Pypi:hexdump <https://pypi.org/project/hexdump/>`_.

The python `ISO8583-Module` library was originally inspired by the work of Igor V. Custodio from his
original ISO8583 parser. Available at `Pypi:ISO8583-Module <https://pypi.org/project/ISO8583-Module/>`_.

Mastercard is a registered trademark of Mastercard International Incorporated.

