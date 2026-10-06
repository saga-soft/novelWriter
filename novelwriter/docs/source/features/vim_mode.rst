.. _docs_features_vim_mode:

********
Vim Mode
********

.. _Vim: https://www.vim.org/

Vim_ is a keyboard-centric text editor. "Vim mode" refers to another editor implementing the
ability to perform a subset of vim motions. This will allow you to write, select, edit, copy,
paste, navigate, etc, efficiently by using keyboard commands.

Vim is modal. Three such modes have been implemented in novelWriter:

- **Normal** mode is the default mode used to navigate text.
- **Insert** mode is where you can write text like in a 'normal' text editor.
- **Visual** mode is for selecting text, with:

  - **Visual** mode for per character selection.
  - **V-Line** mode for per-line selection.

The vim mode setting is found in the **Features** section of the **Preferences**.

.. note::

   Vim mode is an advanced feature. When you enable it, the text editor will behave very
   differently than a standard text editor. A label in the footer of the editor will show which of
   the vim modes it is in.


Mode Switching
==============

To switch between the various vim modes, these keystrokes implemented:

.. csv-table::
   :header: "From Mode", "To Mode", "Keystrokes"

   "Normal", "Insert", ":kbd:`i`, :kbd:`I`, :kbd:`a`, :kbd:`A`, :kbd:`o`, :kbd:`O`"
   "Insert", "Normal", ":kbd:`Esc`"
   "Normal", "Visual", ":kbd:`v`, :kbd:`V`"

You can exit visual mode back to normal mode by pressing :kbd:`Esc`, but all visual mode commands
that logically "terminate" the visual mode usage will return you to normal mode.

For instance, press :kbd:`V` to enter V-Line mode, select next word with :kbd:`w`. press :kbd:`y`
to yank (copy), you are now automatically put back in normal mode as you have completed selecting
your text.


Implemented Keystrokes (Vim Motions)
====================================

The table below shows the vim motions currently implemented in novelWriter.

.. csv-table::
   :header: "Motion", "Mode(s)", "Description"

   ":kbd:`i`",  "Normal → Insert", "Enter insert mode"
   ":kbd:`I`",  "Normal → Insert", "Jump to first non-blank of line and enter insert"
   ":kbd:`v`",  "Normal → Visual", "Enter character-wise visual mode"
   ":kbd:`V`",  "Normal → V-Line", "Enter line-wise visual mode"
   ":kbd:`dd`", "Normal",          "Delete (cut) current line"
   ":kbd:`x`",  "Normal",          "Delete character under cursor"
   ":kbd:`w`",  "Normal / Visual", "Move to next word start"
   ":kbd:`b`",  "Normal / Visual", "Move to previous word start"
   ":kbd:`e`",  "Normal / Visual", "Move to next word end"
   ":kbd:`dw`", "Normal",          "Delete from cursor to next word start"
   ":kbd:`de`", "Normal",          "Delete from cursor to next word end"
   ":kbd:`db`", "Normal",          "Delete from cursor to previous word start"
   ":kbd:`d$`", "Normal",          "Delete from cursor to end of line"
   ":kbd:`yw`", "Normal",          "Yank (copy) from cursor to next word start"
   ":kbd:`gg`", "Normal / Visual", "Jump to first line"
   ":kbd:`G`",  "Normal / Visual", "Jump to last line"
   ":kbd:`yy`", "Normal",          "Yank current line"
   ":kbd:`p`",  "Normal",          "Paste after current line"
   ":kbd:`P`",  "Normal",          "Paste before current line"
   ":kbd:`o`",  "Normal → Insert", "Open new line below and enter insert"
   ":kbd:`O`",  "Normal → Insert", "Open new line above and enter insert"
   ":kbd:`$`",  "Normal / Visual", "Move to end of line"
   ":kbd:`a`",  "Normal → Insert", "Enter insert after cursor"
   ":kbd:`A`",  "Normal → Insert", "Enter insert at end of line"
   ":kbd:`u`",  "Normal",          "Undo last change"
   ":kbd:`zz`", "Normal",          "Centre cursor vertically"
   ":kbd:`h`",  "Normal / Visual", "Move left"
   ":kbd:`j`",  "Normal / Visual", "Move down"
   ":kbd:`k`",  "Normal / Visual", "Move up"
   ":kbd:`l`",  "Normal / Visual", "Move right"
   ":kbd:`d`",  "Visual / V-Line", "Delete selection"
   ":kbd:`x`",  "Visual / V-Line", "Delete selection"
   ":kbd:`y`",  "Visual / V-Line", "Yank selection"
   ":kbd:`0`",  "Visual",          "Move to start of line (extend selection)"


Known Issues
============

* Currently, :kbd:`dd` on an empty line will not delete, but using :kbd:`x` will.
* :kbd:`vypyy` will have :kbd:`ypyy` in command memory and thus not register :kbd:`yy`. Expected
  behavior would be visual mode, yank, paste, yank line.
* Differing behavior from vim: the :kbd:`e` command behaves a bit differently with regards to the
  last character of a word. The behavior is inconsistent with vim but functional and still logical
  to use. The cursor is placed at the end of the word after the last character rather than on the
  last character.

  .. code-block::

     test
        ^ Cursor placed here in vim
     test
         ^ Cursor placed here in novelWriter vim mode

  You will only really ever notice this behavior if you try to combine the :kbd:`e` command with
  another. For instance, :kbd:`de` will not delete the last character but delete forward as it
  starts one character after the word boundary.
