.. _docs_usage_tags_refs:

*******************
Tags and References
*******************

One of the core features of novelWriter is its **Tags and References** system. This is perhaps one
of the features that makes novelWriter different from other similar applications. It is therefore
not always obvious to new users how this is supposed to work.

In novelWriter there are no forms or tables to fill in to define characters, locations or other
elements of your story. Instead, you create documents in one of the root folders for notes. Within
these documents you can set **tags**, like for instance for your main character. If you then want
to annotate a scene with this character as its point-of-view, you create a **reference** to the
tag.

.. tip::

   If you find the Tags and Reference system difficult to follow just from reading this chapter,
   you can create a new project in the **Welcome** dialog's New Project form and select "Create an
   example project" from the "Pre-fill project" option. The example project contains several
   examples of tags and references.


.. _docs_usage_tags_refs_tags:

How to Use Tags
===============

The structure of your novelWriter project is inferred from the headings within the documents, not
the documents themselves. See :ref:`docs_usage_headings` for more details. Therefore, metadata is
also associated with headings, and not the documents themselves.

A "tag" in novelWriter is a word or phrase that you define as belonging to a heading. Tags are set
by using the ``@tag`` keyword.

The basic format of a tag is ``@tag: TagName``.

An alternative format of a tag is ``@tag: TagName | Display Name``.

``tagName`` (Required)
   This is a unique identifier of your choosing. It is the value you use later for making
   references back to the heading in the document. The tag must be unique.

``Display Name`` (Optional)
   This is an optional display name used for the tag. When you build your manuscript, you can for
   instance insert the point-of-view character name directly into chapter titles. By default, the
   ``tagName`` value is used in such headings, but if you use a shortened format internally in your
   project, you can use the display name to specify a more suitable format for your chapter title.

.. note::

   You can only set **one** tag per heading, and the tag has to be unique across **all** documents
   in the project.

After a tag has been defined, it can be referenced in novel documents, or cross-referenced in other
notes. Tags will also show up in the **Outline View** and in the **References** panel under the
document viewer when a document is open in the viewer. See :ref:`docs_ui_main_outline` and
:ref:`docs_ui_edit_view_view_references` for more details.

The editor will indicate to you that the keyword is correctly used and that the tag is allowed,
that is, the tag is unique, by adding a colour highlighting to it. An invalid tag should have a
wiggly line under it, and will not receive the colour that valid tags do.

The tag is the only part of notes that novelWriter uses. The rest of the document content is there
for you to use in whatever way you wish.

.. versionadded:: 2.2

   Tags are no longer case sensitive. The tags are by default displayed with the capitalisation you
   use when defining the tag, but you don't have to use the same capitalisation when referencing
   it later.

.. versionadded:: 2.3

   Tags can have an optional display name for manuscript builds.

.. versionadded:: 2.6

   You can now add tags also to Novel Documents. These can be used for cross-referencing between
   chapters and scenes, and also from notes if desired.

:bdg-info:`Example`

Example of a note document for a character with a tag set:

.. code-block:: md

   # Character: Jane Doe

   @tag: Jane | Jane Doe

   Some information about the character Jane Doe.

When this is done in a document in a root folder of type **Characters**, the tag is automatically
treated as an available character in your project with the value "Jane". You will then be able to
reference "Jane" in any of your other documents using the reference keywords for characters.

The character "Jane" will also show up in the **Character** tab in the **Reference** panel below
the document viewer.

.. note::

   It is the root folder type that defines what category of story elements the tag is indexed
   under. See :ref:`docs_usage_project_roots` for more details.


.. _docs_usage_tags_refs_refs:

How to Use References
=====================

Each heading of any level in your project can contain references to tags set in your notes. The
references are gathered by the project index and used to generate the **Outline View**, among other
things.

References are set with a special keyword, with a list of corresponding tags. The valid keywords
are listed below. The format of a reference line is ``@keyword: value1, [value2] ... [valueN]``.
All reference keywords allow multiple values.

``@pov``
   The point-of-view character for the current section. The target must be a note tag in a
   **Character** type root folder.

``@focus``
   The character that has the focus for the current section. This can be used in cases where the
   focus is not the point-of-view character. The target must be a note tag in a **Character** type
   root folder.

``@char``
   For other characters in the current section. The target must be a note tag in a **Character**
   type root folder. This should not include the point-of-view or focus character if those
   references are used.

``@plot``
   The plot or subplot advanced in the current section. The target must be a note tag in a **Plot**
   type root folder.

``@time``
   The timelines touched by the current section. The target must be a note tag in a **Timeline**
   type root folder.

``@location``
   The location the current section takes place in. The target must be a note tag in a
   **Locations** type root folder.

``@object``
   Objects present in the current section. The target must be a note tag in a **Object** type root
   folder.

``@entity``
   Entities present in the current section. The target must be a note tag in an **Entities** type
   root folder.

``@custom``
   Custom references in the current section. The target must be a note tag in a **Custom** type
   root folder. The custom folder are for any other category of notes you may want to use.

``@mention``
   For anything, anyone or anyplace mentioned, but not present in the current section. It is
   intended for those cases where you reveal details about a character or place in a scene without
   otherwise being a part of it. This can be useful when checking for consistency later. Any tag in
   any root note folder can be listed under ``@mention``.

``@story``
   This is used when referencing a Novel Document, like a scene or chapter, from somewhere else in
   your project. It is possible to also set tags in documents in a **Novel** type folder, and this
   is the keyword you use to reference those.

When tags and references are used correctly, it will be indicated by highlight colours in the
editor.

.. note::

   The highlighter may be mistaken if the index of defined tags is out of date. If so, press
   :kbd:`F9` to regenerate it, or select **Rebuild Index** from the **Tools** menu. In general, the
   index for a document is regenerated when it is saved, so this shouldn't normally be necessary.

.. tip::

   If you add a reference in the editor to a tag that doesn't yet exist, you can right-click it and
   select **Create Note for Tag**. This will generate a new note automatically in the correct type
   of root folder, with the new tag defined.

One note can also reference another note in the same way novel documents do. When the note is
opened in the document viewer, the references become clickable links, making it easier to follow
connections in the plot. You can follow links in the document editor by clicking them with the
mouse while holding down the :kbd:`Ctrl` key. Clicked links are always opened in the view panel.

Your notes don't show up in the **Outline View**, so referencing between notes is only meaningful
if you want to be able to click-navigate between them, or of course if you just want to highlight
that two notes are related.

.. tip::

   If you cross-reference between notes and export your project as an HTML document using the
   **Manuscript Build** tool, the cross-references become clickable links in the exported HTML
   document as well.

:bdg-info:`Example`

Example of a novel document with references to characters and plots:

.. code-block:: md

   ## Chapter 1

   @pov: Jane

   ### Scene 1

   @char: John, Sam
   @plot: Main

   Once upon a time ...


.. _docs_usage_tags_refs_completer:

Auto-Completion in the Editor
-----------------------------

An auto-completer context menu will show up automatically in the document editor when you type the
character ``@`` on a new line. It will first suggest tag or reference keywords for you to add, and
after the ``:`` has been added, suggest references from the list of tags you have already defined.

You can use the auto-completer to add multiple references with a ``,`` between them, and even type
new ones. Notes for new references can be created by right-clicking on them and selecting **Create
Note for Tag** from the menu.

.. versionadded:: 2.2
