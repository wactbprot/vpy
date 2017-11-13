vpy
===

Classes and methods for vaclab measurement analysis.

virtual env
===========

.. code-block:: shell

    > python3 -m venv /path/to/vpy
    > cd /path/to/vpy
    > source bin/activate

docu gen
========

.. code-block:: shell

    > cd $HOME/vpy
    > sphinx-apidoc -f -M -o docs/source/ vpy
    > 
    > make html

run script with file
====================


.. code-block:: shell

    > python se3_fm_eval.py --file test_doc/fm_doc.json

run script with database
========================


.. code-block:: shell

    > python se3_fm_eval.py --id 'doc-id'
