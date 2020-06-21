==================
Command line tools
==================

The following command line tools are installed as part of the package

mastercard ipm tools
====================

``mci_ipm_to_csv``
------------------
Converts Mastercard IPM files to csv format

.. note::
   Fields defined as datetime in the ISO8583 config will be rendered in the CSV as ISO 8601 calendar date format.

.. code-block:: text

    usage: mci_ipm_to_csv [-h] [-o OUT_FILENAME] [--in-encoding IN_ENCODING]
                          [--out-encoding OUT_ENCODING]
                          [--no1014blocking] [--config-file CONFIG_FILE] [--version]
                          in_filename

    Mastercard IPM to CSV

    positional arguments:
      in_filename

    optional arguments:
      -h, --help            show this help message and exit
      -o OUT_FILENAME, --out-filename OUT_FILENAME
      --in-encoding IN_ENCODING
      --out-encoding OUT_ENCODING
      --no1014blocking
      --config-file CONFIG_FILE
                            File containing cardutil configuration - JSON format
      --version             show program's version number and exit



``mci_ipm_param_encode``
------------------------
Changes the encoding of a Mastercard IPM parameter file

.. code-block:: text

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

.. code-block:: text

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

.. note::
   **Parsing of string dates**

   Parsing of dates contained in the input CSV file will be different based on:

   * if you have the `python-dateutil library <https://dateutil.readthedocs.io/en/stable/>`_ installed -- it will use its date parser
   * if you are using python 3.7 or above - will use `datetime.fromisodate <https://docs.python.org/3/library/datetime.html#datetime.date.fromisoformat>`_ function
   * Otherwise, it will use a simple parser that will attempt 3 patterns::

      ccyy-mm-dd hh:mm:ss
      ccyy-mm-dd hh:mm
      ccyy-mm-dd

    It is recommended that if you require more than basic ISO 8601 calendar date parsing, that you install the python-dateutil module.


.. code-block:: text

    usage: mci_csv_to_ipm [-h] [-o OUT_FILENAME] [--in-encoding IN_ENCODING]
                          [--out-encoding OUT_ENCODING]
                          [--no1014blocking] [--config-file CONFIG_FILE] [--version]
                          in_filename

    CSV to Mastercard IPM

    positional arguments:
      in_filename

    optional arguments:
      -h, --help            show this help message and exit
      -o OUT_FILENAME, --out-filename OUT_FILENAME
      --in-encoding IN_ENCODING
      --out-encoding OUT_ENCODING
      --no1014blocking
      --config-file CONFIG_FILE
                            File containing cardutil configuration - JSON format
      --version             show program's version number and exit


``mci_ipm_param_to_csv``
------------------------
Extracts parameter tables from the IPM parameter extracts files

.. code-block:: text

    usage: mci_ipm_param_to_csv [-h] [-o OUT_FILENAME]
                                [--in-encoding IN_ENCODING] [--out-encoding OUT_ENCODING]
                                [--no1014blocking]
                                [--config-file CONFIG_FILE] [--version]
                                in_filename table_id

    Mastercard IPM parameter file to CSV

    positional arguments:
      in_filename           IPM Parameter file to process
      table_id              Parameter table to extract

    optional arguments:
      -h, --help            show this help message and exit
      -o OUT_FILENAME, --out-filename OUT_FILENAME
      --in-encoding IN_ENCODING
      --out-encoding OUT_ENCODING
      --no1014blocking
      --config-file CONFIG_FILE
                            File containing cardutil configuration - JSON format
      --version             show program's version number and exit


config file
===========
Command line tools can allow passing of configuration to customise the tool behavior.

There are 2 ways the custom configuration can be provided:

* set ``--config-file`` to location of file containing configuration
* set **CARDUTIL_CONFIG** environment variable to point to folder containing ``cardutil.json`` file

The format is a JSON object containing the config variable from the package config.py file.
See :py:mod:`cardutil.config`.

.. warning::
    This is an example only. Please refer to :py:mod:`cardutil.config` for full details.

.. code-block:: json

    {
        "bit_config": {
            "1": {"field_name": "Bitmap secondary", "field_type": "FIXED", "field_length": 8},
            "other bits": {},
            "127": {"field_name": "Network data", "field_type": "LLLVAR", "field_length": 0}
        },
        "output_data_elements": [
            "MTI", "DE2", "DE3", "DE4", "DE12", "DE14", "DE22", "DE23", "DE24", "DE25", "DE26",
            "DE30", "DE31", "DE33", "DE37", "DE38", "DE40", "DE41", "DE42", "DE48", "DE49",
            "DE50", "DE63", "DE71", "DE73", "DE93", "DE94", "DE95", "DE100", "PDS0023",
            "PDS0052", "PDS0122", "PDS0148", "PDS0158", "PDS0165", "DE43_NAME", "DE43_SUBURB",
            "DE43_POSTCODE", "ICC_DATA"
        ],
        "mci_parameter_tables": {
            "IP0006T1": {
                "effective_timestamp": {"start": 1, "end": 10},
                "active_inactive_code": {"start": 7, "end": 8},
                "table_id": {"start": 8, "end": 11},
                "card_program_id": {"start": 11, "end": 14},
                "data_element_id": {"start": 14, "end": 17},
                "data_element_name": {"start": 17, "end": 74},
                "data_element_format": {"start": 74, "end": 77}
            }
        }
    }
