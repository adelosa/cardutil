==================
Command line tools
==================

The following command line tools are installed as part of the package

``mci_ipm_to_csv``
------------------
Converts Mastercard IPM files to csv format

.. code-block:: none

    usage: mci_ipm_to_csv [-h] [-o OUT_FILENAME] [--in-encoding IN_ENCODING]
                          [--no1014blocking] [--version]
                          in_filename

    Mastercard IPM to CSV

    positional arguments:
      in_filename

    optional arguments:
      -h, --help            show this help message and exit
      -o OUT_FILENAME, --out-filename OUT_FILENAME
      --in-encoding IN_ENCODING
      --no1014blocking
      --version             show program's version number and exit


``mci_ipm_param_encode``
------------------------
Changes the encoding of a Mastercard IPM parameter file

.. code-block:: none

    usage: mci_ipm_param_encode [-h] [-o OUT_FILENAME] [--in-encoding IN_ENCODING]
                                [--out-encoding OUT_ENCODING] [--no1014blocking]
                                [--version]
                                in_filename

    Mastercard IPM param file encoder

    positional arguments:
      in_filename

    optional arguments:
      -h, --help            show this help message and exit
      -o OUT_FILENAME, --out-filename OUT_FILENAME
      --in-encoding IN_ENCODING
      --out-encoding OUT_ENCODING
      --no1014blocking
      --version             show program's version number and exit

``mci_ipm_encode``
------------------
Changes the encoding of a Mastercard IPM file

.. code-block:: none

    usage: mci_ipm_encode [-h] [-o OUT_FILENAME] [--in-encoding IN_ENCODING]
                          [--out-encoding OUT_ENCODING] [--no1014blocking]
                          [--version]
                          in_filename

    Mastercard IPM file encoder

    positional arguments:
      in_filename

    optional arguments:
      -h, --help            show this help message and exit
      -o OUT_FILENAME, --out-filename OUT_FILENAME
      --in-encoding IN_ENCODING
      --out-encoding OUT_ENCODING
      --no1014blocking
      --version             show program's version number and exit



``mci_csv_to_ipm``
------------------
Creates a Mastercard IPM file from a csv file

.. code-block:: none

    usage: mci_csv_to_ipm [-h] [-o OUT_FILENAME] [--out-encoding OUT_ENCODING]
                          [--no1014blocking] [--version]
                          in_filename

    CSV to Mastercard IPM

    positional arguments:
      in_filename

    optional arguments:
      -h, --help            show this help message and exit
      -o OUT_FILENAME, --out-filename OUT_FILENAME
      --out-encoding OUT_ENCODING
      --no1014blocking
      --version             show program's version number and exit

Modules
-------

cardutil.cli
^^^^^^^^^^^^

.. automodule:: cardutil.cli
   :members:
   :undoc-members:
   :show-inheritance:
