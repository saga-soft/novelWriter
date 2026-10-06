.. _docs_technical_source:

*******************
Running from Source
*******************

.. _GitHub: https://github.com/saga-soft/novelWriter/releases
.. _PyPi: https://pypi.org/project/novelWriter/
.. _Sphinx Docs: https://www.sphinx-doc.org/
.. _uv: https://docs.astral.sh/uv/

This chapter describes various ways of running novelWriter directly from the source code, and how
to build the various components like the translation files and documentation.

.. note::

   The text below assumes the command ``python`` corresponds to a Python 3 executable. Python 2 is
   now deprecated, but on many systems the command ``python3`` may be needed instead. Likewise,
   ``pip`` may need to be replaced with ``pip3``.

Most of the custom commands for building packages of novelWriter, or building assets, are contained
in the ``pkgutils.py`` script in the root of the source code. You can list the available commands
by running:

.. code-block:: bash

   python pkgutils.py --help


.. _docs_technical_source_depend:


Dependencies
============

novelWriter has been designed to rely on as few dependencies as possible. Only the Python wrapper
for the Qt GUI libraries is required. The package for spell checking is optional, but recommended.
Everything else is handled with standard Python libraries.

The following Python packages are needed to run all features of novelWriter:

* ``PyQt6`` – needed for connecting with the Qt6 libraries.
* ``PyEnchant`` – needed for spell checking (optional).

If you want spell checking, you must install the ``PyEnchant`` package. The spell check library
must be at least 3.0 to work with Windows. On Linux, 2.0 also works fine.

If you install novelWriter from PyPi, these dependencies should be installed automatically.

You can run novelWriter directly from source with uv_ or another similar tool:

.. code-block:: bash

   uv run novelwriter

If you prefer to install dependencies using ``pip``, you must first generate the
``requirements.txt`` file:

.. code-block:: bash

   python pkgutils.py gen-req
   pip install -r requirements.txt

.. note::

   On Linux distros, the Qt library is usually split up into multiple packages. In some cases,
   secondary dependencies may not be installed automatically. For novelWriter, the library files
   for rendering the SVG icons may be left out and needs to be installed manually. This is the
   case on for instance Arch Linux.


.. _docs_technical_source_install:

Build and Install from Source
=============================

If you want to install novelWriter directly from the source available on GitHub_, you must first
build the package using the Python Packaging Authority's build tool. It can be installed with:

.. code-block:: bash

   pip install build

On Debian-based systems the tool can also be installed with:

.. code-block:: bash

   sudo apt install python3-build

With the tool installed, run the following command from the root of the novelWriter source code:

.. code-block:: bash

   python -m build --wheel

This should generate a ``.whl`` file in the ``dist/`` folder at your current location. The wheel
file can then be installed on your system. Here with example version number 2.0.7, but yours may be
different:

.. code-block:: bash

   pip install --user dist/novelWriter-2.0.7-py3-none-any.whl


.. _docs_technical_source_i18n:

Building the Translation Files
==============================

If you installed novelWriter from a package, the translation files should be pre-built and
included. If you're running novelWriter from the source code, you will need to generate the files
yourself. The files you need will be written to the ``novelwriter/assets/i18n`` folder, and will
have the ``.qm`` file extension.

You can build the ``.qm`` files with:

.. code-block:: bash

   python pkgutils.py qtlrelease

This requires that the Qt Linguist tool is installed on your system. On Ubuntu and Debian, the
needed package is called ``qttools5-dev-tools``.

.. note::

   If you want to improve novelWriter with translation files for another language, or update an
   existing translation, instructions for how to contribute can be found in the ``README.md`` file
   in the ``i18n`` folder of the source code.


.. _docs_technical_source_sample:

Building the Example Project
============================

In order to be able to create new projects from example files, you need a ``sample.zip`` file in
the ``assets`` folder of the source. This file can be built from the ``pkgutils.py`` script by
running:

.. code-block:: bash

   python pkgutils.py sample


.. _docs_technical_source_docs:

Building the Documentation
==========================

A local copy of this documentation can be generated as HTML.

If you're using ``pip``, you must first generate the ``requirements.txt`` file:

.. code-block:: bash

   python pkgutils.py gen-req docs
   pip install -r requirements.txt

The documentation can then be built from the root folder in the source code by running:

.. code-block:: bash

   make -C docs html

Or you can run directly with uv_ or similar tools:

.. code-block:: bash

   uv run make -C docs html

If successful, the documentation should be available in the ``docs/build/html`` folder and you can
open the ``index.html`` file in your browser.

You can also build a PDF manual from the documentation using the ``pkgutils.py`` script:

.. code-block:: bash

   python pkgutils.py docs-pdf en

This will build the English documentation as a PDF using LaTeX. The file will then be copied into
the assets folder and made available in the **Help** menu in novelWriter. Replace ``en`` with
``all`` to build for all languages. The Sphinx build system has a few extra dependencies when
building the PDF. Please check the `Sphinx Docs`_ for more details.
