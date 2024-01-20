========
cardutil
========
Cardutil is a python package for working with payment card systems including
command line tools for working with Mastercard IPM files.

.. image:: https://img.shields.io/pypi/l/cardutil.svg
        :target: https://pypi.org/project/cardutil
        :alt: License

.. image:: https://img.shields.io/pypi/v/cardutil.svg
        :target: https://pypi.org/project/cardutil
        :alt: Version

.. image:: https://img.shields.io/pypi/wheel/cardutil.svg
        :target: https://pypi.org/project/cardutil
        :alt: Wheel

.. image:: https://img.shields.io/pypi/implementation/cardutil.svg
        :target: https://pypi.org/project/cardutil
        :alt: Implementation

.. image:: https://img.shields.io/github/issues/adelosa/cardutil
        :target: https://github.com/adelosa/cardutil/issues
        :alt: Status

.. image:: https://img.shields.io/pypi/dm/cardutil.svg
        :target: https://pypi.org/project/cardutil
        :alt: Downloads per month

.. image:: https://img.shields.io/pypi/pyversions/cardutil.svg
        :target: https://pypi.org/project/cardutil
        :alt: Python versions

.. image:: https://img.shields.io/github/actions/workflow/status/adelosa/cardutil/docs.yml?event=push&label=doc%20build
        :target: https://adelosa.github.io/cardutil
        :alt: doc build

.. image:: https://snyk.io/advisor/python/cardutil/badge.svg
        :target: https://snyk.io/advisor/python/cardutil
        :alt: snyk package health


Features
========
* ISO8583 message parsing
* Mastercard IPM file reader/writer/encoder
* Check digit calculator
* Encrypted pin block generator
* Visa PVV calculator
* Permissive license (MIT)

Installing
==========
Install and update using pip::

    pip install -U cardutil


Information
===========
* Works with all supported Python versions.
* Pythonic programmer interfaces
* Core library has **zero** package dependencies.
* Low memory usage
* Download from `pypi <https://pypi.org/project/cardutil/>`_
* Documentation available at `Read The Docs <https://cardutil.readthedocs.io/en/latest/>`_ and `GitHub Pages <https://adelosa.github.io/cardutil>`_
* Source hosted at `GitHub <https://github.com/adelosa/cardutil>`_

Acknowledgements
================
The python `hexdump` library is embedded in this package. Many thank to Anatoly Techtonik <techtonik@gmail.com>
This library is a life saver for debugging issues with binary data.
Available at `Pypi:hexdump <https://pypi.org/project/hexdump/>`_.

The iso8583 module in cardutil was inspired by the work of Igor V. Custodio from his
original ISO8583 parser. Available at `Pypi:ISO8583-Module <https://pypi.org/project/ISO8583-Module/>`_.

Mastercard is a registered trademark of Mastercard International Incorporated.
