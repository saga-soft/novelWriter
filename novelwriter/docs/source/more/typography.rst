.. _docs_more_typographical:

*******************
Typographical Notes
*******************

.. _Prime: https://en.wikipedia.org/wiki/Prime_(symbol)
.. _thin space: https://en.wikipedia.org/wiki/Thin_space
.. _Quotation Mark: https://en.wikipedia.org/wiki/Quotation_mark
.. _Modifier letter apostrophe: https://en.wikipedia.org/wiki/Modifier_letter_apostrophe

novelWriter has some support for typographical symbols that are not usually easily available in
many text editors. This includes for instance the proper unicode quotation marks, dashes, ellipsis,
thin spaces, etc. All these symbols are available from the **Insert** menu, and via
keyboard shortcuts. See :ref:`docs_features_shortcuts_insert`.

This chapter provides some additional information on how novelWriter handles these symbols.


Dashes and Ellipsis
===================

With the auto-replace feature enabled (see :ref:`docs_ui_edit_view_auto`), two and three hyphens
are converted automatically to short and long dashes, four hyphens to a horizontal bar, and three
dots to ellipsis.

.. tip::

   The last auto-replace can always be reverted with the undo command :kbd:`Ctrl+Z`, reverting the
   text to what you typed before the automatic replacement occurred.

In addition, "Figure Dash" is available. The Figure Dash is a dash that has the same width as the
numbers of the same font, for most fonts. It helps to align numbers nicely in columns when you need
to use a dash in them.


Single and Double Quotes
========================

All the different quotation marks listed on the `Quotation Mark`_ Wikipedia page are available, and
can be selected as auto-replaced symbols for straight single and double quote key strokes. The
settings can be found in **Preferences**.

If your text contains straight single and double quotes, there are two convenience functions in the
**Format** menu that can be used to re-format a selected section of text with the correct quote
symbols.

You can enable dialogue recognition and colour highlighting for novel documents.
See :ref:`docs_features_dialogue` for more details.


Single and Double Prime
=======================

Both single and double prime symbols are available in the **Insert** menu. These symbols
are the correct symbols to use for unit symbols for feet, inches, minutes, and seconds. The usage
of these is described in more detail on the Wikipedia Prime_ page. They look very similar to single
and double straight quotes, and may be rendered similarly by the font, but they have different
codes. Using these correctly will also prevent the auto-replace and dialogue highlighting features
misunderstanding their meaning in the text.


.. _docs_more_typographical_symbols_apostrophe:

Modifier Letter Apostrophe
==========================

The auto-replace feature will consider any right-facing single straight quote as a quote symbol,
even if it is intended as an apostrophe. This also includes the syntax highlighter, which may
assume the first following apostrophe is the closing symbol of a single quoted region of text.

To get around this, an alternative apostrophe is available. It is a special Unicode character that
is not categorised as punctuation, but as a modifier. It is usually rendered the same way as the
right single quotation marks, depending on the font. There is a Wikipedia article for the
`Modifier letter apostrophe`_ with more details.

.. note::

   On export with the **Manuscript Build** tool, these apostrophes will be replaced
   automatically with the corresponding right hand single quote symbol as is generally recommended.
   Therefore it doesn't really matter if you only use them to correct syntax highlighting in some
   places, and not others.


White Space Symbols
===================

A few variations of the regular space character is supported. The correct typographical way to
separate a number from its unit is with a `thin space`_. It is usually 2/3 the width of a regular
space. For numbers and units, this should in addition be a non-breaking space, that is, the text
wrapping should not add a line break on this particular space.

A regular space can also be made into a non-breaking space if needed.

All non-breaking spaces are highlighted with a differently coloured background to make it easier to
spot them in the text. The colour will depend on the selected colour theme.

You can insert these spaces in your text using the following keyboard combinations:

* A non-breaking space can be inserted with :kbd:`Ctrl+K`, :kbd:`Space`.
* Thin spaces are also supported, and can be inserted with :kbd:`Ctrl+K`, :kbd:`Shift+Space`.
* Non-breaking thin space can be inserted with :kbd:`Ctrl+K`, :kbd:`Ctrl+Space`.

These are all insert features, and the **Insert** menu has more. The keyboard shortcuts for them
are also listed in :ref:`docs_features_shortcuts`.
