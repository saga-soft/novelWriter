.. _docs_usage_comments:

******************
Comments and Notes
******************

You can add comments to your text that are not a part of the story. Regular comments are intended
for you to add notes to yourself inside the text, which may be useful when you revise your drafts.
However, there are several types of comments you can use.

This section covers the basic comment types. There are a couple of advanced features that use
comment syntax too, but they are covered later.


.. _docs_usage_comments_plain:

Plain Comments
==============

A plain comment is a line or paragraph that starts with the character ``%`` as its first character.
You can put them wherever you like in your documents, and you can choose to include or exclude them
from your manuscript.

For the most part, novelWriter completely ignores these comments. They are not included in your
word or character counts either, and are only displayed in the document viewer panel if you enable
them.

:bdg-info:`Example`

.. code-block:: md

   ### Scene

   A regular text paragraph in the scene.

   % A comment you've added for your own notes.

   Another regular text paragraph in the scene.


.. _docs_usage_comments_synopsis:

Synopsis or Description Comments
================================

A special kind of comments are **Synopsis** and **Short Description** comments. They are different
from plain comments in that they can be displayed alongside other information about a scene or a
character or other story element described in a note. As with plain comments, they can be included
in your manuscript, but they are formatted differently than plain comments.

.. note::

   A summary or description comment can be used once, and only once, for each heading as they are
   considered a description of the content of the text under that heading. If you add two such
   comments under the same heading, the last one will be used.


Synopsis
--------

A **Synopsis** comment is intended for adding a summary of your chapters and scenes.

:bdg-info:`Example`

.. code-block:: md

   ### Scene

   %Synopsis: A summary of the content of the scene.

   The actual scene text.


Short Description
-----------------

A **Short Description** comment behaves exactly the same as a synopsis comment, but is intended as
a description of a story element, like a character.

:bdg-info:`Example`

.. code-block:: md

   # Characters

   ## Darth Vader

   %Short: A Sith Lord that used to be a Jedi.

   Your text about the character.

   ## Luke Skywalker

   %Short: A Jedi. The son of Darth Vader.

   Your text about the character.

.. note::

   The ``%Synopsis:`` and ``%Short:`` comment prefixes are interchangeable, but when you include
   them in the manuscript, they are labelled based on the prefix, so the latter may make more sense
   for a Character note than the former.


.. _docs_usage_comments_footnotes:

Footnote Comments
=================

Footnotes are added with a shortcode, paired with a matching comment for the actual footnote text.
The matching is done with a key that links the two. If you insert a footnote from the **Insert**
menu, a unique key is generated for you. Shortcodes in general are covered in more detail in
:ref:`docs_usage_formatting_shortcodes`.

The insert footnote feature will add the footnote shortcode marker at the position of your cursor
in the editor panel, and create the associated footnote comment right after the paragraph. It will
then move the cursor there so you can immediately start typing the footnote text.

The footnote comment can be anywhere in the document, so if you wish to move them to, say, the
bottom of the text, you are free to do so.

Footnote keys are only required to be unique within a document, so if you copy, move or merge text,
you must make sure the keys are not duplicated. If you use the automatically generated keys from
the **Insert** menu, they are unique among all indexed documents. They are not guaranteed to be
unique against footnotes in the **Archive** or **Trash** folder though, but the chance of
accidentally generating the same key twice in a project is relatively small.

:bdg-info:`Example`

.. code-block:: md

   ### Scene

   This is a text paragraph with a footnote[footnote:fn1] in the middle.

   %Footnote.fn1: This is the text of the footnote.

.. versionadded:: 2.5


.. _docs_usage_comments_ignored:

Ignored Text
============

If you want to completely ignore some of the text in your documents, but are not ready to delete
it, you can add ``%~`` before the text paragraph or line. This will cause novelWriter to skip the
text entirely when generating previews or building manuscripts.

This is a better way of removing text than converting them to regular comments, as you may want to
include regular comments in your previews or draft manuscript.

You can toggle the ignored text feature on and off for a paragraph by pressing :kbd:`Ctrl+Shift+D`
on your keyboard with your cursor somewhere in the paragraph.

:bdg-info:`Example`

.. code-block:: md

   ### Scene

   %~ This text is ignored.

   This text is a regular paragraph.
