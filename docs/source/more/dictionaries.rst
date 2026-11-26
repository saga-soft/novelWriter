.. _docs_more_dictionaries:

************************
Spell Check Dictionaries
************************

.. _Enchant: https://rrthomas.github.io/enchant/

On Linux and Windows, spell checking is provided by the Enchant_ library. Depending on your
operating system, it may or may not load all installed spell check dictionaries automatically. On
macOS, novelWriter uses the spell checker built into the operating system.


Linux
=====

On Linux, you generally only have to install hunspell, aspell or myspell dictionaries on your
system like you do for other applications. See your distro or OS documentation for how to do this.
These dictionaries should show up as available spell check languages in novelWriter.


macOS
=====

On macOS, novelWriter uses the operating system's own spell checker, so there is nothing extra to
install. The available spell check languages are the ones provided by macOS.

macOS ships with dictionaries for a number of languages. If your language is missing, you can add
Hunspell dictionaries yourself by copying the ``.aff`` and ``.dic`` files into the folder
``~/Library/Spelling``. You may have to restart novelWriter before the new language shows up.

The language is always set by the project's spell check setting. The automatic language detection
of macOS is not used. Words you add to the project dictionary are stored in the project, just like
on the other platforms, and are not added to the system's list of learned words.


Windows
=======

For Windows, English is included with the installation. For other languages you have to download
and add dictionaries yourself.


Install Tool
------------

A small tool to assist with this can be found under **Tools > Add Dictionaries**. It will import
spell checking dictionaries from Free Office or Libre Office extensions. The dictionaries are then
installed in the install location for the Enchant library and should thus work for any application
that uses Enchant for spell checking.


Manual Install
--------------

If you prefer to do this manually or want to use a different source than the ones mentioned above,
You need to get compatible dictionary files for your language. You need two files ending with
``.aff`` and ``.dic``. These files must then be copied to the following location:

``C:\Users\<USER>\AppData\Local\enchant\hunspell``

This assumes your user profile is stored at ``C:\Users\<USER>``. The last one or two folders may
not exist, so you may need to create them.
