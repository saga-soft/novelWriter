.. _docs_more_errors:

***************
Handling Errors
***************

In case something goes wrong, novelWriter has a few built-in features to reduce the chance your
work is lost. In case of a crash, it will also try to save whatever changes you have made before
exiting, if this is at all possible.

The storage solution is designed to save each text document independently, so only the document
you're working on is actually at a risk of losing data in the event of a crash.


.. _docs_more_errors_orphaned:

Recovered Documents
===================

If novelWriter crashes or otherwise exits without saving the project state, or if you're using a
file synchronisation tool that runs out of sync, there may be files in the project storage folder
that aren't tracked in the core project file. These files, when discovered, are recovered and added
back into the project when a project is opened.

The discovered files are scanned for metadata that give clues as to where the document may
previously have been located in the project. The project loading routine will try to put them back
as close as possible to this location, if it still exists. Generally, it will be appended to the
end of the folder where it previously was located. If that folder doesn't exist, it will try to add
it to the correct root folder type. If it cannot figure out which root folder is correct, the
document will be added to the **Novel** root folder. Finally, if a **Novel** does not exist, one
will be created.

If the title of the document can be recovered, the word "Recovered:" will be added as a prefix to
indicate that it may need further attention. If the title cannot be determined, the document will
be named after its internal key, which is a string of characters and numbers.


.. _docs_more_errors_lock:

Project Lockfile
================

To prevent data loss caused by file conflicts when novelWriter projects are synchronised via file
synchronisation tools, a project lockfile is written to the project storage folder when a project
is open. If you try to open a project that already has such a file present, you will be presented
with a warning, and some information about where else novelWriter thinks the project is also open.
You will be given the option to ignore this warning, and continue opening the project at your own
risk.

.. note::

   If, for some reason, novelWriter or your computer crashes, the lock file may remain even if
   there are no other instances keeping the project open. In such a case it is safe to ignore the
   lock file warning when re-opening the project.

.. warning::

   If you choose to ignore the warning and continue opening the project, and multiple instances of
   the project are in fact open, you are likely to cause inconsistencies and create diverging
   project files, potentially resulting in loss of data and orphaned files. You are not likely to
   lose any actual text unless both instances have the same document open in the editor, and
   novelWriter will try to resolve project inconsistencies the next time you open the project.
