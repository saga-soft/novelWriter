.. _docs_usage_basics:

****************
Basic Formatting
****************

.. _Markdown: https://en.wikipedia.org/wiki/Markdown

The basic text formatting syntax of novelWriter is based on Markdown_. It is only a subset of the
Markdown syntax though. Lists, images, and links are not supported.

That said, URLs in the text should automatically be highlighted and become clickable. However, only
URLs starting with "http" or "https" are recognised. In the editor, you must hold down the
:kbd:`Ctrl` key when clicking a URL to follow it.


.. _docs_usage_basics_paragraphs:

Text Paragraphs
===============

A text paragraph is indicated by a blank line. That is, you need two line breaks to separate two
fragments of text into two paragraphs. Single line breaks are treated as line breaks within a
paragraph.

It is important that you actually follow this rule. You should not, for instance, mimic indented
paragraphs manually in the editor. This, and a lot of other formatting options that can be
applied to text paragraphs in the :ref:`Manuscript Tool <docs_ui_manuscript>` depend on paragraphs
being separated by blank lines.

:bdg-success:`Correct`

.. code-block:: md

   ### Scene

   This is a text paragraph.

   This is another text paragraph.

:bdg-danger:`Incorrect`

.. code-block:: md

   ### Scene

   This is a text paragraph.
       This is meant to be another text paragraph.

If you do as shown in the "Incorrect" example, novelWriter will understand this as a single
paragraph with two lines.


.. _docs_usage_basics_emphasis:

Text Emphasis with Markdown
===========================

A minimal set of Markdown text emphasis styles are supported for text paragraphs.

``_text_``
   The text is rendered as emphasised text (italicised).

``**text**``
   The text is rendered as strongly emphasised text (bold).

``*text*`` (optional)
   The text is also rendered as strongly emphasised text (bold).

``~~text~~``
   Strike through text.

``==text==``
   The text is highlighted.

In Markdown guides it is often recommended to differentiate between strong emphasis and emphasis
by using ``**`` for strong and ``_`` for emphasis, although Markdown generally also supports ``__``
for strong and ``*`` for emphasis. However, since the differentiation makes the highlighting and
conversion significantly simpler and faster, in novelWriter this is a rule, not just a
recommendation.

As of version 2026.1, it is possible to enable ``*text*`` for bold text. This has become a very
common notation in many user interfaces, and is now also supported by novelWriter. It can be
enabled in **Preferences** in the **Text Editing** section. Enabling this will not disable
``**text**`` as bold, but will allow both formats. It will, however, change the format button and
:kbd:`Ctrl+B` to use a single asterisk instead of two.

In general, the following rules apply:

1. The emphasis, strike through and highlight formatting tags do not allow spaces between the words
   and the tag itself. That is, ``**text**`` is valid, ``**text **`` is not.
2. More generally, the delimiters must be on the outer edge of words. That is, ``some **text in
   bold** here`` is valid, ``some** text in bold** here`` is not.
3. If using both ``**`` and ``_`` to wrap the same text, the underscore must be the **inner**
   wrapper. This is due to the underscore also being a valid word character, so if they are on the
   outside, they violate rule 2.
4. Text emphasis does not span past line breaks. If you need to add emphasis to multiple lines or
   paragraphs, you must apply it to each of them in turn.
5. Text emphasis can only be used in comments and paragraphs. Headings and meta data tags don't
   allow for formatting, and any formatting markup will be displayed as-is.

.. tip::

   novelWriter supports standard escape syntax for the emphasis markup characters in case the
   editor misunderstands your intended usage of them. That is, ``\*``, ``\_`` and ``\~`` will
   generate a plain ``*``, ``_`` and ``~``, respectively, without interpreting them as part of the
   markup.
