.. _docs_usage_headings:

*******************
Chapters and Scenes
*******************

.. _Markdown: https://en.wikipedia.org/wiki/Markdown

Since novelWriter uses a plain text format, the structure of your novel must follow a certain set
of simple rules. For documents in a **Novel** type root folder, it is the heading that determines
if the document is a chapter or a scene.

The formatting of headings is based on Markdown_. A heading is indicated by a line starting with
one or more ``#`` characters. It accepts up to four of these. You can use multiple headings in the
same document, but it is the first heading that determines which icon and information is displayed
in the project tree.

.. note::

   You can use the same heading levels for your notes in the other root folders, but they aren't
   treated as chapters or scenes, so there you are free to use them as you want.


.. _docs_usage_headings_levels:

Heading Levels
==============

.. figure:: images/fig_heading_levels.png

   An illustration of how heading levels correspond to the novel structure.

Four levels of headings are understood for novel documents. You can pick and choose from these as
you want, but if your story has chapters, you should use these headings to indicate them. If you
also add scene headings, you have better control of how your scene separators are formatted in your
manuscript. The chapter and scenes headings are also displayed in the
:ref:`Novel View <docs_ui_main_novel>` and :ref:`Outline View <docs_ui_main_outline>`.

``# Title Text``
   This is a heading level one. This heading indicates the start of a new partition. Partitions are
   for when you want to split your story into "Part 1", "Part 2", etc. You can also choose to use
   them for splitting the text up into acts, and then hide these headings in your manuscript so
   that they are not included in the output.

``## Chapter Title``
   This is a heading level two. This heading indicates the start of a new chapter. Chapter numbers
   can be inserted automatically when building the manuscript, so you don't have to do this in the
   title. See :ref:`docs_ui_manuscript_formatting_head_numbers` for more details.

``### Scene Title``
   This is a heading level three. This heading indicates the start of a new scene. Scene numbers or
   scene separators can be inserted automatically when building the manuscript, so you can use the
   title field as a working title for your scenes if you wish, but you must provide a minimal
   title.

``#### Section Title``
   This is a heading level four. This heading indicates the start of a new section. Section titles
   can be replaced by separators or ignored completely when building the manuscript. The meaning of
   a section is really whatever you want it to be. You can use it to split your scenes up into
   chunks, or into separate documents.

For headings level one through three, adding a ``!`` modifies the meaning of the heading. The
alternative meaning of the heading is only relevant when you generate your manuscript, but you may
want to keep the use cases in mind while writing.

``#! Title Text``
   This tells the **Manuscript Build** tool that the level one heading is intended to be used for
   the novel or notes folder's main title, like for instance the novel title on the cover page.
   When building the manuscript, this will use a different styling of the title, which you can
   modify independently from how partition titles are styled.
   See :ref:`docs_usage_front_back_matter_title` for more details.

``##! Chapter Title``
   This tells the **Manuscript Build** tool to not assign a chapter number to this chapter title if
   automatic chapter numbers are enabled. Such titles are useful for prologues and epilogues for
   instance. See :ref:`docs_usage_front_back_matter_unnumbered` for more details.

``###! Scene Title``
   This is an alternative scene heading that can be formatted differently in the **Manuscript
   Build** tool. It is intended for separating "soft" and "hard" scene breaks. Aside from this, it
   behaves identically to a regular scene heading.
   See :ref:`docs_ui_manuscript_formatting_head_hard_soft` for more details.

The formatting of these headings can be customised quite extensively in the
:ref:`Manuscript Tool <docs_ui_manuscript_formatting>`, which is covered in a separate part of the
documentation.

.. note::

   The space after the ``#`` or ``!`` character is mandatory. The editor will change colour and
   font size when the heading is correctly formatted.

Page breaks can be automatically added before titles, partition, chapter and scene headings from
the **Manuscript Build** tool when you build your project to a format that supports page breaks.
If you want page breaks in other places, you have to specify them manually.
See :ref:`docs_usage_formatting_breaks` for more details.

.. note::

   When you build a manuscript from your project, the level of the headings in your document will
   change. See :ref:`docs_ui_manuscript_formatting_head_promote` for more details.
