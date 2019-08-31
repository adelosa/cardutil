cardutil
========
Cardutil is a python library and toolset for working with payment card messages and files.

The library has **zero** pypi module dependencies.

.. image:: https://img.shields.io/pypi/l/mciutil.svg |
.. image:: https://img.shields.io/pypi/v/mciutil.svg |
.. image:: https://img.shields.io/pypi/wheel/cardutil.svg |
.. image:: https://img.shields.io/pypi/implementation/cardutil.svg |
.. image:: https://img.shields.io/pypi/status/cardutil.svg |
.. image:: https://img.shields.io/pypi/dm/cardutil.svg |
.. image:: https://img.shields.io/pypi/pyversions/cardutil.svg


Quickstart
----------
Install
~~~~~~~
::

    $ pip install cardutil

ISO8583 messages
~~~~~~~~~~~~~~~~
Read an ISO8583 message returning dict::

    from cardutil import iso8583
    message_bytes = b'1144\xc0\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00164444555566667777'
    message_dict = iso8583.loads(message_bytes)

Create an ISO8583 message returning bytes::

    from cardutil import iso8583
    message_dict = {'MTI': '1144', 'DE2': '4444555566667777'}
    message_bytes = iso8583.dumps(message_dict)

Mastercard IPM files
~~~~~~~~~~~~~~~~~~~~
Read an IPM file::

    from cardutil import mciipm
    with open('ipm_in.bin', 'rb') as ipm_in:
        reader = mciipm.IpmReader(ipm_in)
        for record in reader:
            print(record)

Create an IPM file::

    from cardutil import mciipm
    with open('ipm_out.bin', 'wb') as ipm_out:
        writer = mciipm.IpmWriter(ipm_out)
        writer.write({'MTI': '1111', 'DE2': '9999111122221111'})
        writer.close()

Tools
-----
The following command line tools are included in the package

* `mci_ipm_extract` converts Mastercard IPM files to csv
* `mci_ipm_param_encode` changes the encoding of IPM parameter files


Contributing
------------

install
~~~~~~~

::

    $ git clone https://hoganman@bitbucket.org/hoganman/cardutil.git
    $ python setup.py develop

test
~~~~

::

    $ python setup.py test
    
docs
~~~~

::

    $ pip install -e ".[docs]"
    $ sphinx-apidoc -o ./docs/source  ./cardutil 
    $ make html -C ./docs
    $ open ./docs/build/html/index.html 


acknowledgements
----------------
The python `hexdump` library is embedded in this package. Many thank to Anatoly Techtonik <techtonik@gmail.com>
This library is a life saver for debugging issues with binary data.
Available at `Pypi:hexdump <https://pypi.org/project/hexdump/>`_.

The python `ISO8583-Module` library was originally inspired by the work of Igor V. Custodio from his
original ISO8583 parser. Available at `Pypi:ISO8583-Module <https://pypi.org/project/ISO8583-Module/>`_.


