.. _docs_more_custom:

*************
Custom Themes
*************

There are a few ways you can customise novelWriter yourself. Currently, you can relatively easily
add new GUI themes. You can also add new icon themes, although this is not as straightforward.


.. _docs_more_custom_theme:

Colour Themes
=============

Adding your own colour themes is relatively easy, although it requires that you manually edit
config files with colour values. The themes are defined in plain text files with meta data and
colour settings, using the toml format,

In order to make your own versions, first copy one of the existing files to your local computer and
modify it as you like.

The existing colour themes are stored in
`novelwriter/assets/themes <https://github.com/saga-soft/novelWriter/tree/main/novelwriter/assets/themes>`_.

Remember to also change the name of your theme by modifying the ``name`` setting at the top of the
file, otherwise you may not be able to distinguish them in **Preferences**.

For novelWriter to be able to locate the custom theme files, you must copy them to the
:ref:`docs_technical_locations_data` location in your home or user area. There should be a folder
there named ``themes`` for colour themes. These folders are created the first time you start
novelWriter.

Once the files are copied there, they should show up in **Preferences** with the label you
set as ``name`` inside the file.

.. note::

   The theme file formats change regularly in new releases. It is up to you to keep custom theme
   files up to date.


The Theme File Format
---------------------

A colour theme ``.toml`` file consists of the following settings:

.. code-block:: toml
   :caption: The theme file for the "Default Light Theme"

   [Main]
   name   = "Default Light Theme"
   mode   = "light"
   author = "Veronica Berglyd Olsen"
   credit = "Veronica Berglyd Olsen"
   url    = "https://github.com/saga-soft/novelWriter"

   [Base]
   base    = "#fcfcfc"
   default = "#303030"
   faded   = "#6c6c6c"
   red     = "#a62a2d"
   orange  = "#b36829"
   yellow  = "#a39c34"
   green   = "#296629"
   cyan    = "#269999"
   blue    = "#3a70a6"
   purple  = "#b35ab3"

   [Project]
   root     = "blue"
   folder   = "yellow"
   file     = "default"
   title    = "green"
   chapter  = "red"
   scene    = "blue"
   note     = "yellow"
   active   = "green"
   inactive = "red"
   disabled = "faded"

   [Icon]
   tool      = "default"
   sidebar   = "default"
   accept    = "green"
   reject    = "red"
   action    = "blue"
   option    = "orange"
   apply     = "green"
   create    = "yellow"
   destroy   = "faded"
   reset     = "green"
   add       = "green"
   change    = "green"
   remove    = "red"
   shortcode = "default"
   markdown  = "orange"
   system    = "yellow"
   info      = "blue"
   warning   = "orange"
   error     = "red"

   [Palette]
   window          = "base:D105"
   windowText      = "default"
   base            = "base"
   alternateBase   = "#e0e0e0"
   text            = "default"
   tooltipBase     = "#ffffc0"
   tooltipText     = "#15150d"
   button          = "#efefef"
   buttonText      = "default"
   brightText      = "base"
   highlight       = "#3087c6"
   highlightedText = "base"
   link            = "blue"
   linkVisited     = "blue"
   accent          = "#3087c6"

   [GUI]
   helpText     = "#5c5c5c"
   fadedText    = "#6c6c6c"
   errorText    = "red"
   accentText   = "blue"
   activeButton = "blue:96"
   activeBase   = "#d7d7d7"
   searchMatch  = "orange:96"

   [Syntax]
   background     = "base"
   text           = "default"
   line           = "default:32"
   link           = "blue"
   headerText     = "green"
   headerTag      = "green:L135"
   emphasis       = "orange"
   whitespace     = "orange:64"
   dialog         = "blue"
   altDialog      = "red"
   note           = "yellow:D125"
   hidden         = "faded"
   shortcode      = "blue"
   keyword        = "red"
   tag            = "green"
   value          = "green"
   optional       = "blue"
   spellCheckLine = "red"
   errorLine      = "green"
   replaceTag     = "green"
   modifier       = "blue"
   textHighlight  = "yellow:72"


Theme Sections
--------------

.. _ColorRole: https://doc.qt.io/qt-6/qpalette.html#ColorRole-enum

The theme file is made up of different sections depending on what part of novelWriter the theme
affects.

.. csv-table:: Theme Sections Overview
   :header: "Section", "Description"
   :class: "tight-table"

   "``[Main]``",    "Meta data about the theme, You must at least set ``name``, ``mode`` and ``author``, and ``mode`` must be either ``light`` or ``dark``."
   "``[Base]``",    "The base colours of the theme. These are also selectable colours in various places inside the app, like for icon colours in **Preferences**."
   "``[Project]``", "The colours used for icons and markers for the different project item types."
   "``[Icon]``",    "The colours used for icons and buttons on the user interface. The names correspond to button and icon roles."
   "``[Palette]``", "The colours used for styling the user interface. The values correspond to the ColorRole_ values in the Qt library."
   "``[GUI]``",     "The colours used for styling additional elements of the user interface."
   "``[Syntax]``",  "The colours used for syntax highlighting in documents."


Colour Value Formats
--------------------

There are several ways to enter colour values:

.. csv-table:: Colour Formats
   :header: "Syntax", "Description"
   :widths: 15, 85
   :class: "tight-table"

   "``#RRGGBB``",    "A CSS style hexadecimal values, like ``#ff0000`` for red."
   "``#RRGGBBAA``",  "A CSS style hexadecimal values with transparency, like ``#ff00007f`` for half-transparent red."
   "``name``",       "A name referring to one of the colours already specified under the ``[Base]`` section, like ``red``. Note that you should not use named colours in the ``[Base]`` section itself as that may have unintended results."
   "``name:255``",   "A name referring to one of the colours already specified under the ``[Base]`` section, with a transparency value added. The value must be in the range ``0`` to ``255``, like ``red:127`` for half-transparent red."
   "``name:L100``",  "A name referring to one of the colours already specified under the ``[Base]`` section, where the L-number is a percentage value that makes it lighter. The value must be greater than ``0``. ``L100`` means no change."
   "``name:D100``",  "A name referring to one of the colours already specified under the ``[Base]`` section, where the D-number is a percentage value that makes it darker. The value must be greater than ``0``. ``D100`` means no change."
   "``r, g, b``",    "A set of red, green and blue numbers in the range ``0`` to ``255``, like ``255, 0, 0`` for red."
   "``r, g, b, a``", "A set of red, green, blue and alpha numbers in the range ``0`` to ``255``, like ``255, 0, 0, 127`` for half-transparent red."

.. versionadded:: 2.5
   The ``fadedtext`` and ``errortext`` theme colour entries were added.

.. versionadded:: 2.7
   The ``icontheme`` setting was dropped as the icon theme is now its own setting.
   The ``[Icons]`` and ``[Project]`` sections were added, and the ``status*`` settings removed.

.. versionadded:: 2.8
   The ``[Syntax]`` section was moved into the main theme file. Previously, these settings were in
   their own file. The ``[Icons]`` section was renamed to ``[Base]``, and a new ``[Icon]`` section
   added for button and icon roles. Added the ``line`` and ``whitespace`` settings. Dropped the
   ``license``, ``licenseurl``, and ``description`` settings. The  ``author`` field is now required
   if the theme is included in the app, but not for user themes.

.. versionadded:: 26.2
   The ``accentText``, ``activeButton``, ``activeBase`` and ``searchMatch`` settings were added to
   the ``[GUI]`` section. The file format was also converted from conf to toml, and a number of the
   colour settings were renamed to camelCase format. The following values were renamed:

   * ``altaction`` to ``option``
   * ``systemio`` to ``system``
   * ``windowtext`` to ``windowText``
   * ``alternatebase`` to ``alternateBase``
   * ``tooltipbase`` to ``tooltipBase``
   * ``tooltiptext`` to ``tooltipText``
   * ``buttontext`` to ``buttonText``
   * ``brighttext`` to ``brightText``
   * ``highlightedtext`` to ``highlightedText``
   * ``linkvisited`` to ``linkVisited``
   * ``helptext`` to ``helpText``
   * ``fadedtext`` to ``fadedText``
   * ``errortext`` to ``errorText``
   * ``headertext`` to ``headerText``
   * ``headertag`` to ``headerTag``
   * ``altdialog`` to ``altDialog``
   * ``spellcheckline`` to ``spellCheckLine``
   * ``errorline`` to ``errorLine``
   * ``replacetag`` to ``replaceTag``
   * ``texthighlight`` to ``textHighlight``


Icon Themes
===========

Icon themes are *not* straightforward to add, but if you want to make the effort, this section
describes how to do it.

The existing icon themes are stored in
`novelwriter/assets/icons <https://github.com/saga-soft/novelWriter/tree/main/novelwriter/assets/icons>`_.

As with colour themes, remember to change the name of your theme by modifying the ``name`` setting
at the top of the file, otherwise you may not be able to distinguish them in **Preferences**.

For novelWriter to be able to locate the custom theme files, you must copy them to the
:ref:`docs_technical_locations_data` location in your home or user area. There should be a folder
there ``icons`` for icon themes. These folders are created the first time you start novelWriter.


The Icons File Format
---------------------

Icon themes are kept in files with the ``.icons`` file extension. The file format is a custom
format with entries on the form ``section:key = value``.

.. code-block:: cfg
   :caption: The icons file for "Material Symbols - Rounded Medium" (truncated)

   # Meta
   meta:name    = Material Symbols - Rounded Medium
   meta:author  = Google Inc
   meta:license = Apache 2.0

   # Icons
   icon:alert_error     = <svg ...>
   icon:alert_info      = <svg ...>
   icon:alert_question  = <svg ...>
   icon:alert_warn      = <svg ...>
   icon:cls_archive     = <svg ...>
   icon:cls_character   = <svg ...>
   icon:cls_custom      = <svg ...>
   icon:cls_entity      = <svg ...>
   icon:cls_none        = <svg ...>
   icon:cls_novel       = <svg ...>
   icon:cls_object      = <svg ...>
   icon:cls_plot        = <svg ...>
   icon:cls_template    = <svg ...>
   icon:cls_timeline    = <svg ...>
   icon:cls_trash       = <svg ...>
   icon:cls_world       = <svg ...>

The icon keys are associated with icon placement locations inside novelWriter, and the template for
them is defined in the script that generates the default icon themes.

The script can be found under
`utils/icon_themes.py <https://github.com/saga-soft/novelWriter/blob/main/utils/icon_themes.py>`__
in the source code.

This file includes all the code needed to generate the themes that are included in novelWriter. The
icon keys are mapped to icon keys from the specific themes in JSON files in the ``icon_themes``
folder next to the script. This is the recommended way to generate these themes. Doing it manually
is not advisable.


Icon Value Format
-----------------

As can be seen from the example, an icon is defined in the ``icon`` section with a key and an
in-line SVG XML block. The XML must fit on one line and obey the following rules:

#. It must be single colour, that is, the fill colour attribute must be able to colourise the
   entire icon.
#. The fill colour attribute *must* be defined and must be set to: ``fill="#000000"``. This value
   is replaced by the relevant theme colour when the icon is processed in novelWriter.
 
.. versionadded:: 2.7
   The icon theme files were added. Previously, icons were stored as individual SVG files with a
   config file mapping the file names to the internal icon keys.
