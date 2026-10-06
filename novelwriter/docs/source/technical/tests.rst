.. _docs_technical_pytest:

*************
Running Tests
*************

.. _uv: https://docs.astral.sh/uv/

The novelWriter source code is well covered by tests. The test framework used for the development
is ``pytest`` with the use of an extension for Qt.


Simple Test Run
===============

To run the tests, you simply need to execute the following from the root of the source folder:

.. code-block:: bash

   uv run pytest

This uses uv_. See below for manually installing dependencies using ``pip``.

Since several of the tests involve opening up the novelWriter GUI, you may want to disable the GUI
for the duration of the test run. Moving your mouse while the tests are running may otherwise
interfere with the execution of some tests.

You can disable the rendering of the GUI by setting the flag ``QT_QPA_PLATFORM=offscreen``:

.. code-block:: bash

   export QT_QPA_PLATFORM=offscreen pytest


Dependencies
------------

To generate the requirements file and install dependencies using ``pip``, run:

.. code-block:: bash

   python pkgutils.py gen-req app test
   pip install -r tests/requirements.txt

This will install a couple of extra packages for coverage and test management. The minimum
requirement is ``pytest`` and ``pytest-qt``.


Advanced Options
================

Adding the flag ``-v`` to the ``pytest`` command will increase verbosity of the test execution.

You can also add coverage report generation. For instance to HTML:

.. code-block:: bash

   export QT_QPA_PLATFORM=offscreen pytest -v --cov=novelwriter --cov-report=html

Other useful report formats are ``xml``, and ``term`` for terminal output.

You can also run tests per subpackage of novelWriter with the ``-m`` command. The available
subpackage groups are ``base``, ``core``, and ``gui``. Consider for instance:

.. code-block:: bash

   export QT_QPA_PLATFORM=offscreen pytest -v --cov=novelwriter --cov-report=html -m core

This will only run the tests of the "core" package, that is, all the classes that deal with the
project data of a novelWriter project. The "gui" tests, likewise, will run the tests for the GUI
components, and the "base" tests cover the bits in-between.

You can also filter the tests with the ``-k`` switch. The following will do the same as
``-m core``:

.. code-block:: bash

   export QT_QPA_PLATFORM=offscreen pytest -v --cov=novelwriter --cov-report=html -k testCore

All tests are named in such a way that you can filter them by adding more bits of the test names.
They all start with the word "test". Then comes the group: "Core", "Base", "Dlg", "Tool", or "Gui".
Finally comes the name of the class or module, which generally corresponds to a single source code
file. For instance, running the following will run all tests for the document editor:

.. code-block:: bash

   export QT_QPA_PLATFORM=offscreen pytest -v --cov=novelwriter --cov-report=html -k testGuiEditor

To run a single test, simply add the full test name to the ``-k`` switch.
