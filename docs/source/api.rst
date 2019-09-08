.. include:: <isonum.txt>
Developer API
=============

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

Installation
------------
::

    $ pip install cardutil

cardutil.iso8583
----------------
Parsers for ISO8583 messages.
Supports Mastercard |reg| PDS field structures.

Read an ISO8583 message returning dict::

    from cardutil import iso8583
    message_bytes = b'1144\xc0\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00164444555566667777'
    message_dict = iso8583.loads(message_bytes)

Create an ISO8583 message returning bytes::

    from cardutil import iso8583
    message_dict = {'MTI': '1144', 'DE2': '4444555566667777'}
    message_bytes = iso8583.dumps(message_dict)

.. automodule:: cardutil.iso8583
   :members:
   :undoc-members:
   :show-inheritance:

cardutil.mciipm
---------------
Mastercard |reg| IPM clearing file readers and writers

* block and unblock 1014 blocked IPM and parameter files
* process VBS format records

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

.. automodule:: cardutil.mciipm
   :members:
   :undoc-members:
   :show-inheritance:

cardutil.config
---------------

.. automodule:: cardutil.config
   :members:
   :undoc-members:
   :show-inheritance:
