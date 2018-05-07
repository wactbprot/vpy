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

There are different log levels available:

.. code-block:: shell
    > python se3_eval_state_doc.py --log=d
    > python se3_eval_state_doc.py --log=i
    > python se3_eval_state_doc.py --log=e

with:

* i .. INFO
* d .. DEBUG
* e .. ERROR

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
