.. _docs_usage_howto:

*************
Tips & Tricks
*************

.. _Discussions Page: https://github.com/saga-soft/novelWriter/discussions

This is a list of hopefully helpful little tips on how to get the most out of novelWriter.

.. note::
   This section will be expanded over time. If you would like to have something added, feel free to
   contribute, or start a discussion on the project's `Discussions Page`_.


Your Project
============

.. dropdown:: How do I create a project from a template?
   :animate: fade-in-slide-down

   On the Welcome dialog's **Create New Project** form, you can select to "Prefill Project" from
   the content of a different project. This feature is most useful if you copy a project you have
   dedicated to be a template project. If you have a structure and settings you want to use for
   every new project, this is the best solution.

.. dropdown:: How do I merge multiple documents into one?
   :animate: fade-in-slide-down

   If you need to merge a selection of documents in your project into a single document, you can
   achieve this by first making a new folder for just that purpose, and drag all the documents you
   want merged into this folder. Then you can right click the folder, select :guilabel:`Transform`
   and :guilabel:`Merge Documents in Folder`.

   In the dialog that pops up, the documents will be in the same order as in the folder, but you
   can rearrange them here of you wish. See :ref:`docs_ui_split_merge` for more details.

.. dropdown:: How do I share status or importance labels between projects?
   :animate: fade-in-slide-down

   The status or importance labels you have defined in a project can be exported from **Project
   Settings** from the respective configuration tabs. You can then import these labels in another
   project.

.. dropdown:: How do I add introductory text to chapters?
   :animate: fade-in-slide-down

   Sometimes chapters have a short preface, like a brief piece of text or a quote to set the stage
   before the first scene begins.

   If you add separate files for chapters and scenes, the chapter file is the perfect place to add
   such text. Separating chapter and scene files also allows you to make scene files child
   documents of the chapter.

.. dropdown:: How do I distinguishing between soft and hard scene breaks?
   :animate: fade-in-slide-down

   Depending on your writing style, you may need to separate between soft and hard scene breaks
   within chapters. Like for instance if you switch point-of-view character often.

   In such cases you may want to use different scene headings for hard and soft scene breaks. The
   **Manuscript Build** tool will let you define a different format for scenes using the ``###``
   and ``###!`` heading codes when you generate your manuscript. You can for instance add the
   common "``* * *``" for hard breaks and select to hide soft scene breaks, which will just insert
   an empty paragraph in their place. See :ref:`docs_ui_manuscript_settings` for more details.

   .. versionadded:: 2.4

.. dropdown:: How can I set the language for my manuscript?
   :animate: fade-in-slide-down

   The language set for manuscript documents like Open Document and Word Document is taken from
   your project language setting in **Project Settings**. Only some languages are available here,
   but you can override the language information by setting the "Override Document Language" value
   in your Manuscript Build settings to a valid language code. The code uses the
   `IETF BCP 47 language tag <https://en.wikipedia.org/wiki/IETF_language_tag>`__ format.

   Examples: ``en`` for English, ``de`` for German, etc.

   If you want to help add new languages to novelWriter, see: :ref:`docs_contributing`.

   .. versionadded:: 2.8


The Application
===============

.. dropdown:: How can I increase the line height?
   :animate: fade-in-slide-down

   Unfortunately, in this case, novelWriter uses the plain text editor component of the underlying
   framework (called Qt) which doesn't support changing the line height. However, you can choose an
   editor font with larger leading (the spacing between the lines). A good font for this case is
   `Noto <https://fonts.google.com/noto>`__, which comes in both Sans-Serif and Serif.


Layout Tricks
=============

.. dropdown:: How do I create a table?
   :animate: fade-in-slide-down

   The formatting tools available in novelWriter don't allow for complex structures like tables.
   However, the editor does render tabs in a similar way that regular word processors do. You can
   set the width of a tab in **Preferences**.

   The tab key should have the same distance in the editor as in the viewer, so you can align text
   in columns using the tab key, and it should look the same when viewed next to the editor.

   This is most suitable for your notes, as the result in exported documents cannot be guaranteed
   to match. Especially if you don't use the same font in your manuscript as in the editor.

.. dropdown:: How do I force a line break when line breaks are ignored in my manuscript?
   :animate: fade-in-slide-down

   In the **Manuscript Build Settings** you can choose to ignore line breaks within paragraphs in
   your text. However, some times you still need those breaks. Like for instance on the cover page
   where you may need to add your name and address. In such cases, you can add ``[br]`` where you
   want line breaks. These breaks cannot be ignored by any settings and will always be respected.

   .. versionadded:: 2.6

.. dropdown:: How do I turn off first line indent for a specific paragraph?
   :animate: fade-in-slide-down

   If you have first line indent enabled, but have a specific paragraph that you don't want
   indented, you can disable the indentation by explicitly adding text alignment. For instance by
   adding ``<<`` to the end to left-align it. Aligned paragraphs are not indented.

   See :ref:`docs_usage_align_indent` for more details.


Other Tools
===========

.. dropdown:: How do I convert my project to/from the yWriter format?
   :animate: fade-in-slide-down

   There is a tool available that lets you convert a `yWriter <http://spacejock.com/yWriter7.html>`_
   project to a novelWriter project, and vice versa.

   The tool is available at `peter88213.github.io/yw2nw <https://peter88213.github.io/yw2nw/>`__
