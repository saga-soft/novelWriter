.. _docs_more_dictionaries:

************************
Spell Check Dictionaries
************************

.. _Enchant: https://rrthomas.github.io/enchant/

Spell checking is provided by the Enchant_ library. Depending on your operating system, it may or
may not load all installed spell check dictionaries automatically.


Linux and MacOS
===============

On Linux and MacOS, you generally only have to install hunspell, aspell or myspell dictionaries on
your system like you do for other applications. See your distro or OS documentation for how to do
this. These dictionaries should show up as available spell check languages in novelWriter.


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
