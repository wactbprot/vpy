vpy
===

Classes and methods for vaclab measurement analysis.

virtual env
===========

.. code-block:: shell

    > python3 -m venv /path/to/vpy
    > cd /path/to/vpy
    > source bin/activate


install dependencies
====================

.. code-block:: shell
    > cd /path/to/vpy
    > source bin/activate
    > pip install -e .


docu gen
========

.. code-block:: shell

    > cd $HOME/vpy/docs
    > sphinx-apidoc -f -M -o source/ ../vpy
    > make html

run script with file
====================


.. code-block:: shell

    > python se3_fm_eval.py --file test_doc/fm_doc.json

run script with database
========================


.. code-block:: shell

    > python se3_fm_eval.py --id 'doc-id'


logging
=======

One can set different log levels:

* INFO
* DEBUG
* ERROR

in ``conf.json``.

unit tests, coverage and pre commit hook
========================================

There is a unit test stub for ``documents.py`` and ``todo.py``. Call with:

.. code-block:: shell

    > python -m unittest vpy/test_*.py

Same with the code coverage tool:

.. code-block:: shell

    > coverage run --source vpy -m unittest vpy/test_*.py
    > coverage html
    > firefox htmcovindex.html

see .. _`documentation of coverage pkg`: https://coverage.readthedocs.io/en/coverage-4.5.1/

The tests run a pre commit hook. The folder for that script is ``./hooks``.

relayServer
============

To run a script by means of the ``relayServer``
use a task like:

.. code-block:: shell

    >  {
    >    "Action": "EXECUTE",
    >    "TaskName": "eval_state",
    >    "Cmd": "cd /usr/local/share/vpy/ && source bin/activate && python se3_eval_state_doc.py -s --log=e"
    >  }
