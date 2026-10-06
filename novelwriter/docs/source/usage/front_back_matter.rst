.. _docs_usage_front_back_matter:

*********************
Front and Back Matter
*********************

Front and back matter documents are documents that go before and after your main story text. They
can include pages like your cover page, content tables, prologues, epilogues, etc. These special
pages and sections are supported to some extent by novelWriter.


.. _docs_usage_front_back_matter_title:

The Title Page
==============

It is recommended that you add a document at the very top of each **Novel** root folder with the
novel title in it. You should modify the level 1 heading format code with an ``!`` in order to
render it as a document title that is excluded from any automatic Table of Content in a manuscript
build document.

You can also add the author name and address above this if this is required by the manuscript
format you use, and additional space added before the title.

:bdg-info:`Example`

This is the title page novelWriter generates automatically for a new project as of version 2.6:

.. code-block:: md

   Jane Doe[br]
   Address Line 1[br]
   Address Line 2 <<

   [vspace:5]

   #! My Novel

   >> **By Jane Doe** <<

   >> Word Count: [field:textWords] <<

The title is by default centred on the page. You can add more text to the page as you wish, like
for instance the author's name and details.

The default title page inserts the word count for text only, but you can add other counts too.
See :ref:`docs_usage_formatting_counts` for more details.


.. _docs_usage_front_back_matter_pages:

Additional Pages
================

If you want an additional page of text after the title page, starting on a fresh page, you can add
``[new page]`` on a line by itself, and continue the text after it. This will insert a page break
before the text. See :ref:`docs_usage_formatting_breaks` for more details.


.. _docs_usage_front_back_matter_unnumbered:

Unnumbered Chapters
===================

If you use the automatic numbering feature for your chapters, but you want to keep some special
chapters separate from this, you can add an ``!`` to the level 2 heading formatting code to tell
the build tool to skip these chapters when adding numbers.

Unnumbered chapters are useful for prologue and epilogue chapters, and also for interlude chapters
if you use those in your text. There is a separate formatting feature for such chapter titles in
the **Manuscript Build** tool. See the :ref:`docs_ui_manuscript` page for more details.

:bdg-info:`Example`

.. code-block:: md

   ##! Unnumbered Chapter Title

   Chapter Text
