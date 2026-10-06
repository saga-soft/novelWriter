.. _docs_technical_storage:

******************
How Data is Stored
******************

.. _version control: https://en.wikipedia.org/wiki/Version_control

This chapter contains details of how novelWriter stores and handles the project data.


Overview
========

The files of a novelWriter project are stored in a dedicated project folder. The project structure
is kept in a file at the root of this folder called ``nwProject.nwx``. All the document files and
associated meta data are stored in other folders below the project folder.

This way of storing data was chosen for several reasons.

Firstly, all the text you add to your project is saved directly to your project folder in separate
files. Only the project structure and the text you are currently editing is stored in memory at any
given time, which means there is a smaller risk of losing data if the application or your computer
crashes.

Secondly, having multiple small files means it is very easy to synchronise them between computers
with standard file synchronisation tools.

Thirdly, if you use `version control`_ software to track the changes to your project, the file
formats used for the files are well suited. All the JSON documents have line breaks and indents as
well, which makes it easier to track them with version control software.

.. note::

   Since novelWriter has to keep track of a bunch of files and folders when a project is open, it
   may not run well on some virtual file systems. A file or folder must be accessible with exactly
   the path it was saved or created with. An example where this is not the case is the way Google
   Drive is mapped on Linux Gnome desktops using gvfs/gio.

.. caution::

   You should not add additional files to the project folder yourself. Nor should you, as a rule,
   manually edit files within it. If you really must manually edit the text files, e.g. with some
   automated task you want to perform, you need to rebuild the Project Index when you open
   the project again.

   Editing text files in the ``content`` folder is less risky as these are just plain text. Editing
   the main project XML file, however, may make the project file unreadable and you may crash
   novelWriter and lose project structure information and project settings.


Project Structure
=================

All novelWriter files are written with utf-8 encoding. Since Python automatically converts Unix
line endings to Windows line endings on Windows systems, novelWriter does not make any adaptations
to the formatting on Windows systems. This is handled entirely by the Python standard library.
Python also handles this when working on the same files on both Windows and Unix-based operating
systems.


Main Project File
-----------------

The project itself requires a dedicated folder for storing its files, where novelWriter will create
its own "file system" where the project's folder and file hierarchy is described in a project XML
file. This is the main project file in the project's root folder with the name ``nwProject.nwx``.
This file also contains all the meta data required for the project (except the index data), and a
number of related project settings.

If this file is lost or corrupted, the structure of the project is lost, although not the text
itself. It is important to keep this file backed up, either through the built-in backup tool, or
your own backup solution.

The project XML file is indent-formatted, and is suitable for diff tools and version control since
most of the file will stay static, although a timestamp is set in the meta section on line 2, and
various meta data entries incremented, on each save.

A full project file format specification is available under "More Documents".


Project Documents
=================

All the project documents are saved in a subfolder of the main project folder named ``content``.
Each document has a file handle based on a 52 bit random number, represented as a hexadecimal
string. The documents are saved with a filename assembled from this handle and the file extension
``.nwd``.

If you wish to find the file system location of a document in the project, you can either look it
up in the project XML file, select **Show File Details** from the **Document** menu when having the
document open in the editor, or look in the ``ToC.txt`` file in the root of the project folder. The
``ToC.txt`` file has a list of all documents in the project, referenced by their label, and where
they are saved.

The reason for this cryptic file naming is to avoid issues with file naming conventions and
restrictions on different operating systems, and also to have a file name that does not depend on
what you name the document within the project, or changes it to. This is particularly useful when
using a versioning system.

Each document file contains a plain text version of the text from the editor. The file can in
principle be edited in any text editor, and is suitable for diffing and version control if so
desired. Just make sure the file remains in utf-8 encoding, otherwise unicode characters may
become mangled when the file is opened in novelWriter again.

Editing these files is generally not recommended. The reason for this is that the index will not be
automatically updated when doing so, which means novelWriter doesn't know you've altered the file.
If you *do* edit a file in this manner, you should rebuild the index when you next open the project
in novelWriter.

The first lines of the file may contain some meta data starting with the characters ``%%~``. These
lines are mainly there to restore some information if the file is lost from the main project file,
and the information may be helpful if you do open the file in an external editor as it contains the
document label and the document class and layout. The lines can be deleted without any consequences
to the rest of the content of the file, and will be added back the next time the document is saved
in novelWriter.


The File Saving Process
-----------------------

When saving the project file, or any of the documents, the data is first saved to a temporary file.
If successful, the old data file is then removed, and the temporary file replaces it. This ensures
that the previously saved data is only replaced when the new data has been successfully saved to
the storage medium.


Project Meta Data
=================

The project folder contains a subfolder named ``meta``, containing a number of files. The meta
folder contains semi-important files. That is, they can be lost with only minor impact to the
project. All files in this folder are JSON or JSON Lines files, although some other files may
remain from earlier versions of novelWriter as they haven't all been JSON files in the past.

If you use version control software on your project, you can exclude this folder, although you may
want to track the session log file and the custom words list.


The Project Index
-----------------

Between writing sessions, the project index is saved in a JSON file in ``meta/index.json``.
This file is not critical. If it is lost, it can be completely rebuilt from within novelWriter from
the **Tools** menu.

The index is maintained and updated whenever a document or note is saved in the editor. It contains
all references and tags in documents and notes, as well as the location of all headers in the
project, and the word counts within each header section.

The integrity of the index is checked when the file is loaded. It is possible to corrupt the index
if the file is manually edited and manipulated, so the check is important to avoid sudden crashes
of novelWriter. If the file contains errors, novelWriter will automatically build it anew. If the
check somehow fails and novelWriter keeps crashing, you can delete the file manually and rebuild
the index. If this too fails, you have likely encountered a bug.


Build Definitions
-----------------

The build definitions from the **Manuscript Build** tool are kept in the ``meta/builds.json`` file.
If this file is lost, all custom build definitions are lost too.


Cached GUI Options
------------------

A file named ``meta/options.json`` contains the latest state of various GUI buttons, switches,
dialog window sizes, column sizes, etc, from the GUI. These are the GUI settings that are specific
to the project. Global GUI settings are stored in the main config file.

The file is not critical, but if it is lost, all such GUI options will revert back to their default
settings.


Custom Word List
----------------

A file named ``meta/userdict.json`` contains all the custom words you've added to the project for
spell checking purposes. The content of the file can be edited from the **Tools** menu. If you lose
this file, all your custom spell check words will be lost too.


Session Stats
-------------

The writing progress is saved in the ``meta/sessions.jsonl`` file. This file records the length
and word counts of each writing session on the given project. The file is used by the **Writing
Statistics** tool. If this file is lost, the history it contains is also lost, but it has otherwise
no impact on the project.

Each session is recorded as a JSON object on a single line of the file. Each session record is
appended to the file.
