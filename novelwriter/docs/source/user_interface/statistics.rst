.. _docs_ui_statistics:

******************
Writing Statistics
******************

When you work on a project, a log file records when you opened it, when you closed it, and the
total word counts of your novel documents and notes at the end of the session, provided that the
session lasted either more than 5 minutes, or that the total word count changed. For more details
about the log file itself, see :ref:`docs_technical_storage`.

A tool to view the content of the log file is available in the **Tools** menu under **Writing
Statistics**. You can also launch it by pressing :kbd:`F6`, or find it on the sidebar.

The tool will show a list of all your sessions, and a set of filters to apply to the data. You can
also export the filtered data to a JSON file or to a CSV file that can be opened by a spreadsheet
application like for instance Libre Office Calc or Excel.


Idle Time
=========

The log file stores how much of the session time was spent idle. The definition of idle here is
that the novelWriter main window loses focus, or the user hasn't made any changes to the currently
open document in five minutes. You can change the number of minutes in **Preferences**.


Session Timer
=============

A session timer is by default visible in the status bar. The icon will show you a clock icon when
you are active, and a pause icon when you are considered "idle" per the criteria mentioned above.

If you do not wish to see the timer, you can click on it once to hide it. The icon will still be
visible. Click the icon once more to display the timer again.

.. versionadded:: 2.6

   As of version 2.6, clicking the timer text or icon in the status bar will toggle its visibility.
