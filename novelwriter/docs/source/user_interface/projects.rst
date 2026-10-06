.. _docs_ui_projects:

*****************
Managing Projects
*****************

Your text in novelWriter is organised into projects. Each project is meant to contain one novel
and associated notes. If you have multiple novels in a series, with the same characters and shared
notes, it is also possible to keep all of them in the same project by creating multiple **Novel**
root folders. See :ref:`docs_usage_project_roots` for more details.


.. _docs_ui_projects_new:

Creating A New Project
======================

You can create a new project from the **Project** menu by selecting **Create or Open Project**.
This will open the **Welcome** dialog, where you can select the :guilabel:`New` button that will
assist you in creating a project. This dialog is also displayed when you start novelWriter.

A novelWriter project requires a dedicated folder for storing its files on the local file system.
If you're interested in the details of how projects are stored, you can have a look at the section
:ref:`docs_technical_storage`.

A list of recently opened projects is maintained, and displayed in the **Welcome** dialog. A
project can be removed from this list by selecting it and pressing the :kbd:`Del` key or by
right-clicking it and selecting the **Remove Project** option.

.. figure:: images/fig_welcome.jpg

   The project list (left) and new project form (right) of the **Welcome** dialog.

Project-specific settings are available in **Project Settings** in the **Project** menu. See
further details below in the :ref:`docs_ui_projects_settings` section.

Statistics about the project are available in the **Manuscript Build** tool.


Template Projects
-----------------

From the Welcome dialog you can also create a new from another existing project. If you have a
specific structure you want to use for all your new projects, you can create a dedicated project to
be used as a template, and select to copy an existing project from the "Prefill Project" option
from the **New Project** form.


.. _docs_ui_projects_settings:

Project Settings
================

The **Project Settings** can be accessed from the **Project** menu, or by pressing
:kbd:`Ctrl+Shift+,`. This will open a dialog box, with a set of tabs.


General Settings
----------------

The **Settings** tab holds the project name, author, and language settings.

The **Project Name** can be edited here. It is used for the main window title and for generating
backup files. So keep in mind that if you do change this setting, the backup file names will change
too.

You can also change the **Author** and **Project Language** setting. These are only used when
building the manuscript, for some formats. The language setting is also used when inserting text
into documents in the viewer, like for instance labels for keywords and special comments.

If your project is in a different language than your main spell checking language is set to, you
can override the default setting here. The project language can also be changed from the **Tools**
menu.

You can also override the automatic backup setting for the project if you wish.


.. _docs_ui_projects_settings_status:

Status and Importance
---------------------

Each document or folder of type **Novel** can be given a "Status" label accompanied by a coloured
icon with an optional shape selected from a list of pre-defined shapes. Each document or folder of
the remaining types can be given an "Importance" label with the same customisation options.

These labels are there purely for your convenience, and you are not required to use them for any
other features to work. No other part of novelWriter accesses this information. The intention is to
use these to indicate at what stage of completion each novel document is, or how important the
content of a note is to the story. You don't have to use them this way, that's just what they were
intended for, but you can make them whatever you want.

Both status and importance labels can be exported and imported so you can share them between
projects, or define a standard set for all your writing projects. When you import labels to a
project, they are always added as *new* labels.

See also :ref:`docs_usage_project_status`.

.. note::

   Status or importance level currently in use cannot be deleted, but they can be edited.


Text Auto-Replace
-----------------

A set of automatically replaced keywords can be added in this tab. The keywords in the left column
will be replaced by the text in the right column when documents are opened in the viewer. They will
also be applied to manuscript builds.

The auto-replace feature will replace text in angle brackets that is in this list. The syntax
highlighter will add an alternate colour to text matching the syntax, but it doesn't check if the
text is in this list.

.. note::

   A keyword cannot contain spaces. The angle brackets are added by default, and when used in the
   text are a part of the keyword to be replaced. This is to ensure that parts of the text aren't
   unintentionally replaced by the content of the list.


.. _docs_ui_projects_backup:

Backup
======

An automatic backup system is built into novelWriter. In order to use it, a backup path to where
the backup files are to be stored must be provided in **Preferences**. The path defaults to a
folder named "Backups" in your home directory.

Backups can run automatically when a project is closed, which also implies it is run when the
application itself is closed. Backups are date stamped zip files of the project files in the
project folder (files not strictly a part of the project are ignored). The zip archives are stored
in a subfolder of the backup path. The subfolder will have the same name as the **Project Name**
defined in :ref:`docs_ui_projects_settings`.

The backup feature, when configured, can also be run manually from the **Tools** menu. It is also
possible to disable automated backups for a given project in **Project Settings**.

.. note::

   For the backup to be able to run, the **Project Name** must be set in **Project Settings**. This
   value is used to generate the name and path of the backups. Without it, the backup will not run
   at all, but it will produce a warning message.
