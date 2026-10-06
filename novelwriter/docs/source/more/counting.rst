.. _docs_more_counting:

********************
Word and Text Counts
********************

This is an overview of how words and other counts of your text are performed. The counting rules
should be relatively standard, and are comparable to Libre Office Writer rules.

The counts provided in the app on the raw text are meant to be approximate. For more accurate
counts, you need to build your manuscript in the **Manuscript Tool** and check the counts on the
generated preview.


Text Word Counts and Stats
==========================

These are the rules for the main counts available for each document in a project.

For all counts, the following rules apply.

#. Short (–) and long (—) dashes are considered word separators.
#. Any line starting with ``%`` or ``@`` is ignored.
#. Trailing white spaces are ignored, including line breaks.
#. Leading ``>`` and trailing ``<`` are ignored with any spaces next to them.
#. Valid shortcodes and other commands wrapped in brackets ``[]`` are ignored.
#. In-line Markdown syntax in text paragraphs is treated as part of the text.

After the above preparation of the text, the following counts are available.

**Character Count**
   The character count is the sum of characters per line, including leading and in-text white space
   characters, but excluding trailing white space characters. Shortcodes in the text are not
   included, but Markdown codes are. Only headings and text are counted.

**Word Count**
   The words count is the sum of blocks of continuous character per line separated by any number of
   white space characters or dashes. Only headings and text are counted.

**Paragraph Count**
   The paragraph count is the number of text blocks separated by one or more empty line. A line
   consisting only of white spaces is considered empty.


Manuscript Counts
=================

These are the rules for the counts available for a manuscript in the **Manuscript Tool**. The rules
have been tuned to agree with LibreOffice Writer, but will vary slightly depending on the content
of your text. LibreOffice Writer also counts the text in the page header, which the **Manuscript
Tool** does not.

The content of each line is counted after all formatting has been processed, so the result will be
more accurate than the counts for text documents elsewhere in the app. The following rules apply:

#. Short (–) and long (—) dashes are considered word separators.
#. Leading and trailing white spaces are generally included, but paragraph breaks are not.
#. Hard line breaks within paragraph are considered white space characters.
#. All formatting codes are ignored, including shortcodes, commands and Markdown.
#. Scene and section separators are counted.
#. Comments and meta data lines are counted after they are formatted.
#. Headers are counted after they are formatted with custom formats.

The following counts are available:

**Headings**
   The number of headings in the manuscript.

**Paragraphs**
   The number of body text paragraphs in the manuscript.

**Words**
   The number of words in the manuscript, including any comments and meta data text.

**Words in Text**
   The number of words in body text paragraphs, excluding all other text.

**Words in Headings**
   The number of words in headings, including inserted formatting like chapter numbers, etc.

**Characters**
   The number of characters in all lines, including any comments and meta data text. Paragraph
   breaks are not counted, but in-paragraph hard line breaks are.

**Characters in Text**
   The number of characters in body text paragraphs. Paragraph breaks are not counted, but
   in-paragraph hard line breaks are.

**Characters in Headings**
   The number of characters in headings.

**Characters in Text, No Spaces**
   The number of characters in body text paragraphs considered part of a word or punctuation. That
   is, white space characters are not counted.

**Characters in Headings, No Spaces**
   The number of characters in headings considered part of a word or punctuation. That is, white
   space characters are not counted.
