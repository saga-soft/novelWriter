.. _docs_more_project_formats:

**********************
Project Format Changes
**********************

Most of the changes to the file formats over the history of novelWriter have no impact on the
user side of things. The project files are generally updated automatically. However, some of the
changes require minor actions from the user.

The key changes in the formats are listed in this chapter, as well as the user actions required,
where applicable.

A full project file format specification is available under "More Documents".

.. caution::

   When you update a project from one format version to the next, the project can no longer be
   opened by a version of novelWriter prior to the version where the new file format was
   introduced. You will get a notification about any updates to your project file format and will
   have the option to decline the upgrade.


.. _docs_more_project_formats_1_5:

Format 1.5 Changes
==================

This project format was introduced in novelWriter version 2.0 RC 2.

This is a modification of the 1.4 format. It makes the XML more consistent in that meta data have
been moved to their respective section nodes as attributes, and key/value settings now have a
consistent format. Logical flags are saved as yes/no instead of Python True/False, and the main
heading of the document is now saved to the item rather than in the index. The conversion is done
automatically the first time a project is loaded. No user action is required.


.. _docs_more_project_formats_1_4:

Format 1.4 Changes
==================

This project format was introduced in novelWriter version 2.0 RC 1. Since this was a release
candidate, it is unlikely that your project uses it, but it may be the case if you've installed a
pre-release.

This format changes the way project items (folders, documents and notes) are stored. It is a more
compact format that is simpler and faster to parse, and easier to extend. The conversion is done
automatically the first time a project is loaded. No user action is required.


.. _docs_more_project_formats_1_3:

Format 1.3 Changes
==================

This project format was introduced in novelWriter version 1.5.

With this format, the number of document layouts was reduced from eight to two. The conversion of
document layouts is performed automatically when the project is opened.

Due to the reduction of layouts, some features that were previously controlled by these layouts
will be lost. These features are instead now controlled by syntax codes, so to recover these
features, some minor modification must be made to select documents by the user.

The manual changes the user must make should be very few as they apply to document layouts that
should be used only a few places in any given project. These are as follows:

**Title Pages**

* The formatting of the level one title on the title page must be changed from ``# Title Text`` to
  ``#! Title Text`` in order to retain the previous functionality.
  See :ref:`docs_usage_headings_levels`.
* Any text that was previously centred on the page must be manually centred using the text
  alignment feature. See :ref:`docs_usage_align_indent`.

**Unnumbered Chapters**

* Since the specific layout for unnumbered chapters has been dropped, such chapters must all use
  the ``##! Chapter Name`` formatting code instead of ``## Chapter Name``. This also includes
  chapters marked by an asterisk: ``## *Chapter Name``, as this feature has also been dropped.
  See :ref:`docs_usage_headings_levels`.

**Plain Pages**

* The layout named "Plain Page" has also been removed. The only feature of this layout was that it
  ensured that the content always started on a fresh page. In the new format, fresh pages can be
  set anywhere in the text with the ``[new page]`` code. See :ref:`docs_usage_formatting_breaks`.


.. _docs_more_project_formats_1_2:

Format 1.2 Changes
==================

This project format was introduced in novelWriter version 0.10.

With this format, the way auto-replace entries were stored in the main project XML file changed.
Conversion from this format is done automatically.


.. _docs_more_project_formats_1_1:

Format 1.1 Changes
==================

This project format was introduced in novelWriter version 0.7.

With this format, the ``content`` folder was introduced in the project storage. Previously, all
novelWriter documents were saved in a series of folders numbered from ``data_0`` to ``data_f``.

It also reduces the number of meta data and cache files. These files are automatically deleted if
an old project is opened. This was also when the Table of Contents file was introduced. Conversion
from this format is done automatically.


.. _docs_more_project_formats_1_0:

Format 1.0 Changes
==================

This is the original file format and project structure. It was in use up to version 0.6.3.
