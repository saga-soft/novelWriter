.. _docs_usage_formatting:

*******************
Advanced Formatting
*******************

Standard Markdown formatting is somewhat limited, so novelWriter has some additional formatting
codes for special use cases. These codes are all based on brackets, and some allow an additional
value to be set after a colon.

This section covers all these formatting codes.


.. _docs_usage_formatting_shortcodes:

Formatting with Shortcodes
==========================

For basic formatting, like emphasis, you should use the standard Markdown style formatting tags
descried in :ref:`docs_usage_basics_emphasis` whenever possible.

For additional formatting options, you can use shortcodes. Shortcodes is a form of in-line codes
that wrap the section of text to be formatted. Shortcodes can be nested to apply multiple formats
to the same piece of text.

These shortcodes are intended for special formatting cases, or more complex cases that cannot be
solved with simple Markdown-like formatting codes. Available shortcodes are listed below.

.. csv-table:: Shortcodes Formats
   :header: "Syntax", "Description"
   :widths: 40, 60
   :class: "tight-table"

   "``[b]text[/b]``",     "Text is displayed as bold text."
   "``[i]text[/i]``",     "Text is displayed as italicised text."
   "``[s]text[/s]``",     "Text is displayed as strike through text."
   "``[u]text[/u]``",     "Text is displayed as underlined text."
   "``[m]text[/m]``",     "Text is displayed as highlighted text."
   "``[sup]text[/sup]``", "Text is displayed as superscript text."
   "``[sub]text[/sub]``", "Text is displayed as subscript text."
   "``[footnote:key]``",  "A reference to a :ref:`footnote comment <docs_usage_comments_footnotes>`."

Unlike Markdown style codes, these can be used anywhere within a paragraph. Even in the middle of a
word if you need to. You can also freely combine them to form more complex formatting.

The shortcodes are available from the **Format** menu and in the editor toolbar, which can be
activated by clicking the left-most icon button in the editor header.

.. note::

   Shortcodes are not processed until you generate a preview or generate a manuscript document. So
   there is no highlighting of the text between the formatting markers. There is also no check that
   your markers make sense. You must ensure that you have both the opening and closing formatting
   markers where you want them.

.. versionadded:: 2.2


.. _docs_usage_formatting_shortcodes_break:

Forced Line Break
-----------------

Inserting ``[br]`` in the text will ensure a line break is always inserted in that place, even if
you turn off **Preserve Hard Line Breaks** in your **Manuscript Build** settings.

You can add a manual line break after it too, for a better visual representation in the editor, but
keep in mind that this line break is removed before the text is processed, so the text on either
side of the ``[br]`` shortcode will be considered as belonging to the same line. This can affect
how alignment is treated. See :ref:`docs_usage_align_indent_forced` for more details.


.. _docs_usage_formatting_breaks:

Vertical Space and Page Breaks
==============================

You can apply page breaks to partition, chapter and scene headings for novel documents from the
**Manuscript Build** tool. If you need to add a page break or additional vertical spacing in other
places, there are special codes available for this purpose.

Adding more than one line break between paragraphs will **not** increase the space between those
paragraphs when generating a manuscript document. To add additional space between paragraphs, add
the text ``[vspace]`` on a line of its own, and the **Manuscript Build** tool will insert a blank
paragraph in its place.

If you need multiple blank paragraphs just add a colon and a number to the above code. For
instance, writing ``[vspace:3]`` will insert three blank paragraphs.

If you need to add a page break somewhere, put the text ``[new page]`` on a line by itself before
the text you wish to start on a new page.

.. note::

   The page break code is applied to the text that follows it. It adds a "page break before" mark
   to the text when exporting to HTML or Open Document. This means that a ``[new page]`` code which
   has no text following it will not result in a page break.

:bdg-info:`Example`

.. code-block:: md

   This is a text paragraph.

   [vspace:2]

   This is another text paragraph, but there will be two empty paragraphs
   between them.

   [new page]

   This text will start on a new page if the build format supports pages.


.. _docs_usage_formatting_counts:

Inserting Word Counts in the Text
=================================

The cover page of a manuscript normally has the word count stated on it. Any statistics value
collected by novelWriter can be inserted into any document using a special shortcode. You can
insert the code for any of the available statistics values from the **Insert** menu under
**Word/Character Count**.

The value inserted is the actual count for your entire manuscript, so it is not populated until you
run the **Manuscript Build** tool. Until then they will show up as "0" in the viewer panel.

The available codes are:

.. csv-table:: Stats Shortcodes
   :header: "Code", "Description"
   :class: "tight-table"

   "``[field:allChars]``",       "Characters"
   "``[field:textChars]``",      "Characters in Text"
   "``[field:titleChars]``",     "Characters in Headings"
   "``[field:paragraphCount]``", "Paragraphs"
   "``[field:titleCount]``",     "Headings"
   "``[field:allWordChars]``",   "Characters, No Spaces"
   "``[field:textWordChars]``",  "Characters in Text, No Spaces"
   "``[field:titleWordChars]``", "Characters in Headings, No Spaces"
   "``[field:allWords]``",       "Words"
   "``[field:textWords]``",      "Words in Text"
   "``[field:titleWords]``",     "Words in Headings"

:bdg-info:`Example`

This is an example cover page. A similar page is automatically generated when you create a new
project.

.. code-block:: md

   Jane Smith[br]
   42 Main Street[br]
   1234 Capital City <<

   [vspace:5]

   #! Example

   >> **By Jane Smith** <<

   >> Word Count: [field:textWords] <<
