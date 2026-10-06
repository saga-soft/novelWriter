.. _docs_usage:

************
Introduction
************

.. _Markdown: https://en.wikipedia.org/wiki/Markdown
.. _Contributing Guide: https://github.com/saga-soft/novelWriter/blob/main/CONTRIBUTING.md
.. _Crowdin: https://crowdin.com/project/novelwriter

In a nutshell, novelWriter is a plain text editor that lets you organise one or more novels, and
associated notes, as many smaller documents. You can at any time generate standard document formats
from these plain text documents. Whether it is an outline of your story, a draft, a complete
manuscript, or even a collection of your character notes or other notes.


Why Plain Text?
===============

The idea is to let you be creative without having to deal with formatting while you are writing, or
be distracted by it.

Of course, you probably need *some* form of minimal formatting for your text. At the very least you
need emphasis. Most people are familiar with adding emphasis using ``_underscores_`` and
``**asterisks**``. This formatting standard comes from Markdown_ and is supported by novelWriter.
It also uses Markdown formatting for defining document headings, which is how you distinguish
between chapters and scenes.

For those special cases where you need more complex formatting, a set of shortcodes are available.
To make these codes easier to use, a dropdown button bar is available in the editor panel with
standard format buttons. So don't worry. You don't have to learn any of these codes.


Adding Meta Data
================

In addition to the body text of your story, novelWriter allows you to enter some additional meta
data into your text documents to indicate things like which characters are present in a chapter or
scene, whose point of view we're seeing, what location the events take place in, and so on.

Since the editor is plain text, this is done on special lines of text starting with an ``@``
character. The editor will show an auto-complete menu to help you write these lines. We will talk
more about this later.

You can also add your own author's comments in your text, without these comments becoming a part of
the story itself. A comment line starts with a ``%`` character. There are different types of
comments, and an auto-complete menu can help you here too. More about this later as well.

.. admonition:: Limitations

   Please keep in mind that novelWriter is designed for writing fiction, so the formatting features
   available are limited to those relevant for this purpose. It is *not* suitable for technical
   writing. It is also *not* a full-featured Markdown editor.

   In addition, novelWriter is not intended as a tool for organising research for writing, and
   therefore lacks formatting features you may need for this purpose. The notes feature is
   mainly intended for character profiles and plot outlines. It is recommended to use a proper
   note-taking tool for research. This is anyway more practical as you may use the same research
   for multiple projects.


.. _docs_contributing:

Contributing
============

This project relies on contributions to add new features. In particular, adding translations into
other languages, or updating translations for existing languages, is particularly useful.

For code contributions, please read the official `Contributing Guide`_.

For translations, please use the project page on Crowdin_. For each language, there are two
translation sets. One for the application itself, labelled "Main GUI". This is a fairly large
dataset to translate. A smaller set called "Project Exports" is also available. The latter is what
makes a language available in **Project Settings** in the application. It is a fairly small set to
translate, and you can choose to translate only this set if you wish. If the language you wish to
contribute to is not available in the list, you can message the maintainer on the Crowdin page to
add new languages to the project.
