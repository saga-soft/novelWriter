# novelWriter Changelog

## Version 2026.2.1 [2026-09-26]

### Release Notes

This is a patch release that fixes the tag hover card icons in the editor and viewer not updating
when the app theme changed. It also adds build metadata used in crash reports and to warn users
who installed via the now deprecated Launchpad PPA. French and Russian translations have been
updated.

See the website for complete [Release Notes](https://novelwriter.io/releases/release_26_2.html).

### Detailed Changelog

**Bugfixes**

* Fixed the tag hover card icons in the editor and viewer not updating when the app theme changed.
  By @vkbo. Issue #3024. PR #3030.

**Packaging**

* Added build metadata to packages, included in crash reports to aid debugging, and used to warn
  users who installed via the now deprecated Launchpad PPA. By @vkbo. PR #3009.

**Code Maintenance**

* Improved the pkgutils CLI tool with i18n file validation and coloured terminal output. By @vkbo.
  PR #3031.

**Internationalisation**

* French translation updated by Amethystium69 and aaribaud. PR #3032.
* Russian translation updated by Kuro Ryuu and konstruktiv. PR #3032.

----

## Version 2026.2 [2026-09-05]

### Release Notes

The 2026.2 release is based on the features added in 2026.2 Beta 1, Beta 2, RC 1.

See the website for complete [Release Notes](https://novelwriter.io/releases/release_26_2.html).

### Detailed Changelog

**Bugfixes**

* Fixed a bug on macOS where using the system's native font selection dialog did not apply the
  selected font, since Qt's native panel does not confirm the choice with an OK button. By
  @kkostov. PR #2970.
* Fixed a bug from the Beta 1 release where tab widgets could show a border despite having flat
  tabs enabled. By @vkbo. PR #2971.
* Fixed a bug from the Beta 1 release where pasting rich text could repeat formatting
  unnecessarily when the source contained overlapping hidden formats. Restored the ability to
  paste as plain text, now bound to `Ctrl+Shift+V`, which was lost when rich text paste was
  introduced. By @vkbo. Issues #2978 and #2979. PR #2980.
* Fixed missing theme colours in the Dark Arts and Ruby Night themes added in the Beta 2 release.
  By @HeyMyian. PR #3003.

**User Interface**

* Changed the default line height from 1.0 to 1.15, the default font on Windows to Segoe UI, and
  reduced the default application font size from 10pt to 9pt. By @HeyMyian. Discussed in #2955.
  PR #2998.

**Other Changes**

* Bumped the project file format version to 1.6 to block the project from being opened by older
  versions of novelWriter that cannot read it correctly anyway. By @vkbo. PR #2984.

**Packaging**

* Rewrote the Debian package build to publish through a package registry, with build versions now
  selectable and Linux Mint added as a supported target. By @vkbo. PRs #2986 and #2990.

**Internationalisation**

* The Norwegian, US English, German, Italian, Japanese, Polish and Portuguese translations are
  now complete, and the Catalan translation has been updated. Translations are contributed via
  [Crowdin](https://crowdin.com/project/novelwriter). PR #2968.

----

## Version 2026.2 RC 1 [2026-08-09]

### Release Notes

This is a release candidate of the next release version, and is intended for testing purposes.
Please be careful when using this version on live writing projects, and make sure you take frequent
backups.

Note that 2026.2 Beta 2 and newer upgrades a project on first load, so it can no longer be opened
in an older version of novelWriter. 2026.2 Beta 1 and newer also updates the main config file, but
leaves the old one in place, so this is not blocking older versions but be aware that the config
changes do not pass between the old and new config files once the new config file exists.

### Detailed Changelog

**Bugfixes**

* Fixed a bug in the updated drag and drop implementation in the project tree from the Beta 1
  release. The tree no longer allowed an item to be dropped on top of another to make it a child of
  the item. Issue #2953. PR #2954.

**Improvements**

* Improved dialogue highlighting for single-quoted dialogue when the text included apostrophes.
  Discussed in #2633. PR #2956.
* Updated the new project builder so it doesn't claim the index is broken the first time it is
  opened. It is only "broken" in the sense that it is missing the first time. The index is now
  built when the project is created, so the warning no longer appears. Issue #2952. PR #2954.

**Documentation**

* Removed broken link and associated instructions on the dictionary install page. PR #2951.

----

## Version 2026.2 Beta 2 [2026-08-02]

### Release Notes

This is a beta release of the next release version, and is intended for testing purposes. Please be
careful when using this version on live writing projects, and make sure you take frequent backups.

### Detailed Changelog

**Bugfixes**

* Fixed an issue where the wrong theme colours were used for the active and inactive icons in the
  project tree context menu. Issue #2941. PR #2946.
* Removed the placeholder text in the Manuscript Tool preview since it used the wrong text colour
  on dark themes and anyway is never visible for more than a few milliseconds. Issue #2942.
  PR #2946.
* Fixed a bug from the beta 1 release where selecting a piece of text and moving it would cause a
  crash. Issue #2917. PR #2918.
* Fixed a re-entrancy bug in the project search tool. Issue #2924. PR #2937.
* Fixed a re-entrancy bug candidate in the status bar message display logic. Issue #2925. PR #2938.
* Fixed a potential segfault candidate, and an incorrect thread pool runnable in the version
  check widget. Issue #2926. PR #2938.
* Fixed a bug in the loop that collects navigation headers in the editor, which was ignoring the
  max count. Issue #2930. PR #2939.

**Improvements**

* Added more granular theme variables to improve contrast for GUI components. Issue #2910.
  PRs #2911, #2915
* Updated themes with new colours and other improvements. By @vkbo and @HeyMyian. Issue #2910.
  PRs #2911, #2912, #2916 and #2943.
* Added five new themes, by @HeyMyian. PR #2943.
* Added a character count toggle for project writing goals. Issue #2913. PR #2919.
* Removed all usages of the Qt find block methods inside loops in the editor. These are binary
  searches, not lookups, so the cost is higher than I expected. Issue #2930. PR #2939.
* The word counter ran twice on every document search. First once in the editor, then in the
  indexer. The run in the editor was removed. Issue #2928. PR #2944.

**Other Changes**

* The way the check against overwriting documents that have been changed on disk is performed has
  been improved so that it doesn't always have to read the existing document before writing.
  Issue #2929. PR #2945.
* Project documents are now saved as a text document with the `.md` extension and a standard TOML
  header instead of the old custom format and extension. Issue #1964. PR #2945.
* Pinned the Python garbage collector to the main gui thread to prevent it from accidentally
  triggering in the Qt thread pool. Issue #2927. PR #2940.
* The index cache and project-local gui state JSON files are no longer written on every autosave.
  Instead they are only written on manual saves or project close. The index cache is verified
  against a revision number on open to catch any stale caches. This was also a potential problem
  before, so this change is a general improvement. A stale cache is rebuilt on project open.
  Issue #2931. PR #2944.

**Installation**

* Added flatpak for Linux installation. Based on work by @Ryex. Issue #1651. PRs #2906 and #2908.

----

## Version 2026.2 Beta 1 [2026-07-26]

### Release Notes

This is a beta release of the next release version, and is intended for testing purposes. Please be
careful when using this version on live writing projects, and make sure you take frequent backups.

### Detailed Changelog

**Bugfixes**

* Fixed an issue with kerning when printing the manuscript preview on Windows, and changed the
  page break marker to a dashed line instead of a solid text block. Issue #2640. PR #2838.
* Fixed tooltip and scrollbar colours not matching the selected theme, a compatibility issue with
  newer versions of Qt; custom stylesheets have been replaced with other styling methods, and the
  Fusion Qt style is now hard coded, to resolve this properly. Issue #2871. PRs #2877 and #2881.
* Fixed a re-entrancy issue when opening documents, and removed a stray call that could delay
  cleanup of objects, improving overall application stability. PR #2840.
* Fixed five memory leaks related to freeing Qt objects created from Python, and added regression
  tests to catch similar issues in the future. PRs #2829 and #2830.

**Features**

* Added EPUB 3 as a new manuscript export format. Issue #2058. PR #2283.
* Added dialogue statistics to manuscripts, showing the number of characters used in dialogue and
  the ratio of dialogue to prose text. The statistics panel has been moved from below the
  manuscript preview to a new tab in the panel on the left. Issue #2096. PR #2841.
* Added a horizontal rule format for manuscript headings. Using four hyphens ("----") as a
  heading inserts a line across the page in all output formats. Issue #2755. PRs #2771 and #2772.
* Added a setting for the automatic backup interval, allowing backups to be limited to one per
  session, day, week, or month by overwriting the previous backup file, using an unambiguous
  ISO8601-based file name format. Issue #2754. PRs #2834 and #2835.
* Added a line height setting for the editor and viewer, applied consistently including to pasted
  text. Issues #654 and #2874. PRs #2817 and #2875.
* Added a text zoom feature for the editor and viewer, using the standard Qt zoom shortcuts.
  Issue #1280. PR #2822.
* Added highlighting of all search result matches in the editor, in addition to the currently
  selected one. Issues #2736 and #2798. PR #2820.
* Added a new format checker that highlights trailing spaces at the end of lines, alongside the
  existing check for multiple spaces between words. Issue #2800. PR #2821.
* Added hover cards for tags in the editor and viewer, with buttons to quickly open the
  referenced document for editing or viewing. Issue #2857. PR #2859.
* Added filters for text content, document type, and root folder to the project search tool,
  available in a new collapsible panel below the search box that updates automatically as root
  folders change. Issues #1927 and #2256. PRs #2847 and #2848.
* Added a collapsible panel widget, now used for the item details panel below the project tree
  and novel view, which can be hidden, and for the new project search filters panel. PR #2843.
* Added support for pasting rich text (HTML) into the editor, without stripping leading or
  trailing whitespace. Issue #2601. PRs #2876 and #2878.
* Added project writing goals with daily progress tracking, shown as progress bars with
  sufficient colour contrast in all themes, and correctly reset when starting a new day. Also
  added an option to exclude specific root folders from the count. Based on work contributed by
  @BlayW. Issue #2223. PRs #2870, #2878, #2887, #2889, #2891 and #2892.
* The symbol auto-replace feature can now also be used in the editor's search and replace boxes,
  the project search box, and the header format field in Manuscript Build Settings, and can be
  toggled on or off in each. Issue #2261. PRs #2866, #2867 and #2868.
* It is now possible to recursively set the active or inactive state of all documents under a
  folder in the project tree from the right-click menu. Issue #2188. PR #2784.
* A checkbox now shows the active project's spell check language in the Tools menu, and the spell
  checker is re-run automatically when the language is changed. Issue #2311. PR #2785.

**Improvements**

* Manuscript Build Settings now has an option to enable or disable justify-expansion of lines
  with manual line breaks, extended to Open Document and Word Document formats. Issue #2764.
  PRs #2769 and #2770.
* The reference list panel now refreshes automatically when the references in a document change,
  instead of requiring a manual refresh. Issue #2124. PR #2782.
* Keypress handling in the editor's auto-complete menu has been improved: arrow keys navigate the
  list, Left and Escape close it, and Tab, Enter, Return, and Right accept the highlighted entry
  or close the menu if nothing is selected. Issue #2742. PR #2743.
* The editor's auto-complete menu has been rewritten to use Qt's native completer widget instead
  of a custom menu, improving its look and behaviour. PR #2856.
* Performance of the spell checker has been substantially improved by caching computed highlights
  and dictionary lookups, and syntax highlighting and spell checking are now skipped for
  excessively long paragraphs (over 20 000 characters) to keep large documents responsive. A
  related concurrency issue in the background word counter has also been fixed. PRs #2808, #2861,
  #2862 and #2863.

**User Interface**

* Toggle buttons, such as those in the search tools, are now more visible when active, using a
  new "toggle" theme colour. A new "searchMatch" theme colour is also used to highlight search
  matches in the editor and project search results, and now refreshes immediately when switching
  themes. Existing themes have been updated accordingly, including contributions by @HeyMyian.
  Issues #2827, #2845 and #2886. PRs #2833, #2844, #2846, #2882 and #2887.
* Restored the flat look of tabs in tab widgets, now implemented with a custom painter instead of
  stylesheets for better compatibility with recent versions of Qt. PR #2890.
* Fixed handling of long labels in switches, and in the quick link and header navigation
  menus. PR #2850.

**Other Changes**

* The document editor's underlying text widget has been switched back to a full rich text editor
  instead of a plain text editor, enabling several of the features in this release, such as line
  height, zoom, and pasting rich text; copying text from the editor still produces plain text as
  before. This also required narrowing down when the editor is re-initialised, which had caused
  some Preferences settings to stop refreshing the GUI properly. Issue #2815. PRs #2816, #2860 and
  #2878.
* Spell checking has been moved out of the syntax highlighter and now runs as a chunked, timed
  background process, using the same block-based caching approach as the new search highlighting.
  PR #2812.
* The application configuration file and all theme files have been converted from Linux-style
  config formats to TOML. PRs #2883 and #2885.
* The project search panel has been internally rewritten to use a model/view architecture, with
  no intended functional change. PR #2842.
* Internal handling of icons has been changed, with no expected functional impact. PR #2852.
* The viewer code has been merged into the editor folder ahead of further refactoring work.
  PR #2880.
* Cleaned up how menu actions with additional data, such as icons and custom data, are created
  internally. Issue #2828. PR #2832.

**Code Maintenance**

* Enabled branch coverage in the test suite, added tests for previously uncovered branches, and
  fixed a few minor bugs found in the process. PR #2807.
* Hardened flaky tests to reduce occasional segfaults during test runs. PR #2864.
* Updated the default Python version used for testing and embedded in builds to 3.14. PR #2786.
* Updated the Ubuntu versions targeted by packaging and CI. PR #2802.
* Updated icon packages, test helper scripts, and documentation build tooling. PR #2853.
* Added tests to the Debian package build process. PR #2896.
* Various internal linting, naming, and code style improvements, including dropping the redundant
  `NW` prefix from most class names. PRs #2779, #2826 and #2831.

----

## Version 2026.1.2 [2026-07-25]

### Release Notes

This is a patch release that fixes a race condition when searching across multiple documents,
restores the application's taskbar icon on Windows, and fixes a font setting that failed to load
on older versions of Qt. Japanese and Russian translations have also been updated.

### Detailed Changelog

**Bugfixes**

* Fixed a race condition when searching through multiple documents that could cause a crash if
  the next match button was pressed too quickly. Issue #2809. PR #2811.
* Fixed the application icon not showing on the Windows taskbar. Issue #2728. PR #2824.
* Fixed loading of a font setting saved with Qt 6.11 when running on older versions of Qt.
  PR #2849.

**Internationalisation**

* Japanese translation updated by @hebekeg. PR #2897.
* Russian translation updated by Kuro Ryuu (kuroryuu) and Konstantin Tan (@k1kimosha). PR #2897.

----

## Version 2026.1.1 [2026-06-28]

### Release Notes

This is a patch release that adds Catalan language to the app, and updates translation files for
other languages. Some user interface labels for the Manuscript tool have been improved, and the
documentation updated. A small fix resolves an error message printed to the log when launching the
app on Linux.

### Detailed Changelog

**Bugfixes**

* Fixed a DBus error message from Qt on Linux. PR #2790.

**Improvements**

* Clarified some of the GUI labels on the Manuscript tool. Issue #2762. PR #2768.

**Internationalisation**

* Catalan translations added by @jaumeplanas. PR #2793.
* Norwegian and US English translations updated by @vkbo. PR #2793.
* Japanese translation updated bu @hebekeg. PR #2793.
* German translation updated by @HeyMyian. PR #2793.
* Polish translation updated by @Nauthizz. PR #2793.
* Dutch translation updated by @risingphoenix73. PR #2793.
* Italian translation updated by Lou Cyper. PR #2793.
* Chinese translation updated by wcxu21 and @longqzh. PR #2793.

**Documentation**

* Fixed some typos in the documentation. PR #2773.
* Improved the documentation for the Manuscript tool. Issue #2763. PR #2768.
* Switched the documentation back to using `uv` for examples. PR #2766.

----

## Version 2026.1 [2026-04-26]

### Release Notes

The 2026.1 release is based on the features added in 2026.1 Beta 1, Beta 2, RC 1.

See the website for complete [Release Notes](https://novelwriter.io/releases/release_26_1.html).

### Detailed Changelog

**Improvements**

* When exporting manuscripts to DocX (Word), the document will no longer expand hard line breaks by
  when default when justified margins are enabled. Issue #2690. PR #2732.
* The "Add titles for notes" label in **Manuscript Build** settings has been updated and should now
  be clearer. Issue #2727. PR #2729.

**Internationalisation**

* A missing translation string for projects was added. Issue #2730. PR #2731.
* Norwegian and US English translations updated by @vkbo. PR #2738.
* Japanese translation updated bu @hebekeg. PR #2738.
* Dutch translation updated by @risingphoenix73. PR #2738.
* German translation updated by @HeyMyian. PR #2738.
* Polish translation updated by @Nauthizz. PR #2738.
* Latin American Spanish translation updated by @tmarplatt. PR #2738.
* Czech translation updated by Tomáš Zmek. PR #2738.
* Italian translation updated by Lou Cyper. PR #2738.

----

## Version 2026.1 RC 1 [2026-04-13]

### Release Notes

This is a release candidate of the next release version, and is intended for testing purposes.
Please be careful when using this version on live writing projects, and make sure you take frequent
backups.

Note: There are no longer any Mac releases produced for novelWriter. See #2618.

### Detailed Changelog

**Bugfixes**

* Fixed an issue where the editor and viewer header no longer changed colour when losing or gaining
  focus. Issue #2716. PR #2717.
* Fixed the project list tooltip on the Welcome dialog. Issue #2714. PR #2715.
* Fixed the size of spin boxes on config forms. Issue #2703. PR #2711.

**Features**

* A new setting in Preferences allows for the usage of single asterisks for bold formatting.
  Enabling this setting does not disable double asterisk bold. Issue #2718. PR #2719.

**User Interface**

* Adjusted some colours of icons in several themes to bring them visually in line with the rest of
  the theme. Contributed by @HeyMyian. PR #2712.

**Internationalisation**

* Updated translation strings. PRs #2721 and #2722.
* Updated Dutch translation by @risingphoenix73. PRs #2721 and #2722.
* Updated US English and Norwegian translation by @vkbo. PRs #2721 and #2722.

**Other Changes**

* GUI font emphasis is now handled by the theme class, and bold text on the GUI has been reduced in
  weight to semibold. Issue #2709. PR #2710.

----

## Version 2026.1 Beta 2 [2026-04-04]

### Release Notes

This is a beta release of the next release version, and is intended for testing purposes. Please be
careful when using this version on live writing projects, and make sure you take frequent backups.

Note: There are no longer any Mac releases produced for novelWriter. See #2618.

### Detailed Changelog

**Bugfixes**

* An unchecked dependency on Qt 6.9 has been fixed. If the app was running in an environment with
  an older Qt version, the app would crash when opening one of the settings dialogs. This should
  only affect the Debian packages since the Windows and AppImage releases bundle Qt 6.11.
  Issue #2706. PR #2704.

----

## Version 2026.1 Beta 1 [2026-04-02]

### Release Notes

This is a beta release of the next release version, and is intended for testing purposes. Please be
careful when using this version on live writing projects, and make sure you take frequent backups.

Note: There are no longer any Mac releases produced for novelWriter. See #2618.

### Detailed Changelog

**Bugfixes**

* The URL highlighting now also works if the URL has an exclamation point. Issue #2693. PR #2695.
* The margin settings in Manuscript Build settings now correctly shows icons to indicate margin
  type. PR #2647.

**Features**

* The novelWriter version number is now year-based. Instead of the next release being 2.9, it is
  now 26.1 or 2026.1 as shown in the app. Discussion #2667. PR #2669.
* Added the Lucide icon theme as a user-selectable icon theme. Issue #2605. PR #2632.
* It is now possible to split a document via text selection, or at the cursor position, from the
  right-click menu in the editor. Issues #1486 and #2571. PR #2688.
* The shortcuts `Ctrl+Up` and `Ctrl+Down` now move the cursor between paragraphs in the editor.
  Issue #2635. PR #2679.
* The size of the different heading levels can now be adjusted in the Manuscript Build settings
  tool. Issue #2439. PR #2650.
* Added a setting for manuscripts to use blank lines instead of margins in manuscript document
  formats. Issue #2648. Discussion #2646. PR #2649.
* A new "Heading Format" sections is available in Manuscript Build settings. The settings for bold
  and colourised headings have been moved there, and a new setting to make them uppercase has been
  added. PR #2647.

**Improvements**

* Added word or character units to count tooltip labels in project tree and novel view. PR #2698.
* The note document associated with a reference can now be opened in the editor from the
  right-click menu. Issue #2448. PR #2697.
* The `Shift+Enter` shortcut now also works in the project search, and opens the document in the
  viewer. However, it cannot show the actual search result since the search itself is performed on
  the raw plain text document and doesn't apply to the generated document in the viewer.
  Issue #2661. PR #2697.
* Backward searches in the editor can now also iterate backwards in project documents if the option
  to continue search in the next document is enabled. Issue #1451. PR #2696.
* Error handling when encountering file system issues has been improved and hardened. It should
  further prevent application crashes when encountering such issues. Issues #2529 and #2671.
  PRs #2675 and #2683.
* The document header in the editor and viewer panels have been improved. An issue with clipping of
  the descending characters have been fixed, and each part of the path can be clicked to highlight
  it in the project tree. Issues #2664 and #2674. PR #2677.
* Added a setting in Preferences that turns off scaling of headings in the editor, which is more
  consistent with plain text where all text is the same size. Issue #2636. PR #2670.
* Improved the way version numbers are shown in the Welcome dialog, allows the selected project to
  be opened with the Enter key, and using the arrow keys will move the selection up and down
  without first having to switch focus to the recent projects list. PR #2668.

**Accessibility**

* Improved screen reader support for remaining buttons, and improved reading of settings pages in
  various dialogs. Issue #2338. PR #2698.
* Two new light colour themes for colour blindness has been added. They are "Today Deuteranopia"
  for red/green colour blindness, and "Today Tritanopia" for blue colour blindness. Issue #2689.
  PR #2694.
* Added an option in Preference to show dotted lines under formatting codes in the editor. This is
  a visual aid in addition to highlighting colours. Issue #2691. PR #2692.

**Internationalisation**

* Updated translation files with some new translations since the 2.8 release. PR #2699.

**Other Changes**

* The fun Discworld themed titles shown on error windows have been extended with new titles to
  randomly select from. PR #2684.
* PDM has replaced UV as the dependency manager for development and testing. This should not matter
  to end users. Issue #2685. PR #2678.

----

## Version 2.8.2 [2026-01-25]

### Release Notes

This is a patch release that fixes an issue with launching novelWriter via a project file on
Windows, adds an alert when the spell check dictionary cannot be loaded, handles headings in HTML
manuscripts the same way as for documents, and updates the documentation on how heading levels are
handled in the manuscript build process.

### Detailed Changelog

**Bugfixes**

* Fixed an issue with the exe launcher on Windows where it didn't support spaces in the path when
  the user tried to open novelWriter from a project file. Issue #2643. PR #2645.
* Fixed an issue with the PDF manuscript format which stopped after about 600-700 pages when
  generating A4 pages. The limit is now in the 11000 pages range. Issue #2637. PRs #2638 and #2639.

**Improvements**

* Added an alert box when the spell check language selected for a project could not be loaded.
  Issue #2631. PR #2654.
* The HTML manuscript format now exports novel title and partition titles as paragraphs with a
  larger font size instead of HTML headings. This is more consistent with the other formatted
  document formats. Issue #2641. PR #2653.

**Documentation**

* Added information to the documentation about heading level promotion when building the
  manuscript. Issue #2641. PR #2653.

----

## Version 2.8.1 [2025-12-28]

### Release Notes

This is a patch release that fixes an issue where the application could crash due to a change in
PyQt/Qt 6.10. The issue is related to certain input methods, and is at least triggered when using
Spotlight on MacOS.

### Detailed Changelog

**Bugfixes**

* Fixed an issue where the inputMethodQuery call to the Qt library returns an object that PyQt6
  cannot convert to a Python object. The fix just disables the conversion since the return value is
  passed back to the Qt library anyway. The problem affects Qt/PyQt 6.10 and is triggered in MacOS
  at least, but it is not known if it affects other platforms. Issue #2622. PR #2623.

**Documentation**

* Removed references to the old colour theme system in the documentation. Issue #2619. PR #2625.

----

## Version 2.8 [2025-12-14]

### Release Notes

The 2.8 release is based on the features added in 2.8 beta 1 and 2.8 RC 1.

See the website for complete [Release Notes](https://novelwriter.io/releases/release_2_8.html).

### Detailed Changelog

**Bugfixes**

* Fixed an issue where the app could crash when the user pasted from an empty clipboard. This
  appears to be a Qt or PyQt bug, and is not present on the later releases, but a fix has been
  added that ensures the bug is not triggered. Issue #2598. PR #2602.

**Documentation**

* Fixed a broken link in the updated 2.8 docs. PR #2595.

**Internationalisation**

* Updated Czech, German, US English, Italian, Japanese, Norwegian and Chinese translation files
  from the Crowdin project page. PR #2608.

**Packaging**

* Added `qt6-svg-plugins` as a direct dependency of novelWriter on Debian. This package was not
  always installed on some distros. Issue #2604. PR #2607.

----

## Version 2.8 RC 1 [2025-11-30]

### Release Notes

This is a release candidate of the next release version, and is intended for testing purposes.
Please be careful when using this version on live writing projects, and make sure you take frequent
backups.

### Detailed Changelog

**Bugfixes**

* Fixed a bug that would block the return key in the editor if French style space padding was
  enabled in Preferences. Issue #2586. PR #2587.
* Fixed an issue where dialog state was no longer saved properly when they were closed for many
  dialogs. This may be due to a change in the Qt framework, or a bug from a previous release.
  PR #2585.
* Fixed an issue where a confusing error would show up if the user cancelled the file dialog during
  example project creation. A new dialog now tells you what the actual issue was and sends you back
  to the welcome dialog. Issue #2590. PR #2592.

**Features**

* Vim mode has been added to the editor, and can now be enabled in Preferences. Contributed by
  @idealemu. Issue #2493. PRs #2499 and #2588.

**Improvements**

* Using format button from the editor toolbar will not apply the formatting on lines that cannot
  take formatting, like headings and meta data lines. Issue #2560. PR #2575.
* Added an option in Preferences that will try to centre the main app windows during startup. This
  effect is always triggered if the main window is scaled down at startup due to being opened on a
  smaller screen. Issue #2579. PRs #2580 and #2581.
* The example project has been updated and improved. Issue #2570. PRs #2572 and #2574.
* The spacing between icon and text in push buttons has been increased. PR #2582.
* The font selection dialog now remembers its previous size, and uses the new standard push buttons
  instead of the Qt defaults. PR #2584.
* It is now possible to override the manuscript language meta value for document formats that have
  this. The IETF BCP 47 language tag is used. Issue #2328. PR #2593.

**Internationalisation**

* Updated US English, Italian, Norwegian, and Japanese translations. PR #2589.

----

## Version 2.8 Beta 1 [2025-10-29]

### Release Notes

This is a beta release of the next release version, and is intended for testing purposes. Please be
careful when using this version on live writing projects, and make sure you take frequent backups.

### Detailed Changelog

**Bugfixes**

* The editor now properly supports 4 byte Unicode characters without breaking the syntax
  highlighting and spell checker. Issue #2449. PR #2451.
* Fixed a bug in the font matching code where the style name property for the font was set,
  preventing Qt from picking a proper styled font. Issue #2502. PR #2503.
* Spell check dictionaries in the main menu are now updated when new dictionaries are installed
  using the add dictionaries tool. Contributed by @Reproog. Issue #2558. PR #2562.
* Fixed an issue where the Novel Tree panel heading would be greyed out if there was only one Novel
  root folder. Issue #2482. PR #2556.

**Features**

* Current line highlighting has been added and can be enabled in Preferences. Issue #1321.
  PR #2405.
* The Status and Importance labels can now use theme colours in addition to a user defined custom
  colour. The settings for these labels have also been made clearer. Issues #2357, #2366 and
  #2452. PRs #2400 and #2461.
* Markdown style highlighting tags are now supported in the editor. Issue #1894. PR #2412.
* Synopsis/short comments, story comments, and story notes can now be used multiple times under a
  heading. The text is just appended as a new paragraph each time the annotated comment type is
  encountered. Issue #2483. PR #2543.

**Improvements**

* You can now press `Ctrl+T` and `Ctrl+Shift+T` when in Focus Mode to exit the Focus Mode
  automatically and switch to the Project Tree or Outline View. Issue #1294. PR #2479.
* When creating a new document from a template, the first title of the template document is
  replaced with the label text set for the new document. Issue #2238. PR #2477.
* When the app is performing a potentially bulky and time consuming task, a small progress bar will
  appear at the top of the status bar to show the progress of the task. It is currently used when
  the index is rebuilt and when processing multiple documents in the Project Tree. Issue #2243.
  PR #2478.
* The auto-replace feature in the editor is now better at detecting opening and closing quotes when
  used in relation to markdown style markup. Issue #2488. PR #2489.
* The application window is now blocked from resizing itself to a size larger than the screen when
  opened on a smaller screen than it was previously opened on. Like for instance when it was
  connected to an external screen from a laptop. Issue #2354. PR #2369.
* Improved the CSS styling of HTML manuscript documents. Issue #2358. PR #2404.
* Trailing spaces are no longer highlighted in the editor with an error underline. Multiple spaces
  between words still are. Issue #2501. PR #2505.
* The rebuild index dialog is no longer showed if the index is rebuilt due to index structure
  changes when a project is opened for the first time in a newer version of novelWriter. This was
  confusing to some users who thought the dialog indicated an error. Issue #2513. PR #2537.
* A switch on the Manuscript Build Settings dialog now allows for automatic preview of the build
  when Apply or Save is clicked. Issue #2486. PR #2553.
* Formatting and handling of Story Comments and Story Notes have been improved, and they can be
  filtered separately in the viewer panel. PR #2421.

**User Interface**

* The GUI and syntax themes have been merged into a single theme, which means there are no longer
  separate settings for the general GUI and the document colour theme. Issue #2335. PR #2373.
* There are now two GUI theme settings in Preferences, one for light and one for dark mode. A new
  button on the sidebar allows you to switch between them, or it can be set to auto mode that
  follows the operating system's light/dark mode. Issues #1173 and #2487.
  PRs #2373 and #2545.
* More themeable settings have been added. The document active flag, the theme base colour, and the
  new GUI accent colour (if Qt version is high enough) is now available. Issue #2382. PR #2384.
* The highlighting colour for special white spaces, like non-breaking spaces, can now be set in the
  theme. Previously it used the emphasis colour. Issue #2547. PR #2548.
* The Welcome dialog background now follows the theme colours. Issue #2379. PR #2380.
* The dialog buttons now use icons from the selected theme, not from the host OS. Issues #2498,
  #2551 and #2561. PRs #2544, #2546, #2553, #2557 and #2563.
* Added semantic categories for icon colours which can be defined in the colour theme. PR #2549.
* Primer Dark and Primer Light themes added by @HeyMyian. Issue #2376. PRs #2377 and #2419.
* Horizon, Otium, Paragon, Selenium, Sepia, Sultana, Vivid, Warpgate, and Waterlily themes added by
  @HeyMyian. Issue #2407. PR #2495.
* Aura, B2T Garden, B2T Suburb, B4T Classic-O, B4T Modern-C, Everforest, New Moon, Full Moon, Nord,
  Nordlicht, Castle, Chernozem, Chalky Soil, Floral, Ruby themes added by @HeyMyian. PR #2450.
* Blue Streak themes added. PR #2388.
* LCARS theme added. PR #2399.
* Espresso and Noctis themes added. PR #2422.
* Various improvements to existing and new themes by @vkbo. PRs #2396, #2418, #2475 and #2481.
* Various improvements to existing and new themes by @HeyMyian. PRs #2506 and #2494.

**Packaging**

* The license info for novelWriter has been updated to include `GPL-3.0-or-later`, `Apache-2.0`,
  and `CC-BY-4.0`. Issue #2444. PR #2446.
* Updated Debian package build and added Qt6 plugin for WebP images as a dependency. PR #2401.

**Documentation**

* Added some info on how to get around the line heigh issue in the editor in the Tips & Tricks
  section of the documentation. Issue #2559. PR #2564.
* Fixed some typos in the documentation. PR #2542.

**Code Maintenance**

* Improved linting and added more mapped Qt constants. PR #2536.
* Added test coverage of the theme files to ensure they are up to date. PR #2378.
* Updated credits and license information of icon themes. PR #2474.
* Some fields have been dropped from icon and colour themes. PRs #2466 and #2423.
* Changed a few default settings in config, added automatic rebuild of the index in new projects,
  and fixed tests. PR #2395.
* Added test coverage and support for Python 3.14. PR #2538.
* Improved logging formatting by stripping HTML content. PR #2402.
* Cleaned up and improved pkgutils CLI tool. PR #2541.
* The project now uses UV as the primary dependency handling tool for development. PR #2540.
* Fixed the run_tests helper script for HighDPI monitors. PR #2496.

----

## Version 2.7.5 [2025-09-14]

### Release Notes

This is a patch release that fixes an issue related to crashes when using the completer menu under
certain conditions, and improves positioning of the input box for CJK languages.

### Detailed Changelog

**Bugfixes**

* Fixed an issue where the app would crash of deleting the `@` character with the completer menu
  visible and the text margins of the editor set to "justified". This is likely crashing due to
  some unhandled corner case in the Qt library, but the implementation of the completer menu in
  novelWriter uses a small hack to bypass some intended behaviour of the menu. Extra steps have
  been added to the implementation that seems to avoid the crash. Issue #2510. PR #2511.
* Fixed an issue where the input box that shows up when typing CJK languages were covering the text
  due to an incorrect offset of the box location. The incorrect offset is caused by the text
  margins not being taken into account. Fix by @Euophrys based on solution by @Jack-name.
  Issues #2267 and #2517. PR #2518.

----

## Version 2.7.4 [2025-07-15]

### Release Notes

This is a patch release that updates the Czech and French translations, and makes some changes to
the available Material Symbols icon themes. Additional icon themes are no longer automatically
included in all release packages due to license constraints.

### Detailed Changelog

**Internationalisation**

* The Czech and French translations are now complete. PR #2469.

**Packaging**

* Only the Material Symbols icons are included by default in packages. Other icon themes are
  included depending on licensing restrictions for free and non-free requirements. The Material
  Symbols Bold themes have been dropped, and a Sharp theme added. Issue #2462. PR #2467.

----

## Version 2.7.3 [2025-07-07]

### Release Notes

This is a patch release that fixes a bug in, and makes a few improvement to, Preferences.

### Detailed Changelog

**Bugfixes**

* Fixes an issue where novelWriter would crash if a `%` was added to any of the free text settings
  fields in Preferences. Issue #2455. PR #2456.

**Improvements**

* The "Dialogue line symbols" setting in Preferences now has an "Add" button with a dropdown menu
  for all the symbols allowed in this field. Since virtually none of them are available on a
  regular keyboard, this makes it easier to add them and more transparent which symbols are allowed
  in the box. Issue #2453. PR #2457.
* The switch for the "Allow open-ended dialogue" setting in Preferences has been moved up one line
  so it is clearer that it only applies to quoted dialogue, and not to the alternative dialogue
  settings. Issue #2454. PR #2457.

**Packaging**

* Package license information has been updated to also list the licenses for the new icon themes.
  Issue #2434. PRs #2435 and #2458.

----

## Version 2.7.2 [2025-06-24]

### Release Notes

This is a patch release that fixes several issues related to DocX and PDF manuscript documents,
improves how line breaks, alignment and indentation is processed, and fixes some issues with
displaying tags for novel documents on the user interface.

### Detailed Changelog

**Bugfixes**

* Fixed an issue where escaped markup characters were not replaced properly in DocX and PDF
  documents, and in previews. Issue #2410. PR #2411.
* Fixed an issue where titles with line breaks in them would have page breaks applied to both lines
  for preview and PDF documents. Issue #2415. PR #2416.
* Fixed an issue where the justified text setting would not be properly applied to a paragraph in a
  manuscript document if there was a line break in the paragraph, but single line breaks were set
  to be ignored. Issue #2426. PR #2427.
* Fixed an issue where the "Tag" field of the Outline View details panel remained blank even if a
  tag was set for the novel document. Issue #2428. PR #2429.

**Improvements**

* When comments are enabled in the viewer, story comments should also be visible. A separate filter
  button will be added for this in 2.8. PR #2420.
* When a paragraph has line breaks in it, the alignment tag will now override first line
  indentation even if the alignment tag is not on the first line. This is more consistent with the
  alignment behaviour for multi-line paragraphs in general. Issue #2425. PR #2427.
* Tags will now be shown in the Novel View tooltip pop-out under the triangle button, together with
  all the other meta data collected about a document or heading. PR #2429.

**Documentation**

* The documentation on how alignment and first line indentation works in conjunction with
  in-paragraph line breaks, the setting to keep or ignore such line breaks, and the forced line
  break shortcode, has been improved. Issue #2425. PR #2427.

----

## Version 2.7.1 [2025-06-09]

### Release Notes

This is a patch release that fixes some issues with tags and references, an issue with the
auto-complete menu on Windows, and some issues with the AppImage on Linux. The Czech translation
for 2.7 has also been completed.

### Detailed Changelog

**Bugfixes**

* Fix a bug where tags would be listed in the auto-complete menu for mentions even if the file
  defining it had been moved to Archive or Trash. Issue #2387. PR #2389.
* Fixed a bug that seems to only have occurred on Windows where the auto-complete menu would hold
  on to the return and arrow keys even when it was hidden. Issue #2386. PR #2389.

**Improvements**

* The auto-complete menu in the editor no longer shows any suggestions when defining the tag.
  This never made sense anyway. PR #2389.

**Internationalisation**

* Updated the Czech. PR #2393.

**Packaging**

* Fixed an issue with the AppImage release where on some platforms `libxcb-cursor0` was missing.
  The library is now included in the AppImage. Issue #2374. PR #2392.

----

## Version 2.7 [2025-06-01]

### Release Notes

The 2.7 release updates the 2.7 RC 1 release and makes an improvement to the build settings tool.
It also updates most translations and updates the French version of the documentation.

See the website for complete [Release Notes](https://novelwriter.io/releases/release_2_7.html).

### Detailed Changelog

**Improvement**

* The Manuscript Build Settings dialog now works on a copy of the settings so that if the dialog
  box is closed without saving, all changes are discarded. It should also now detect any change
  made to properly raise a confirmation prompt when closing without saving. Issue #2350. PR #2351.

**Documentation**

* The user documentation has been restructured, and the Getting Started section has been made less
  technical. The install instructions have been moved out and into the main website. The technical
  and in-depth parts of the documentation have been kept, but moved further back so that the
  documentation can be read from the start and to the point where the user has enough information.
  The larger sections have also been split up so that it should be easier to find the wanted
  information directly from the menu. Issue #2345. PR #2355.

**Internationalisation**

* Updated US English, Japanese, Norwegian. German, Italian, Polish, Brazilian Portuguese and
  Chinese translation files. PR #2353.
* French documentation updated by @Karduin. Issue #2360. PR #2361.

----

## Version 2.7 RC 1 [2025-05-19]

### Release Notes

This is a release candidate of the next release version, and is intended for testing purposes.
Please be careful when using this version on live writing projects, and make sure you take frequent
backups.

### Detailed Changelog

**New Features**

* It is now possible to set character count as the main statistics displayed on the GUI instead of
  word count. The setting is available under the "Appearance" section in Preferences. Issue #1657.
  PR #2323.
* Comments can now be marked as "Manuscript Notes" with the `%Note.term:` syntax. The term is a
  free form value that is displayed alongside the note when exported to the manuscript. Each term
  is also added as a column in exports from the Outline View. Issue #1133. PR #2346.
* A completer drop down menu has been added to comments as well in the editor. It is triggered when
  a new line starts with `%`. It will show the options of Synopsis, Short, Story and Note, and when
  a period is added after the latter two, show a list of previously used Story and Note keys.
  Issue #1784. PR #2290.

**Improvements**

* The dialogue colour of the Snazzy Light syntax theme has changed from yellow to blue, which
  should make it easier to read. PR #2336.
* The Snazzy Light theme has also been added as a GUI theme. PR #2334.
* The auto-generated title page for new projects should now make a little more sense in terms of
  default values filled in for the author. PR #2333.
* The new project form on the Welcome dialog now remembers the previous author name filled in, so
  there should be no need to type it again every time. PR #2333.
* Project name and author name values are now also used for new example projects. PR #2333.
* The narrator break symbol settings for dialogue have been changed from a free text field to a
  dropdown list of dashes. This helps to avoid misunderstandings where the field was populated with
  other symbols, like quote symbols (see #2320). Issue #2324. PR #2327.
* A splash screen is now shown at startup, providing some information about the initialisation
  steps the startup script is running before the GUI is launched. Since loading system fonts can be
  quote heavy, this at least gives some user feedback to users running on systems where there is a
  significant delay. In particular, there is a long delay when loading fonts with poor Unicode
  support, in which case the Qt library will look for replacement glyphs when the symbols are first
  encountered. Previously, the delay happened when the Welcome dialog was being drawn, since this
  is the first time a non-Ascii Unicode character is used. Now these Unicode characters are probed
  when the config is loaded, with progress output on the splash screen. Issue #2315. PR #2316.

**Bugfixes**

* Moving a note between root folders of a different type will now update the class the tags defined
  within the note are associated with. This association is used to populate the tag auto-completion
  in the editor. Issue #2330. PR #2343.
* The story structure comments now appear under the correct column when exported to CSV from the
  Outline View. Issue #2313. PR #2343.
* A new unique ID is now assigned to new example projects. Creating multiple example projects would
  previously retain the original ID, causing the Welcome dialog to override them rather than list
  them as unique projects. PR #2333.
* In Qt6, or probably in PyQt6, the datetime type from Python was truncated to a date variable when
  localising it. This has been fixed by explicitly converting the Python datetime to a QDateTime
  before passing it to the PyQt wrapper. This is probably a bug in PyQt6. Issue #2325. PR #2326.
* A missing Remix icon for project copy has been added. Issue #2314. PR #2317.

**Accessibility**

* Trees and lists on the GUI have been assigned names so that screen readers can more easily
  identify them. Switches on the GUI have also been associated with their labels so the screen
  reader can pick up the label text. Icons on the project tree also have an accessibility label.
  Issues #2106 and #2107. PR #2337.
* Switches should now show a highlighted border when they have focus, and the toggle animation also
  now works properly when a switch is toggled using the keyboard. This should improve keyboard
  navigation. PR #2337.
* The default status and importance labels for new projects now use shapes for icons, to make the
  defaults more accessible for people with reduced colour vision. Issue #2332. PR #2333.

**Code Improvements**

* New tests have been added for the custom data models, using the Qt model tester framework that
  ensures the models have all the virtual methods implemented. PR #2331.

----

## Version 2.7 Beta 1 [2025-04-20]

### Release Notes

This is a beta release of the next release version, and is intended for testing purposes. Please be
careful when using this version on live writing projects, and make sure you take frequent backups.

### Detailed Changelog

**New Features**

* The TypIcons icon set has been dropped and all individual icon files removed. Instead, three new
  icon themes have been added in a total of nine different variations. These icon themes are kept
  in single files and generated from official sources. They are also colourised at runtime using
  the GUI theme colours for consistency. Issue #2159. PRs #2171, #2174, #2177, #2178 and #2203.
* Support for Story Structure comments have been added. These are special in-text comments that can
  be used for analysing the story structure using various writing techniques. The comments are
  indexed by novelWriter and can be included in manuscripts as well as exported to CSV files from
  the Outline View for use with spread sheet software. Idea and documentation by Alan Langford
  (@instancezero). Issues #1784, #2288, #2289 and #2296. PRs #2255, #2284, #2293, #2295 and #2298.

**Improvements**

* The thickness of the editor cursor can now be set in Preferences. Issue #2219. PR #2230.
* The Novel View has been rewritten from scratch using a model/view framework. Several minor issues
  were resolved in the process. Issues #942 and #2253. PR #2272.
* The logic of where new documents are added in the project tree has been rewritten and improved.
  The algorithm should now avoid adding chapters within chapters when a scene inside a chapter is
  selected. Otherwise the behaviour should be similar to before, but it will now also apply the
  same logic when new documents are created from templates. Issue #2260. PR #2302.
* Dialogue highlighting should now work a little better for single quoted dialogue when it
  encounters apostrophes in the same text. Issue #2271. PR #2300.
* Quoted text is no longer highlighted as dialogue in the editor when the document is a project
  note. This is consistent with how the viewer and manuscript tool work. Issue #2297. PR #2299.

**Documentation**

* Internationalisation for the documentation is now properly supported in the code base, and new
  contributions are possible. Discussion #1834. PRs #2224 and #2227.

**Internationalisation**

* French translation files for the documentation were added by @Karduin. PR #2226.

**Packaging and Installation**

* The move to Qt6 is complete, and the new minimum requirement is Qt 6.4. Issues #864, #1142,
  #2192, #2193, #2194 and #2195. PRs #2184, #2187, #2190, #2191, #2196, #2204, #2301 and #2306.
* Support for Python 3.9 has been dropped. Due to the Qt6 change, older distros are no longer
  supported. The oldest Ubuntu release still supported is 24.04. PR #2182.
* The Windows release now uses a custom novelWriter.exe launcher rather than calling the Python exe
  directly with novelWriter.pyw as an argument. This means novelWriter can also be launched from
  its install folder, and desktop shortcuts created directly. It also simplifies the registry
  entries. PRs #2197, #2198 and #2199.
* The Appdata XML files used with AppImage releases has been updated and broken links fixed.
  PR #2229.
* RPM packages are now available for the 2.6.3 release on Fedora 41 and 42. Several minor
  adjustments to the code base has been made to make the packaging process easier for the 2.7
  release. The Fedora releases are maintained by Benson Muite (@bkmgit). Issues #907, #2276 and
  #2303. PRs #2305 and #2307.
* The shebang from the launch script on Windows has been removed. Issue #1284. PR #2280.

**Code Improvements**

* The log output now obeys the `NO_COLOR` and `FORCE_COLOR` environment variables. PR #2228.
* The CI/CD pipeline now runs type checking on the code base using Pyright. PR #2279.
* The CI/CD pipeline now uses Ruff to check code style and format. PRs #2281, #2282 and #2287.
* The code base has been updated to conform to new linting rules. PR #2201.

----

## Version 2.6.3 [2025-02-16]

### Release Notes

This is a patch release that fixes a translation issue that affected several labels on the user
interface where the wrong or no translation was used. The bug affected all languages except for
English.

### Detailed Changelog

**Bugfixes**

* Fix retrieval of translation string for stats and shape constants. This particularly affected the
  details panel below the project tree, some labels on the outline, the statics panel on the
  Manuscript tool and the status icon shape menu in Project Settings. It also affected the
  statistics submenu in the Insert menu. Issue #2246. PRs #2247 and #2249.

----

## Version 2.6.2 [2025-02-16]

### Release Notes

This is a patch release that fixes a few issues with the project tree: The Empty Trash option in
the menu now works again, and it is no longer possible to accidentally drag and drop project items
onto the root of the project tree.

In addition, a Czech translation has been added by Tomáš Zmek, and the Italian, Polish and
Brazilian Portuguese translations have been updated.

### Detailed Changelog

**Bugfixes**

* Fixed a bug where alternative scene formats were ignored when splitting a document. Issue #2233.
  PR #2234.
* Fixed the Empty Trash menu entry in the Project menu. It was not connected to the project tree
  and therefore selecting it did nothing. Issue #2239. PR #2242.
* Fixed a bug where it was possible to drag items to the root levels as long as they were dropped
  between existing root items. This action is now properly blocked. PR #2242.

**Improvements**

* Added an extra check in the project tree item model that can prevent a crash in certain
  circumstances when moving multiple project items. It is probably a corner case caused by
  competing garbage collectors in Python and Qt, but the additional check should handle. PR #2242.

**Internationalisation**

* Add Czech translation by Tomáš Zmek. PR #2244.
* Updated Italian, Polish and Brazilian Portuguese translations. PR #2244.

See the [translation activity stream](https://crowdin.com/project/novelwriter/activity-stream) for
more details.

----

## Version 2.6.1 [2025-02-02]

### Release Notes

This is a patch release that fixes an issue with creating new notes from the editor context menu,
adds an option to turn off the confirmation box that pops up when closing novelWriter, and improves
the recent project list on the Welcome dialog.

A French version of the user guide is now also available when the localisation is set to French,
and the French, Latin American Spanish, Norwegian, US English, German and Japanese translations of
the application have been updated.

### Detailed Changelog

**Bugfixes**

* Fixed an issue where the "Create Note from Tag" would also show up for `@story` references. These
  should not create new novel documents. The same menu entry was also removed for `@mention`
  references, as it is not known what category the would belong to. Issue #2212. PR #2215.

**Improvements**

* A setting was added to Preferences to disable the dialog box when exiting novelWriter. It is
  available under the "Behaviour" section. Issue #2209. PR#2213.
* Recent projects on the Welcome dialog box are now tracked using their unique ID as well as their
  path. This means that if a project is moved, it should not show up twice in the list, but the
  path should be updated. Issue #2217. PR #2218.

**Documentation**

* A French version of the user guide is nov available from the Help menu if the GUi language is set
  to French. The French translation was contributed by @Karduin. It is currently directly added to
  the source, but from 2.7 it will be generated automatically in the same way the English user
  guide is. Discussion #1834. PR #2220.

**Internationalisation**

* French translations are available up to the 2.6 release. That is, the new exit dialog setting is
  not translated yet. PR #2214.
* Latin American Spanish, Norwegian, US English, German and Japanese translations are fully
  updated. PR #2214.

See the [translation activity stream](https://crowdin.com/project/novelwriter/activity-stream) for
more details.

----

## Version 2.6 [2025-01-26]

### Release Notes

The 2.6 release fixes a few minor issues from the RC 1 pre-release, and updates most translations.

See the website for complete [Release Notes](https://novelwriter.io/releases/release_2_6.html).

### Detailed Changelog

**Bugfixes**

* Fixed a bug in the novel selector dropdown used a few places that would clear the selection if
  the novel list was refreshed. PR #2179.
* Fixed a bug that would crash the app if the project tree was clicked without any project having
  been loaded. The selection model does not exist prior to a project load. Issue #2173. PR #2181.
* Replaced a broken link on the dictionary install tool available on Windows. PR #2189.
* Backported a few code fixes from 2.7 related to freeing memory from closed dialogs and one
  instance of a potentially uninitialised variable. PR #2202.
* Fixed word wrapping in the item details panel for status and importance labels with very long
  names. PR #2202.
* Fixed the project tree context menu so that it is not opened when right-clicking on an empty area
  of the tree widget. PR #2202.

**Improvements**

* Chapter headings are now level 1 headings in all manuscript output formats, not just HTML like
  before. Most applications that post-processes output will assume chapters are level 1.
  Correspondingly, scenes are now level 2 and sections are level 3. Notes headings remain
  unchanged. Issue #2205. PR #2206.

**Internationalisation**

* German, US English, Italian, Japanese, Norwegian and Polish have been updated in full. Brazilian
  Portuguese and Chinese have been partially updated. PR #2207.

**Documentation**

* Documentation has been updated with 2.6 features. PR #2210.

----

## Version 2.6 RC 1 [2025-01-09]

### Release Notes

This is a release candidate of the next release version, and is intended for testing purposes.
Please be careful when using this version on live writing projects, and make sure you take frequent
backups.

### Detailed Changelog

**New Features**

* The session timer in the status bar can now be hidden by clicking on it. Issue #1029. PR #2149.
* Status and importance labels can now be exported and imported. Issue #1847. PRs #2152 and #2153.

**Bugfixes**

* Fix a beta release bug where it was not possible to change the status or importance flag on
  folders in the project tree. Issue #2145. PR #2147.
* Fix an issue where the word counter would override the selection counter in the editor. This was
  caused by the selection counter being on a much shorter timer than the word counter, so in some
  cases the latter result came in after the former even if the user actions where the other way
  around. The selection counter now takes precedence, always. Issue #2155. PRs #2156 and #2157.
* Fix a minor issue where the search panel header background would not update colour when the theme
  was changed. Issue #2162. PR #2167.

**Improvements**

* It is no longer necessary to click the "Apply" button when making changes to status and
  importance labels, or auto-replace settings, in Project Settings. The changes are applied
  directly to the listed items. They are not applied to the project until the Project Settings are
  accepted. This is a more intuitive approach. Issue #2150. PR #2151.

**Packaging and Installation**

* MacOS packages are now built on the latest MacOS image available on GitHub. The x86_64 build was
  previously locked to MacOS 12, which is no loner available. PR #2141.

----

## Version 2.6 Beta 2 [2024-12-23]

### Release Notes

This is a beta release of the next release version, and is intended for testing purposes. Please be
careful when using this version on live writing projects, and make sure you take frequent backups.

### Detailed Changelog

**New Features**

* The project tree has been completely rewritten under the hood. The main difference in the GUI is
  a lifting of restrictions on drag and drop. You can now select multiple items in multiple places
  in the tree, and drag them to a new location. It is still not allowed to drag root level items,
  or drop items on the root level. PR #2119.
* You can now drag and drop items from the project tree onto the editor and viewer to load the
  documents there. PR #2119.

**Bugfixes**

* Make line height in DocX scale correctly. Issue #2099. PR #2102.
* Make margins scale with font size in ODT and HTML output. PR #2102.
* Fix DocX page count to work with Office 365. PR #2102.
* Fix font scaling issues for PDF output. Issue #2100. PR #2104.
* Fix an issue that cleared the editor when the return key was used on a folder item. PR #2113.
* Fix an issue where the viewer and preview would not reset text emphasis when selecting a default
  font style with emphasis features. Issue #2121. PR #2122.
* Change how custom fonts are loaded to ensure that the Qt framework don't take shortcuts by using
  a similar font instead of the chosen font. This is a side effect of the Qt font matching feature.
  Issue #2118. PR #2122.

**Improvements**

* Move processing of alternative apostrophe and dash to a later point in the tokenization process.
  It needs to happen after dialogue is processed to work as intended. PR #2095.
* Use icons for text margin settings in Build Settings. Issue #2098. PR #2102.
* Replace the toolbar icon in the editor. PR #2103.
* Turn off auto-default button on the Build dialog. Issue #2101. PR #2105.
* Add ANSI colours to log output for easier debugging. PRs #2114 and #2117.
* Document header is now aligned to the bottom of the top page margin in the same way for ODT and
  DocX output. Issue #2120. PR #2128.
* Dialogue detection for quoted dialogue has been improved to better support Chinese, and other
  languages that don't use whitespaces to separate words. Some improvements have also been made to
  how single quoted dialogues are processed when apostrophes are present. Issue #2131. PR #2138.

**Code Improvements**

* Completely rewrite the project tree into a model/view set with one single definition if the
  project structure. PR #2109.
* The auto-replace feature in the editor has been refactored. It is now better separated from the
  editor code, and may have some minor performance improvements. Issue #2129. PR #2132.

----

## Version 2.6 Beta 1 [2024-11-12]

### Release Notes

This is a beta release of the next release version, and is intended for testing purposes. Please be
careful when using this version on live writing projects, and make sure you take frequent backups.

### Detailed Changelog

**New Features**

* Added PDF build format. Issue #2046. PR #2048.
* Added DocX (MS Word) format. Issue #1537. PR #2056.
* The Build settings tool has the following changes: Ability to control page break and centring of
  main titles, an option to disable styling for headings altogether, and the ODT section has been
  generalised to apply to all document formats. Issue #2023. PR #2045.
* Text and heading margin can now be control in the Manuscript Build tool. Issue #2023. PR #2051.
* Word counts and other such statistics can now be inserted into the manuscript. This is done
  through new insert actions in the Insert menu, and processed at build time. Issue #2024.
  PR #2073.
* Forced line breaks can now be inserted as a shortcode. This is useful when line breaks in
  paragraphs are ignored when building the manuscript. Issue #1991. PR #2063.
* A new `@mentions` keyword has been added that can list any tag in the project as being mentioned
  in the current section. These are listed separately from tags present in the story section.
  Issue #1822. PR #2064.
* Tags in novel documents can now be referenced with the `@story` keyword. Issue #1990. PR #2072.
* URLs starting with http/https are now recognised and clickable in the editor, viewer, and
  manuscript preview. Issue #1426. PR #2067.
* Added dialogue highlighting for Portuguese and Polish dialogue styles. Issues #2066 and #2070.
  Related to #1773. PRs #2068, #2079, #2081 and #2082.
* Four dashes in the editor are now replaced by a horizontal bar. This is useful as a replacement
  symbol for em dash when using dialogue highlighting to avoid triggering it. The horizontal bar is
  replaced with an em dash in the manuscript. Issue #2070. PR #2079.
* Manuscript Build settings can now be duplicated. Issue #1931. PR #2084.
* Page breaks can optionally be made visible in the Manuscript preview. PR #2086.
* The document status label can now be selected in the Outline View. Issue #1909. PR #2088.
* The document viewer now has an edit button to open the document in the editor. Issue #1963.
  PR #2089.

**User Interface**

* The Manuscript Build settings have now been moved into a single scrollable page, using the same
  layout as in Preferences. The heading and filtering pages are still separate forms, as they are
  of a more complex nature. PR #2031.
* The currently open document in the editor is now highlighted in the project tree, just like it is
  in the novel view. Issue #1981. PR #2077.
* The details panel in the Outline view is now resizable. PR #2078.

**Improvements**

* Add an option to ignore a word in the spell checker. An ignored word is ignored only for the
  current writing session. PR #2030.
* Word counts and other such statistics is now exported as custom variables to ODT files, and can
  be inserted in the text in LibreOffice, and similar. Issue #2033. PR #2035.

**Code Improvements**

* Added Python 3.13 coverage to ensure the new Python release is supported. Issue #2040. PR #2044.
* Preparation for Qt6: Clean up Qt enums. PR #2025.
* Preparation for Qt6: Replace Qt regular expression tools with the internal Python re module for
  markup processing and syntax highlighting. It is both slightly faster, and there are issues with
  text encoding in at least some versions of Qt6 or PyQt6. PRs #2028 and #2043.
* Preparation for Qt6: Added a wrapper function for connecting signals to slots that has a
  different function signature. Python lambdas generate warnings in Qt6. PR #2075.
* Refactored manuscript formats and moved most of the processing to the Tokenizer class to simplify
  the format classes and also make them more consistent. PRs #2060, #2061 and #2062.
* The document builder has been refactored to support more generalised format classes. PR #2047.
* Action parent assignment has been rafactored in the main menu. #2075.
* Raw text format output has been refactored and reduced to just appending documents. PR #2087.

----

## Version 2.5.3 [2024-11-26]

### Release Notes

This is a patch release that fixes a few minor bugs in the user interface, and with the HTML
manuscript format. This patch also adds a Russian translation, and updated the German and
Portuguese translations.

### Detailed Changelog

**Bugfixes**

* Fixed the red/green LEDs on the statusbar for the Default Light theme. The colours were swapped.
  Issue #2057. PR #2059.
* Moved the styles tag into the head tag for HTML manuscript output, which is the correct placement
  for them. Issue #2080. PR #2085.
* Fixed a bug in the project tree where it was possible to drag content to root level on some Qt
  versions where the disallow flag is not obeyed. The illegal action is now additionally blocked by
  code. Issue #2108. PR #2109.

**Documentation**

* Updated a dead link to the spell check library with the new one. Issue #2042. PR #2059.

**Internationalisation**

* Russian translation added by Konstantin Tan (@k1kimosha). PR #2126
* Updated German and Portuguese translations. PR #2126

----

## Version 2.5.2 [2024-09-17]

### Release Notes

This is a patch release that fixes a series of issues mostly affecting dialogue highlighting in the
document viewer. The way the text is formatted in the viewer changed a lot in 2.5, and there were a
few issues with the new implementation. The tab stop distance setting was also ignored, but has now
been fixed as well.

### Detailed Changelog

**Bugfixes**

* Fixed an issue where the tab stop distance setting was being ignored in the document viewer. It
  must be set again every time a document is loaded. Issue #1996. PR #2014.
* Fixed an issue with overlapping formatting markers when processing text into new formats. This
  issues was introduced when dialogue highlighting was added to the document viewer and manuscript
  build. It arises because start and end of dialogue can occur on the same character as other
  formatting, and then the order these markers are processed matters. This was not properly handled
  in the code. Issue #2012. PR #2014.
* Dialogue highlighting is now only applied to plain text paragraphs, not comments, headings, and
  other places where there should be no dialogue. Issue #2013. PR #2014.
* Note documents no longer get dialogue highlighting. Issue #2011. PR #2014.

**Documentation**

* Added a section about spell checking in the documentation. PR #2015.

----

## Version 2.5.1 [2024-07-28]

### Release Notes

This is a patch release that fixes an issue with the lock file being left in the project when the
project open is cancelled, a few issues with custom input boxes in Preferences, and a usability
issue when selecting to edit a tag or reference from the Tags and References panel as well as fixed
an issue with the Importance labels not being updated in the tabs for tags.

### Detailed Changelog

**Bugfixes**

* Fixes an issue where the project lock file was created before certain checks where the user could
  cancel the project open process, leaving a lock file in the project folder behind. Issue #1977.
  PR #1978.
* Fixes an issue where the user could add spaces to the pad before and after Preference settings,
  which would pad every space entered into the text. The Preferences settings no longer accept any
  white spaces in these boxes (they are removed on save) and also strips duplicate character
  entries. Issue #1985. PR #1986.
* The narrator break and dialog symbol Preference text boxes will now be cleared if the settings is
  a white space. PR #1986.
* Fixed an issue where Importance labels were not updated in the viewer panel's tags tabs when they
  where changed in Project Settings. Issue #1992. PR #1993.

**Usability**

* When selecting to edit a tag or reference from the panel below the Document Viewer, the editor
  now scrolls to the relevant heading as it does in the viewer. Issue #1983. PR #1987.

**Internationalisation**

* Latin American Spanish translation updated by Tommy Marplatt (@tmarplatt). PR #1989.

----

## Version 2.5 [2024-07-10]

### Release Notes

The 2.5 release fixes a number of minor issues from the RC 1 pre-release, and updates most
translation files. Polish has also been added.

See the website for complete [Release Notes](https://novelwriter.io/releases/release_2_5.html).

### Detailed Changelog

**Bugfixes**

* Fix an issue with unresponsiveness when switching from Outline View to Tree View with a keyboard
  shortcut. Issue #1949. PR #1954.
* Fix an issue with switching focus between editor and viewer when the viewer is hidden.
  Issue #1950. PR #1954.
* Fix an issue with first line indentation where it would sometimes indent first paragraph when it
  should not. Issue #1965. PR #1971.

**Usability**

* Remove the "Apply" button from Preferences as changing theme does not updated the Preferences
  dialog, which is unexpected behaviour. The Preferences dialog is now also consistent with other
  settings dialogs. Issue #1951. PR #1954.
* Improved the error messages when opening a project fails. Issue #1944. PR #1956.
* Make sure the Project Name is selected and in focus when switching to the New Project Form on the
  Welcome dialog. Issue #1967. PR #1968.

**Improvements**

* Add first line indentation to Manuscript previews. Issue #1961. PR #1962.

**Internationalisation**

* Norwegian and US English translations updated by @vkbo. PR #1955.
* German translation updated by Myian (@HeyMyian). PR #1955.
* Italian translation updated by Lou Cyper (loucyper1). PR #1955.
* Dutch translation updated by Martijn van der Kleijn (mvdkleijn). PR #1955.
* Chinese translation updated by @longqzh. PR #1955.
* Portuguese translation updated by Oli Maia. PR #1955.
* Japanese translation updated by @hebekeg. PR #1955.
* French translation updated by Albert Aribaud (@aaribaud). PR #1955.
* Polish translation added by Anna Maria Polak (@Nauthizz). PR #1955.

**Packaging**

* Rewrote the packaging utilities script. Windows builds are now created in GitHub actions, which
  is needed for signed packages when this is enabled. PRs #1958 and #1959.

**Documentation**

* Updated the documentation for 2.5. PR #1928.

----

## Version 2.5 RC 1 [2024-06-22]

### Release Notes

This is a release candidate of the next release version, and is intended for testing purposes.
Please be careful when using this version on live writing projects, and make sure you take frequent
backups.

### Detailed Changelog

**Bugfixes**

* The Status bar LEDs are now properly updated when the theme changes. Issue #1893. PR #1906.
* All HTML tags are now properly closed at the end of each paragraph in HTML output. After
  shortcodes were introduced, it was possible to leave formatting tags open. Issue #1919. PR #1926.

**Improvements**

* Move the first line indent setting from being an Open Document feature to a general build
  settings feature that also applies to HTML, and make it visible in the Manuscript build tool
  preview. Issue #1839 and #1858. PR #1898.
* Make sure the document in the editor is saved before the same document is opened in the viewer.
  Issue #1884. PR #1902.
* The project name now appears before "novelWriter" in the main window title, which improves the
  task bar label on at least Linux Mint Cinnamon, and Windows. Issue #1910. PR #1911.
* Dialogue highlighting now only applies to novel documents, not notes. It is also possible to
  apply it to HTML and ODT manuscripts, and it also shows up in the preview and in the document
  viewer. Issue #1774. PR #1908.
* The Welcome dialog and other tools that use the project name to generate files of folder names
  are now less restrictive on what characters it allows in the file or folder names. Issue #1917.
  PR #1922.
* Last used folder paths are now remembered individually for each tool or feature that requires
  path input from the user. Issues #1930 and #1933. PR #1934.
* The Manuscript preview will now show line height as set in build settings. Issue #1920. PR #1935.
* Global search now refreshes if any of the search option buttons are toggled, and the search
  result will show the complete word if the search term only matches part of a word. Issue #1830.
  PR #1936.
* When a new note is created from a reference tag in the editor, the syntax highlighting is
  properly updated to indicate the tag is now valid. Issue #1916. PR #1938.
* The `Ctrl+E` shortcut now toggles focus between editor and viewer instead of just going to the
  editor. The header text colour changes to indicate which panel has focus. This should make it
  easier to scroll the content of the viewer without having to click it with the mouse first.
  Issue #1387. PRs #1940 and #1941.

**Code Improvements**

* Change how dialogs are handled in memory, and drop the calls to deleteLater for the underlying Qt
  object as it caused problems in some cases. Instead, the dialog is disconnected from the parent
  object, which seems to let the Python and Qt garbage collectors to kick in.
  PRs #1899. #1913 and #1921.
* Overload the reject call for dialogs rather to call close, which the default implementation does
  not. This simplifies the logic when closing dialogs, as reject() is also a slot, which close() is
  not. Issue #1915. PR #1918.
* Processing of dialogue highlighting has been added to the Tokenizer class, and the RegEx handling
  moved to a separate factory class. PR #1908.
* The progress bar widgets have been moved to a single module, and test coverage added. PR #1937.

**Packaging**

* The Windows installer is now built with Inno Setup 6.3, and uses zip compression rather than
  lzma. It also properly sets the undelete icon, and the undelete process is better at cleaning up
  files. PR #1932.

----

## Version 2.5 Beta 1 [2024-05-26]

### Release Notes

This is a beta release of the next release version, and is intended for testing purposes. Please be
careful when using this version on live writing projects, and make sure you take frequent backups.

### Detailed Changelog

**General Changes**

* novelWriter now requires Python 3.9 and Qt 5.15 as a minimum. That means Ubuntu 20.04 and older
  are no longer supported for the Debian packages. Users on Ubuntu 20.04 and equivalent Linux
  distros must use the AppImage. PRs #1826 and #1833.

**Major Features**

* Status and Importance icons can now be assigned a shape in addition to a colour. Issue #1786.
  PRs #1810 and #1819.
* Footnotes have been added. They use a modified comment format for specifying the footnote text,
  and a shortcode for inserting the footnote into the text. They are linked via a key. If the
  footnote is inserted via the **Insert** menu, a unique key is generated. Issue #342. PR #1832.
* Comments in general now support formatting, so format tags work just like in regular text. This
  was needed for footnotes, but has been expanded to include all comments. PR #1832.
* Two new themes have been added. Dracula is available as a set for both the GUI and the editor.
  Snazzy Light is available for syntax only, but works well with the default light GUI theme.
  PR #1840.
* Character dialogue highlighting has been completely redesigned. The highlighting rule now
  specifically relates to dialogue, and not just quoted text in general. To that effect, more rules
  for detecting what is and isn't dialogue has been added. This is designed to support difference
  between dialogue conventions in different languages. Issues #1770 and #1771. PR #1864.
* The font settings in Preferences now considers the full range of font options, in particular font
  style and weight. The changes include the font size in these settings, so the additional setting
  for font size has been removed. Use the font dialog to pick size as well. Due to this removal,
  the font size has been reset to default and must be set again by the user. Issue #1733. PR #1881.
* The document viewer and the manuscript preview now uses a completely new class to generate the
  formatted text. The old method used an outdated HTML format as the go-between, which restricted
  what formatting could be applied. The main noticeable change to users at the moment should be the
  size of headings, that now match the size in the editor. Issue #1882. PR #1892.

**Improvements**

* The default dark theme has been redesigned to match the GUI theme a little better, and is now
  also consistent with the default light themes. PRs #1836 and #1840.
* Special comments now have a different text colour than plain comments. PR #1836.
* The various Tomorrow themes are now a little more consistent in what colours are used for which
  components. More variation has also been added. PR #1840.
* The Tango theme has been updated. PR #1840.
* The last cursor position is now always saved when a document is closed in the editor, even if the
  content has not been changed. PR #1849.
* The settings for first line indent have now been extended to allow setting how deep the indents
  are and whether or not to indent the first paragraph after a heading or break. The settings have
  also moved from being Open Document specific to the general formatting tab for manuscripts.
  PR #1857.
* Preserving in-paragraph line breaks is now a general Manuscript setting that applies to all
  output formats. PR #1891.
* The Manuscript builds now also uses the full font settings of the selected output font, not just
  the font family and size option. Since the size option has been merged into the general font
  choice, the separate font size setting has been dropped and users must set it again. PR #1891.
* It is now possible to disable the usage of the font selection dialog from your operating system.
  At least on Linux Gnome desktops, the system's font dialog lacks a lot of the selection options
  available in the font dialog provided with Qt. PR #1891.

**Bugfixes**

* Fixed an issue where Manuscript dialogs would be left open if the project was closed. PR #1844.
* First line indents are no longer reset after a comment. Issue #1852. PR #1857.

**Packaging**

* Minimal zip file release packages can no longer be built from the package utility script. The zip
  file needed for building the Windows installer is still available. PR #1826.
* Added build packages for AARCH64 on MacOS. It seems some dependencies still prevents it from
  being installed cleanly without requiring some virtualisation feature, but it works. PR #1829.
* AppImages are now released with Python 3.12. PR #1829.

**Other Changes**

* A new GUI theme setting for error text has been added. It is used when error messages need to be
  displayed on the GUI. PR #1880.

**Code Improvements**

* The behaviour of dialogs across various platforms has been unified and improved a little to
  ensure more consistent behaviour. It is mostly related to modality and z-order. There are still
  limitations due to platform restrictions, like non-modal dialogs being stuck on top on Linux
  Wayland. PR #1844.
* Some GUI components have been improved and refactored to rely more on signals and slots rather
  than reaching into each other's classes and calling methods. This is a little more robust.
  PR #1849.
* The text tokenizer used to parse the formatting codes in novelWriter has been refactored and
  improved. In particular, multi-line paragraphs are now processed during the second pass of
  tokenization rather than when the final format is applied. This allows a much more compact format
  of the token data, and avoid potential inconsistencies between the various output formats.
  PR #1885.

----

## Version 2.4.4 [2024-06-12]

### Release Notes

This is a patch release that fixes a usage issue when setting document label from an unsaved
document, fixes a rare chance of a crash when closing the Manuscript tool, and updates the
Portuguese translation.

### Detailed Changelog

**Bugfixes**

* Backported some memory improvements from the upcoming 2.5 release. This also fixes a potential,
  but low probability crash in the Manuscript tool. If the tool is closed during the milliseconds
  long window when the clock on the yellow label is updated, the app can crash with a segmentation
  fault. PRs #1903 and #1905.
* Fixed an issue where changing a document's label to match the document heading would suggest the
  wrong title if the document was open in the editor, but in an unsaved state. An easy condition to
  encounter when creating a new document and setting the heading first. Issue #1914. PR #1923.

**Internationalisation**

* Portuguese translation updated by Oli Maia. PR #1904.

----

## Version 2.4.3 [2024-05-20]

### Release Notes

This is a patch release that fixes issues with the document font in the editor, viewer and
manuscript preview on some Linux distros, and also fixes a potential crash on Windows when using
the spell check dictionary install tool.

### Detailed Changelog

**Bugfixes**

* Fixed a crash in the dictionaries install tool on Windows if the config folder reported by the
  third party Enchant spell checker tool didn't already exist prior to adding new dictionaries.
  The folder is now created when the tool is opened if it doesn't exist. Issue #1874. PR #1876.
* Fixed issues when setting a different text font for the editor and viewer, and related issues
  with the preview in the Manuscript Build tool, on certain platforms. Changing the font and
  setting non-standard font sizes produced unexpected results when reloading. The issue seems to be
  related to Qt 5.15.3, but that is not fully confirmed. However, the only place so far where the
  issue is observed is on Mint 21.3. Issues #1862 and #1875. PR #1877.

----

## Version 2.4.2 [2024-05-18]

### Release Notes

This is a patch release that fixes two minor font issues and updates the Dutch and Chinese
translations.

### Detailed Changelog

**Bugfixes**

* Change the preview widget in the Manuscript Build tool to use the document font only for the
  document itself, not the yellow heading stating the age of the previewed text. PR #1863.
* Fixes the syntax highlighter so that it is re-initialised when the document editor is
  re-initialised, so that changes to document font size regenerates the heading font sizes as well.
  Issue #1865. PR #1866.

**Internationalisation**

* Dutch translation updated by Martijn van der Kleijn (@mvdkleijn). PR #1872.
* Chinese translation updated by @longqzh. PR #1872.

----

## Version 2.4.1 [2024-05-06]

### Release Notes

This is a patch release that fixes a number of minor issues with the Manuscript Build tool. The
only critical fix is related to a potential crash when deleting a build entry when its settings
dialog is still open.

### Detailed Changelog

**Bugfixes**

* Fixed an issue that could crash novelWriter if a build settings entry was deleted from the
  Manuscript tool while its settings window was open. PR #1845.

**Improvements**

* Changed the font used for the document editor and viewer header and footer from the one used for
  the document text to the one used for the user interface. Issue #1842. PR #1843.
* Added a save document step in the editor before running a manuscript build or a preview job. This
  ensures that the text in the editor is included in the manuscript. Issue #1835. PR #1846.
* Restore preview panel scroll bar position after updating the preview on the Manuscript tool.
  Issue #1837. PR #1846.
* Close all non-modal dialogs when a project is closed. PR #1848.

**Code Improvements**

* Fixed an issue with the Build Settings dialog that blocks the garbage collector from deleting the
  dialog after it's been closed. PR #1843.
* Remove some deprecated translation entries from the translation files. PR #1850.

----

## Version 2.4 [2024-04-20]

### Release Notes

This release adds a new global search feature. The tool is still relatively basic, and will likely
be extended in later releases.

Among new text editing features is the ability to highlight text using `[m]text[/m]` shortcodes.
The code `[m]` is for "mark", which is the equivalent code in HTML.

A second feature added for text editing is the ability to add an alternatively formatted scene
heading by adding a `!` to the markup, like for chapters and main titles. This allows to
distinguish between two scene formatting styles, `### Title` and `###! Title`, which can for
instance be used for soft and hard scene breaks.

The **Manuscript Build** tool has also been extended with multiple new formatting options.

See the website for complete [Release Notes](https://novelwriter.io/releases/release_2_4.html).

### Detailed Changelog

**Bugfixes**

* Fixed background colour on some widgets on the new Project Search tool. PR #1800.
* Fixed a bug when using bold/italic/strike through toggle on an existing text selection in the
  editor. Issue #1807. PR #1808.
* An index out of bounds error in the word counter has been fixed. It could only be triggered by a
  single line only containing a ">" character. Issues #1816 and #1825. PR #1817.
* Fixed an issue where not all theme colours were completely reset before changing theme. PR #1820.
* Shortcodes are no longer passed to the spell checker. PR #1823.

**Improvements**

* Made placeholder text for search read as "Search for" and "Replace with". PR #1799.
* The initial count for adding chapter and scenes to new project in the Welcome dialog has been
  changed to 0. The user must now select to add chapters and scenes. Issue #1811. PR #1815.

**Documentation**

* Updated the documentation for 2.4 features. PR #1818.

**Internationalisation**

* Norwegian and US English translations updated by Veronica Berglyd Olsen (@vkbo).
  PRs #1799 and #1814.
* Latin American Spanish translation updated by Tommy Marplatt (@tmarplatt). PR #1814.
* Italian translation updated by Lou Cyper (loucyper1). PR #1814.
* Japanese translation updated by @hebekeg. PR #1814.
* French translation updated by Albert Aribaud (@aaribaud). PR #1821.
* German translation updated by Myian (@HeyMyian). PR #1821.

----

## Version 2.4 RC 1 [2024-04-06]

### Release Notes

This is a release candidate of the next release version, and is intended for testing purposes.
Please be careful when using this version on writing projects, and make frequent backups.

### Detailed Changelog

**Bugfixes**

* A number of issues GUI icon scaling has been fixed. Icons and buttons are supposed to scale
  relative to the GUI font size, but several of them were not. Issue #1787. PR #1788.
* The persistence of button state for the editor search box has been improved. The present state
  was only saved when the search box was actively closed, and there were several scenarios where
  this didn't happen. The button states are now tracked in the central config, and will always be
  preserved. Issue #1794. PR #1795.

**Other Improvements**

* A placeholder icon has been added for cases where users have their own icon theme, and icons are
  missing. Issue #1780. PR #1781.
* The project search now refreshes the search results for the currently open document when it's
  being edited. PR #1782.
* When activating project search from the editor while text is selected, the search box is
  populated with this text. Issue #1789. PR #1790.

**Packaging**

* The project has moved from using a `setup.cfg` to only using the `pyproject.toml` meta data file
  for packaging. This is the preferred file format now. PR #1791.

**Code Improvements**

* The part of the code related to Qt widgets and flags has been updated and refactored in
  preparation for the eventual move to the Qt6 framework. Part of issue #1142. PR #1792.
* The Open Document writer class has been refactored and improved. PR #1796.

----

## Version 2.4 Beta 1 [2024-03-26]

### Release Notes

This is a beta release of the next release version, and is intended for testing purposes. Please be
careful when using this version on live writing projects, and make sure you take frequent backups.

### Detailed Changelog

**Major Features**

* A global search feature has been added to the main sidebar. The search panel replaces the project
  and novel tree when activated. PR #1775. Issue #894.
* A new shortcode to highlight text has been added. PR #1715. Issue #705.
* A new heading format for hard scene breaks has been added. It uses `###!` heading markup. The
  only affect this has in the GUI is that these headings can be independently formatted in the
  Manuscript tool. PR #1753. Issue #1050.
* The document editor and viewer now have a dropdown menu in the header listing all headings of the
  current document for quick navigation. The list is capped at 30 entries. PR #1764. issue #1059.

**Build Tool Improvements**

* The Manuscript Build Tool now has a word stats section below the preview that shows a number of
  word and character counts for the previewed text. PR #1717. Issues #1114 and #1116.
* The Manuscript Build Tool now shows an outline of the previewed document as a tab next to the
  build settings list. PR #1768. Issue #1765.
* Tabs handling in HTML output now has a separate setting from the other format. PR #1723.
* Hard line breaks can now be excluded from Markdown builds. PR #1723. Issue #944.
* It is now possible to control the centring and page breaks of partition, chapter and scene
  headings. PR #1723. Issues #1117 and #1661.
* Special titles (`#!`) can now be used in notes as well. PR #1723.
* Meta data categories can be filtered out from the manuscript. PR #1723. issue #1132.
* Any heading in a novel document can now be hidden in the manuscript. PR #1759. Issue #1756.
* First line of a paragraph can now be indented in the manuscript. PR #1761. Issue #906.
* Each meta data entry in HTML builds have a new class assigned to it that matches the tag used in
  the text. PR #1767. Issue #1134.

**Other Improvements**

* The percentage progress counter in the editor document footer now counts progress per character
  instead of per line. This is only noticeable on short documents. PR #1725.
* Some improvements have been made to terms on the GUI and some strings have been simplified in
  order to be easier to understand and to translate. PR #1727. Issue #1726.
* Dates are now formatted according to the selected locale, if such a locale is available. If not,
  it falls back to the local system locale. PR #1755. Issue #1739.

**Code Improvements**

* The tokenization of the novelWriter markup format has been refactored and improved. PR #1724.
* A way to read project documents fast has been added. It is useful many places in the code where
  only the text is needed, not the meta data. PR #1777.

----

## Version 2.3.1 [2024-03-17]

### Release Notes

This is a patch release that fixes several issues with translations into other languages than the
default English, and adds completed translations for French.

### Detailed Changelog

**Internationalisation**

* Fix untranslated text on the "Project Word List" dialog. PR #1744. Issue #1746.
* Fix untranslated text on the dialog that pops up after an upgrade, PR #1754. Issue #1749.
* Fix error in Norwegian translation. PR #1744.
* Allow the translated text for adding chapter and scenes on the Welcome dialog to flow around the
  number selector since the number is inserted into the sentence, and not all languages will split
  the sentence around the number like is done in English. PR #1754. Issue #1750.
* French translation updated by Albert Aribaud (@aaribaud). PR #1760.
* Minor updates to other translations for the 2.3.1 fixes by other contributors. PR #1760.

**Other Changes**

* Bump the revision of the project file format to 1.5 Revision 3 from Revision 2. This should have
  been done in the 2.3 release due to the addition of the Templates root folder type. PR #1748.

----

## Version 2.3 [2024-03-10]

### Release Notes

This release introduces a new Welcome dialog that replaces both the previous Open Project dialog
and the New Project Wizard. The Welcome dialog has received a friendly custom art design created by
Louis Durrant.

The Preferences, Project Settings, Project Details, and About dialogs have received completely new
designs and layouts, and the Manuscript Build Settings dialog has been updated to match.

Among new features is a new Templates root folder where the writer can store template documents to
be used when creating new project documents and notes. It is now also possible to include Point of
View and Focus character names in chapter titles in Manuscripts. A new feature to ignore text has
also been added. It behaves similarly to comments, but is never included in a manuscript even if
comments in the manuscript are enabled.

See the website for complete [Release Notes](https://novelwriter.io/releases/release_2_3.html).

### Detailed Changelog

**Bugfixes**

* Fix an issue where the Tags and References panel below the document viewer was not cleared if a
  project was opened, closed, and a new project with no tags defined were opened again. PR #1720.
  Issue #1718.
* Fixed an issue where multi-selecting documents in Trash would give the option to again move items
  to Trash. The menu now properly offers the option to permanently delete the documents. PR #1728.
* Fixed an issue where multi-select for deletion would only process the item right-clicked, and not
  all the selected items. PR #1728.
* Changed the error message that pops up when trying to open a project from the Welcome dialog that
  no longer exists. The error message should no indicate that the project was not found, as opposed
  to unreadable. PR #1740. Issue #1737.

**Improvements**

* The build tool no longer inserts a scene separator immediately after a partition heading, and
  should now behave the same way as for chapters. If there is text before the first scene break,
  the text flows continuously without a separator. PR #1716. Issue #1704.
* Added one new GUI theme named "Cyberpunk Night" by @alemvigh. Also added a matching "Cyberpunk
  Night" document editor theme by @alemvigh, and a new Tango theme by @vkbo. PR #1738. Issue #1730.
* When the Welcome dialog fails to open a project, and there is not already a project open in the
  app, the Welcome dialog appears again. PR #1740. Issue #1737.

**Internationalisation**

* Norwegian and US English translations updated by @vkbo. PR #1714.
* Japanese translation updated by @hebekeg. PR #1714.
* Italian translation updated by Lou Cyper (loucyper1). PR #1714.
* Dutch translation updated by Annelotte and Martijn van der Kleijn (mvdkleijn). PR #1714.
* Latin American Spanish translation updated by @tmarplatt. PR #1741.
* German translation updated by Myian (@HeyMyian). PR #1741.

**Other Changes**

* Removed the novelwriter-cli entry point that was in any case broken. PR #1734. Issue #1732.

----

## Version 2.3 RC 1 [2024-02-24]

### Release Notes

This is a release candidate of the next release version, and is intended for testing purposes.
Please be careful when using this version on live writing projects, and make sure you take frequent
backups.

Please check the changelog for an overview of changes. The full release notes will be added to the
final release.

### Detailed Changelog

**Improvements**

* Redesign the buttons on the new Welcome dialog so that they only show buttons related to the
  visible page. Drop the additional buttons on the New Project page. Issue #1706.
  PRs #1707 and #1709.
* Drop the Language setting on the Welcome dialog's New Project page. PR #1707.
* Hide the additional settings for Fresh Projects on the New Project page of the new Welcome
  dialog. Issue #1705. PR #1707.
* Update the Templates root folder icon. PR #1709.
* Scene separators are now hidden after a new title in manuscript builds, also when there are no
  chapters. Issue #1704. PR #1711.
* Scene and chapter counters are now reset when a novel title is encountered. PR #1711.

----

## Version 2.3 Beta 1 [2024-02-16]

### Release Notes

This is a beta release of the next release version, and is intended for testing purposes. Please be
careful when using this version on live writing projects, and make sure you take frequent backups.

Please check the changelog for an overview of changes. The full release notes will be added to the
final release.

### Detailed Changelog

**Major Features**

* A new Welcome dialog has been added. The dialog replaces the Open Project dialog and the New
  Project Wizard. The Welcome dialog features artwork created by Louis Durrant, and a custom design
  for the project list. New projects can be created by a form available from the same dialog, and
  features a simplified set of options. Issue #1506. PRs #1647, #1681 and #1689.
* It is now possible to create a new project by copying the content of another project, or a Zip
  file of a project, including a backup. This option is available from the New Project feature of
  the Welcome dialog. Issue #841. PRs #1680 and #1684.
* The Preferences dialog has been completely redesigned. All options are now available in a single,
  scrollable list with appropriate section headers. All sections are available as navigation
  buttons along the side, and it is also possible to search for settings in a search box at the
  top. The design matches that created for the Manuscript Build Settings dialog added in 2.1.
  Issues #1603 and #1604. PR #1652.
* The Project Details dialog has been redesigned to match the other new dialogs. It has also been
  modified to properly handle multiple novel folders. The novel selector is placed at the top of
  the dialog, and affects all data in the tabs. The Novel Title info has been removed. PR #1665.
* The Manuscript Build Settings dialog has been updated to use the new config layout classes, which
  are more flexible in terms of content flow. PR #1674.
* A new root folder type called "Templates" has been added. Any document added here will show up in
  the Add Item menu in the Project Tree view under a "From Template" submenu. Selecting such an
  entry will create a new document at the selected location in the project, and populate it with
  the content of the template file. Issues #996 and #1125. PR #1688.
* The About novelWriter dialog has been simplified to only show some key information and the
  credits text. A link to the releases page is available for checking release notes. Keeping the
  release notes online means it is easier to update them, and make them more visually interesting
  as the formatting of the dialog box is limited. PR #1695.
* The old Check for Updates dialog has been removed. Checking for new releases of novelWriter can
  be done directly in the Welcome dialog or the About dialog by clicking "Check Now" next to the
  "Latest Version" label. PR #1696.

**Minor Features**

* A new drop down menu in the References panel below the Document Viewer has an option to filter
  out inactive notes in the various tag lists in the tabs on the panel. Issue #1653. PR #1654.
* The Novel Title fields, which no longer makes much sense after it was possible to add multiple
  novel folders to a project, has been fully dropped. Issue #1655. PR #1669.
* The document header for ODT manuscript files can now be customised. Issue #1505. PR #1675.
* The Manuscript Build tool can now insert characters (Point of View or Focus) into chapter headers
  and other headers. By default, it inserts the tag value, but the display name for a tag can be
  set with a `|` character in the `@tag` definition if a different text is desired. Issue #1468.
  PR #1677.
* A new modified comment format for the editor has been added. Instead of the regular comment using
  `%`, this one uses `%~`. The only difference is that the latter will never be exported to a
  manuscript at all, while regular comments can be exported when a setting is enabled. Issue #1075.
  PR #1690.
* It is now possible to change a document's label from the first heading in the document by
  right-clicking on it and selecting "Rename to heading". Issue #1443. PR #1692.
* The content of the Project Word List can now be exported and imported using plain text files.
  Issue #1560. PR #1691.
* The content of the Outline View can now be exported to a CSV file to be opened in any spreadsheet
  application. Issue #1507. PR #1697.

**Usability**

* A Create New submenu in the Project Tree context menu has been added, which give quick access to
  the items at the top level of the Add Item menu. Issue #1519. PR #1679.
* When multiple paragraphs are selected in the editor, and any of the comment features are toggled,
  or formatting is reset, the action is applied to all selected paragraphs, not just the first.
  Issue #1042 and #1687. PR #1690.

**Packaging**

* The in-app version format is now identical to the version tag, and the format for Ubuntu
  pre-release packages has been updated so that they are compatible with release packages. That is,
  if you add both the release and pre-release repos from Launchpad, release packages will now
  properly replace pre-release packages when running apt upgrade. PR #1659.

**Code Improvements**

* The Storage class has been refactored. It is the class that handles the project storage folder
  for a novelWriter project. The refactoring is a step towards allowing single file storage for
  projects as an alternative to project folders. Issue #977. PR #1635.
* All theme colours are now proper QColor objects from the start, which avoids the need to create
  a large number of these where they are used. PR #1656.
* A nwProject.bak file is no longer kept in the project folder. It never really served any purpose.
  The project file is still written to a temp file before the old file is replaced, which prevents
  partial overwrites. PR #1670.
* Other minor code improvements in PRs #1693 and 1694.

----

## Version 2.2.1 [2024-01-27]

### Release Notes

This is a patch release that fixes an issue where the Project View would sometimes switch to the
Novel View when a new item was created. This patch also includes updated translations for German
and Chinese.

### Detailed Changelog

**Bugfixes**

* Fix a bug in the toggle for the tree view on the left would trigger each time a new project item
  was created. Issue #1649. PR #1648.
* Fix an issue where multiple Manuscript and Writing Stats dialogs could be opened. PR #1671.

**Internationalisation**

* Updated German translation, by @HeyMyian. PR #1666.
* Updated Chinese translation, by @ruixuan658 and @longqzh. PR #1666.

----

## Version 2.2 [2023-12-17]

### Release Notes

This release comes with a number of new features. These are some highlights.

In addition to the common Markdown style formatting for bold, italic and strike through, a set of
new shortcodes have been added. The shortcodes are far more flexible than the Markdown style
syntax, and can be used for more complex formatting cases. Like when you need to add multiple,
overlapping formats, or add emphasis to just a part of a word. The shortcodes also allow for
underline, subscript and superscript, which the Markdown syntax does not. The new formats are
available in the "Format" menu, and in a new toolbar in the editor that can be enabled by clicking
the three dots in the top--left corner. The shortcode format was chosen because it can later be
extended to include other requested features as well. Please have a look at the documentation for
more details about the new shortcodes.

The Tags and References system has been improved. The tags themselves are no longer case sensitive
when you use them in references, but they are still displayed as you typed them in the tag
definition when they are displayed in the user interface. Starting to type the `@` symbol in the
text editor, on a new line, will now open an auto-completer menu which will display available
options. It may not display all of your tags if you have a lot of them, but starting to type more
characters will filter the list down further.

You can now automatically create a note file for a new tag that you have added to a reference list
in a document, but is not yet defined in a project note. So, for instance, if you come up with a
new character while writing, and add a new tag to your `@char` references, you can right-click the
new tag and create a new note for that entry directly. In addition, it is now also possible to
right-click a heading in an open document and set the item label in the project tree to match the
heading.

In addition to the changes in the editor, the "References" panel below the document viewer has also
been completely redesigned. It now shows all the references to the document you are viewing as a
list, with a lot more details than before. In addition, tabs in the panel will appear to show all
the tags you have defined in your notes, sorted as one tab per category. Like for instance
Characters, Locations, Objects, etc. You can also give each note a short description comment on the
same format as the summary comments for chapters and scenes. The short description comment can be
added from the "Insert" menu under "Special Comments".

The last major change in this release is the new multi-select feature in the project tree. You can
now select multiple documents and folders using the mouse while pressing `Ctrl` or `Shift`. By
right-clicking the selected items, you can perform a limited set of operations on all of them, like
changing active status, and the status or importance labels. You can also drag and drop multiple
items under the condition that all the selected items are in the same folder, at the same level.
This restriction is in place due to limitations in the framework novelWriter is based on. But this
should help in cases where multiple documents need to be moved in and out of folders or between
folders. Note that adding the multi-select feature meant that the undo feature of the project tree
had to be removed. It may be added back later.

_These Release Notes also include the changes from the 2.2 Beta 1 and 2.2 RC 1 releases._

### Detailed Changelog

**Bugfixes**

* Fix column widths for columns with no text in the viewer panel lists, and fix an issues where
  icons were not updated on theme switch. Issue #1627. PR #1626.
* Fix auto-selection of words with apostrophes. Issue #1624. PR #1632.

**Usability**

* Use `Ctrl+K, H` for inserting short description comments (alias to synopsis), drop the space
  after the `%` symbol when inserting special comments, add a browse icon to the open project
  dialog, and remove the popup warning for Alpha releases. PR #1626.
* Menu entries no longer clear the status bar message when they are hovered. This was caused by a
  status tip feature in Qt, which prints a blank message to the status bar. PR #1630.
* The novel view panel now scrolls to bring the current document into view when iteratively
  searching through documents in the project. Issue #1555. PR #1632.
* The progress bar on the Manuscript Build dialog now stays for 3 seconds after completion instead
  of 1 second. PR #1634.
* The document viewer panel now shows the importance label next to each entry, and double-clicking
  an entry will open it in the viewer. All entries also now show the content in tooltips so that
  the columns can be shrunk to only view the icon if there is too little space. Issue #1620.
  PR #1639.
* The editor toolbar no longer uses the same buttons for markdown and shortcodes style formatting.
  They have each received their separate buttons. Some additional space has been added between the
  two types of buttons to visually separate them. Issues #1636 and #1637. PR #1638.
* Convert the Synopsis and Comment buttons in the document viewer footer to buttons with both icon
  and text, and drop the label. Issue #1628. PR #1638.

**Internationalisation**

* Updated US English, Norwegian, Japanese, Latin American Spanish, French, and Italian
  translations. PRs #1625 and #1641.

**Documentation**

* The documentation has been updated to cover new features in 2.2. PR #1640.

**Code Improvements**

* Improve memory usage by making sure C++ objects are deleted when they are no longer used. There
  is an issue between the Python and Qt side of things where objects are left in memory and not
  properly garbage collected when they run out of scope. A number of deferred delete calls have
  been added that seems to solve most of these cases. A `--meminfo` flag has been added to the
  command line arguments to provide diagnostic data to help debug such issues. PR #1629.
* Improve handling of alert boxes and their memory clean up, and refactor event filters. PR #1631.
* Clean up unused methods in GUI extensions. PR #1634.

----

## Version 2.2 RC 1 [2023-11-26]

### Release Notes

This is a release candidate of the next release version, and is intended for testing purposes.
Please be careful when using this version on live writing projects, and make sure you take frequent
backups.

Please check the changelog for an overview of changes. The full release notes will be added to the
final release.

### Detailed Changelog

**Bugfixes**

* Revert the change of keyboard shortcut to delete a project tree item made in 2.2 Beta 1 as it
  blocks certain features in the editor. This is a regression. PR 1616.

**Features**

* The old References panel under the Document Viewer has been replaced with a completely new widget
  with a lot more features. The Back-references panel is still there, but is now a scrollable list
  with a lot more information. In addition, tabs for each category of tags are available when there
  are tags defined for them. These panels list all available tags, with a good deal of information
  about them that may be useful to the writer, as well as buttons to open them in the viewer or
  editor. Issues #925 and #998. PR #1606.
* Multi-select is now possible in the project tree, with some limitations. Drag and drop is only
  permitted if the selected items have the same parent item. Any other drag and drop selection will
  be cancelled and the user notified. A new context menu has been added for the case when multiple
  items are selected, with a reduced set of options that can be collectively applied to them.
  Issues #1549 and #1592. PR #1612.
* The "Scroll Past End" setting in Preferences has been added back in. It is slightly different
  than the old one, as this one uses the Qt Plain Text Editor implementation, which has some side
  effects some users may want to avoid. Issue #1602. PR #1605.
* For Windows users, there is now an "Add Dictionaries" tool in the Tools menu where new spell
  check dictionaries can be added. Links are provided to sources for these dictionaries, and a file
  selector tool to import the files into novelWriter. Issue #982. PR #1611.
* You can now update the name of a document by right-clicking on any heading inside the document
  and select "Set as Document Name". This will open the Rename dialog with the text of the heading
  pre-filled. Issue #1503. PR #1614.
* A new special comment, called "Short" can be added to Project Notes. They are identical to
  Synopsis comments, and are in fact just an alias for them. The "Short Description" will be
  displayed alongside the tags in the new panel under the Document Viewer. Issues #1617 and #1621.
  PRs #1617, #1619 and #1622.

**Usability**

* The feature to auto select word under cursor no longer uses the default Qt implementation, and
  has instead been implemented by iterating backward and forward in the text to find the nearest
  word boundaries. It will stop on characters that aren't Unicode alphanumeric as per Python's
  definition. Toggling markup will also move the cursor to after the markup if it was already at
  the end of the word. Otherwise it remains within the word at the same position. The word is not
  selected after formatting if it wasn't selected before. If no selection was made, and no word is
  auto selected, the formatting tags are inserted in-place with the cursor in the middle.
  Issues #1333 and #1598. PR #1600.
* The auto complete context menu is now only triggered on actual user input consisting of adding or
  removing a single character. PR #1601.
* Various improvements to the visibility of the cursor when the dimensions of the editor changes
  have been added. Like for instance keeping the cursor visible when opening or closing the Viewer
  panel, or toggling Focus Mode. Issues #1302 and #1478. PR #1608.
* The Manuscript Build dialog now has a button to open the output folder. Issue #1554. PR #1613.

**Code Improvements**

* Improve test coverage. PR #1607.

----

## Version 2.2 Beta 1 [2023-11-11]

### Release Notes

This is a beta release of the next release version, and is intended for testing purposes. Please be
careful when using this version on live writing projects, and make sure you take frequent backups.

Please check the changelog for an overview of changes. The full release notes will be added to the
final release.

### Detailed Changelog

**Features**

* novelWriter has a new logo and icon. PR #1593.
* The Document Editor is now a true plain text editor. This has a number of benefits and a couple
  of drawbacks. The most important benefits is that the editor responds a lot faster, and can hold
  much larger text documents. The big document limit has therefore been removed. It mostly affected
  automatic spell checking. The syntax highlighter and spell checker are also more efficient, which
  allows for needed improvements to these. The drawbacks are mainly that the editor now scrolls one
  line at a time, instead of scrolling pixel by pixel like before. PRs #1521 and #1525.
* Tags and References are now case insensitive. Their display name on the user interface remains
  the same as the value set for the `@tag` entry. Issue #1313. PRs #1522 and #1578.
* Keywords for Tags and References, and the References themselves, now have an auto-complete menu
  that pops up in the editor on lines starting with the `@` character. It will first suggest what
  keyword you want to use, and when it has been added, use that keyword to look up suggestions for
  references to add. The suggestions improve as you type by looking for the characters you've
  already typed in the tags you've previously defined. Issue #823. PR #1581.
* You can now right-click an undefined tag, and a context menu option to create a Project Note for
  that tag will appear in the menu. On selection, it will create a note in the first root folder of
  the correct kind, and set the title and tag to match the undefined reference, making it instantly
  defined. Issues #1580 and #823. PR #1582.
* Shortcodes have been added to the Document Editor. Shortcodes are HTML-like syntax, but uses
  square brackets instead of angular brackets. So `[b]text[/b]` will make the word "text" appear as
  bold. Shortcodes currently support bold, italic, strike trough, underline, superscript and
  subscript text. The first three are complimentary to the Markdown-like syntax that. The benefit
  of the shortcode emphasis syntax, however, is that it does not care about word boundaries, and
  can therefore be used any place in the text. Including in the middle of words. Issues #1337 and
  #1444. PRs #1540 and #1583.
* A show/hide toolbar has been added to the editor where tool buttons for formatting options are
  available. The toolbar is hidden by default, but can be activated from a three dots icon in the
  top left corner of the editor. Issue #1585. PR #1584.
* Build Definitions in the Manuscript Build tool can now be re-ordered, and the order is preserved
  when the tool is closed and re-opened. Issue #1542. PR #1591.

**Usability**

* The Settings menu in the sidebar now always pops out to the right and upwards from the bottom of
  the icon. The previous behaviour was not guaranteed to stay in the visible area of the screen.
  PR #1520.
* The right click action on a misspelled word now uses the actual spell checker data for lookup.
  Previously, the spell checker would underline a word that was misspelled, but the right click
  action actually had no way of reading where the error line was, so it had to guess again what
  word the user was clicking. Since these two parts of the code used different logic, they
  sometimes produced different results. The spell checker now saves the location of each spell
  check error, and the right click action retrieves this data when generating suggestions, which
  should eliminate the problem of picking the correct word boundaries. Issue #1532. PR #1525.
* The language of a project is not set in the New Project Wizard and in Project Settings. It is no
  longer defined in the Build Settings panel. Issue #1588. PR #1589.
* The way switching focus and view in the main GUI has changed. Pressing `Ctrl+T` will now switch
  focus to the Project or Novel Tree if focus is elsewhere, or if either have focus already, it
  will switch view to the other tree. Pressing `Ctrl+E` will switch focus and view to the Document
  Editor. Pressing `Ctrl+Shift+T` will do the same for the Outline View. The old Alt-based
  shortcuts have been removed. Issues #1310 and #1291. PR #1590.

**User Interface**

* The labels under the sidebar buttons have been removed. The tool tips have the necessary
  information. PR #1520.

**Other Improvements**

* Also the Tags and References keywords are now translated into the project language when these are
  included in Manuscript builds. As long as the phrases have been translated. PR #1586.

----

## Version 2.1.1 [2023-11-05]

### Release Notes

This is a patch release that fixes a layout issue and internationalisation issues with the new
Manuscript Build tool. It also fixes a number of issues related to bugs in the underlying Qt
framework that affects drag and drop functionality in the project tree. These issues were mostly
only affecting Debian Linux package releases.

Other, minor issues related to updating the editor on colour theme change and project word list
changes have been fixed as well. See the full changelog for more details.

### Detailed Changelog

**Bugfixes**

* Fix an issue with width of the last two columns on Selection page of the Build Settings dialog on
  Windows. They were far too wide by default. Issue #1551. PR #1553.
* Fix an issue where a lot of string were not translated to the UI language in the new Manuscript
  Build tool. Issue #1563. PR #1565.
* Fix an issue in the Document Viewer where it wouldn't scroll to a heading further down the page
  when following a reference pointing to it. Issue #1566. PR #1568.
* Add back in checks for illegal drag and drop moves in the project tree. In 2.0, the logic here
  was changed to set certain restrictions on the elements of the project tree itself, but there are
  numerous bugs in the Qt framework related to drag and drop, so the checks are ignored on at least
  Qt 5.15.8. In particular, it is possible to drop items on the root level, and it's possible to
  move root items to other locations. Neither should be possible and will severely mess up the
  project if done. Issue #1569. PR #1570.
* Add a custom auto-scroll feature when dragging an item in the project tree to near the top or
  bottom. This is actually a default feature of the tree widget in the Qt library, but this too is
  broken in some versions of Qt 5.15.x. The default feature has been permanently disabled and
  replaced by a custom written feature that behaves similarly. Issue #1561. PR #1571.
* Fix an issue where the editor document wasn't re-highlighted when the Syntax Theme for it was
  changed. Issue #1535. PR #1573.
* Fix an issue where editing the Project Word List would not refresh the spell checking of the
  editor. Issue #1559. PR #1573.

**Usability**

* Changed how the default UI language is selected. It used to default to the system locale, but
  that is now changed to British English if the system local is not available in novelWriter. The
  only real effects of this is that the dropdown box in Preferences now selects British English if
  the system locale is not available rather than the first in the list (currently Deutch). The
  second effect is that the language on buttons and other Qt components will match the rest of the
  UI. Issue #1564. PR #1565.
* There is a bug in Qt on Wayland desktops where menus don't open in the correct location.
  According to one Qt ticket, QTBUG-68636, this can be mitigated by ensuring all QMenu instances
  have a parent set. This does not fix all issues, but it should help. The menus without a parent
  set have now been updated. Issue #1536. PR #1572.

**Documentation**

* Fixed a number of spelling errors and typing mistakes in the documentation for 2.1. Contributed
  by @nisemono-neko. PR #1567.

----

## Version 2.1 [2023-10-17]

### Release Notes

The primary focus of this release has been a complete redesign of the Build Tool, that is, the tool
that assembles your project into a manuscript document. The new tool, called the "Manuscript Build
Tool" allows you to define multiple build definitions for your project. The build definitions are
edited in a new Manuscript Build Settings dialog, with a lot more options than the old tool.

The reason for this redesign is a long list of feature requests that could not easily be
accommodated in the old, much simpler tool. Far from all the features have been added yet, but now
that the new tool is in place, they will be gradually added in the coming releases.

The key feature added in this release is the extended control you now have for selecting exactly
what part of your project is included in a given build definition. You have the same filters for
selecting documents and notes, and turning on or off root folders as before, but you can now easily
override on a per-document basis what is included or excluded in addition to the filter.

A second major improvement is a better tool to format your manuscript headings. You no longer have
to look up formatting codes and add them manually. Instead, there is now a heading format editor in
the Build Settings dialog for creating the header format, with syntax highlighting included.

#### Other Changes

Among other features is a new option to duplicate documents and folders in the project tree. The
duplicate feature is available from the right-click menu. A proper light colour theme has also been
added. In most cases it will be the same as the default theme, depending on your platform.

There are other, minor improvements as well, and a lot of code improvements under the hood. For a
full list of changes, see the detailed changelogs.

_These Release Notes also include the changes from the 2.1 Beta 1 and 2.1 RC 1 releases._

### Detailed Changelog

**Usability**

* A widget has been added to the Build Manuscript tool main window to show some select build
  settings for the selected build definition. This should make it a little easier to find the
  wanted build definition if there are many available. PR #1516.
* All columns on the Writing Stats tool now uses the same fixed width font. Issue #1442, PR #1518.

**Documentation**

* The documentation has received significant updates for the 2.1 release. PR #1531.

**Packaging and Installation**

* Python 3.7 support has officially been dropped. Python 3.7 has reached end of life, and dropping
  it relaxes some restrictions on development. PR #1515.
* MacOS and Windows is now tested against Python 3.11, and 3.12 has been added to Linux. PR #1515.

----

## Version 2.1 RC 1 [2023-08-31]

### Release Notes

This is a release candidate of the next release version, and is intended for testing purposes.
Please be careful when using this version on live writing projects, and make sure you take frequent
backups.

Please check the changelog for an overview of changes. The full release notes will be added to the
final release.

### Detailed Changelog

**Bugfixes**

* Fixed an issue where closing modal dialogs would close their parent. Issue #1494. PR #1496.
* The log output no longer prints an error message if the project does not have anything in its
  custom dictionary. PR #1495.

**Usability**

* novelWriter will no longer try to restore full screen mode if full screen was activated when it
  was last closed. This never worked right anyway. PR #1498.
* There are several usability updates for the Build Settings tool. Please check the PR for details.
  Some key changes are that the build dialogs are now children of the main GUI, so they can be
  moved freely from each other. The Selection page has been given a new look that should hopefully
  make it easier to understand, and the side bar for the tool has been redesigned. A few labels
  have also been changed to be easier to understand. Issue #1497. PR #1499.
* The alert and message boxes have been reimplemented with the full feature set of the Qt message
  box dialog instead of using the quick access functions with limited functionality. PR #1501.
* A project's spell check dictionary can now be set directly from the Tools menu. Issue #1260.
  PR #1508.
* The document details dialog box now shows a document's creation and update date if that has been
  set. Issue #1423. PR #1510.
* Moving the mouse wheel on any area within the border of the text editor or viewer will now scroll
  the document. Issue #1425. PR #1511.

**Code Improvements**

* A new shared data instance now owns the Gui Theme, the Project class and holds a link to the main
  Gui instance as well. This new class also handles message and alert boxes. The project instance
  is now destroyed and recreated between each project close/open cycle. This should guard better
  from project to project data leakage. PRs #1502 and #1504.
* The spell checker instance has been moved to the new shared data instance where it is destroyed
  and recreated together with the project instance. This blocks against bleed-through of the user's
  custom dictionary. PR #1508.
* Text hash (SHA1) and creation and update time stamps are now added to the document file's meta
  data section. The hash is used to detect file changes outside of novelWriter while documents are
  open. The old checker has been deleted. Issue #1423. PR #1509.

----

## Version 2.1 Beta 1 [2023-07-30]

### Release Notes

This is a beta release of the next release version, and is intended for testing purposes. Please be
careful when using this version on live writing projects, and make sure you take frequent backups.

Please check the changelog for an overview of changes. The full release notes will be added to the
final release.

### Detailed Changelog

**Usability**

* When the main window is resized, the change in size is only assigned to the editor and viewer. To
  resize the project tree area, its slider needs to be moved. PR #1388.
* The default text font on MacOS is now Helvetica instead of Courier. Issue #1463. PR #1479.
* Backup files now contain the project name again. Issue #1476. PR #1484.
* The backup success dialog now displays the file size of the backup file. Issue #1453. PR #1484.
* New root folders in the Project Tree now appear next to the root folder of the item selected when
  the request to make the root folder was made. Previously, it would appear at the bottom of the
  Project Tree. Issue #1259. PR #1487.

**Features**

* A new Manuscript Build Tool has been added. The new tool allows for detailed handling of which
  documents are included in a build, as well as a much better tool for formatting headers. It also
  allows for saving multiple build presets. PRs #1389 and #1466. Issues #971, #1315 and #1448.
* Exported ODT documents now have an accessible style for scene separators. It is also possible to
  define page size and margin sizes from the new build tool. Issue #622. PR #1477.
* A proper light colour theme has been added. The default theme will usually default to light
  colours, but in Qt6 it will not depending on host OS settings, so creating a proper light theme
  is needed. This also allows for some tweaking of the colours. The contrast of the dark theme has
  been improved a bit as well, and a default icon theme is now selected based on the lightness of
  the background if an icon theme is not specified in the theme definition file.
  Issues #1472 and #1473. PR #1475.
* Documents, folders and root folders can now be duplicated from the Project Tree, including all
  child elements. The duplicated content is stored next to the source items, and can then be moved
  to wherever the user wants a copy. Issue #1469. PR #1480.
* A set of new keyboard shortcuts have been added to make some types of navigation in the Project
  Tree easier. `Alt+Up` and `Alt+Down` will move between sibling items in the tree, skipping child
  items. `Alt+Left` will move to the parent of the selected item without triggering the collapse of
  the node like the `Left` key does. `Alt+Right` does the reverse, and both expands the node and
  moves to the first child in one click. Issue #1348. PRs #1488 and #1489.

**Packaging and Installation**

* Support for Python 3.7 is no longer maintained, but has not officially been dropped. It is
  expected to be dropped for the final release of 2.1. PR #1452.
* The `lxml` package has been removed from the source code, dropping it as a dependency of
  novelWriter. The standard Python `xml` library is used instead. The standard library is somewhat
  limited, which is why it wasn't originally used, but when dropping support for Python 3.7, it is
  now good alternative. Issue #1257. PR #1452.
* The `setup.py` file has been removed. The custom packaging utilities in the old `setup.py` file
  are now available in `pkgutils.py` instead. Issues #1437 and #1438. PR #1483.

**Code Improvements**

* All imports of modules are now direct imports instead of going via init files. All subfolder init
  files have been reduced to empty files. PR #1262.
* The mocking of the main config object in the test suite has been rewritten to be easier to deal
  with when writing tests. The new approach also removes the need to access the config object via
  an attribute in many classes, and is now instead accessed directly. This should give a tiny
  performance boost as a bonus. PR #1447.
* The building of manuscript documents from novelWriter source text is now handled by a core
  builder class, thus separating it from any GUI module. Previously, this was baked into the build
  tool. PR #1316.
* SVG icons have been optimised in terms of storage size and object complexity. PR #1456.
* The file names for the project meta data files have been simplified and references to legacy
  formats removed. The wordlist has been converted to a JSON file, and the session log to a JSON
  Lines file. All old files are renamed or converted on the fly when opening the project. PR #1464.
* The core project item and tree classes have been modified to improve how items, and in
  particular, orphaned items are handled. These are mostly internal changes that simplifies how
  items are accessed in the source code. Issue #1481. PR #1482.
* Many of the above PRs adds type annotations to classes and functions in the source code. These
  will be added gradually to the entire source code going forward.

----

## Version 2.0.7 [2023-04-16]

### Release Notes

This is a patch release that fixes a few issues and adds a Japanese translation.

The issues were mostly related to spell checking. In particular, issues with finding the word
boundary when using underscore characters for italics markup. These issues should now be resolved.
In addition, escaped markup characters are now rendered properly in HTML and ODT build formats.

A few usability improvements have also been made. The Add Item menu in the project tree no longer
shows the options to create Novel Documents when an item in the tree is selected that cannot hold
such a document. In addition, the "Change Label" context menu entry has been changed to say
"Rename", which is a more logical choice.

### Detailed Changelog

**Bugfixes**

* Fixed an issue where novelWriter sometimes shows up in the desktop environment on Linux under
  another name than it's supposed to, which meant it would show up without the correct icon. The
  desktop environment was apparently guessing its name based on various values. It is now set
  explicitly. PR #1405.
* Fixed an issue where the syntax highlighting for spell checked words were not cleared when spell
  checking was disabled. Issue #1414. PR #1416.
* Fixed a series of issues with spell checking of words and sentences with italics styling using
  underscores. The spell checker relies on RegEx for splitting words, and RegEx considers the
  underscore a word character. Issue #1415. PR #1417.
* Fixed an issue where escaped markup characters were not being cleaned up when building HTML and
  ODT outputs. Issue #1412. PR #1418.

**Usability Fixes**

* The context menu entry "Change Label" in the project tree has now been changed to say "Rename",
  which matches with the main menu, and is also more in line with what users expect. PR #1403.
* The entries for creating new Novel Documents in the project tree's Add Item menu are now hidden
  when the select item in the tree does not allow Novel Documents. This is less confusing than the
  previous behaviour where it would just create a Project Note regardless of selected file option.
  Issue #1404. PR #1406.

**Internationalisation**

* Added Japanese translation, contributed by @hebekeg. PR #1407.
* Updated existing translations. PR #1407.

**Packaging**

* Legacy AppImage formats have been added to support glibc 2.24. This is a temporary solution until
  the AppImage base image is deprecated later in 2023. Issue #1391. PR #1410.

----

## Version 2.0.6 [2023-02-26]

### Release Notes

This is a patch release that fixes a few minor bugs and a broken feature.

When opening a document from the Novel Tree or Outline View, the Project Tree would receive focus
even when it was hidden. This has been corrected and no focus change is made. The Project Tree now
also receives focus automatically when a new Project Item is created.

The backlinks in the Reference Panel below the Document Viewer were no longer working. They have
now been fixed. They were broken due to a change in the link format in 2.0.

### Detailed Changelog

**Bugfixes**

* The Reference Panel link would no longer recognise the new, shorter links after the 2.0 project
  index change. The explicit check has now been made more lenient and will accept any link that is
  at least 13 characters long (the length of a document handle). Test coverage has been added for
  handling Reference Panel links. Issue #1378. PR #1379.
* The `setSelectedItem` method of the project tree class had a `setFocus()` call. It should not do
  this as global focus is handled by the main GUI class, and doing this explicitly in the
  `setSelectedItem` method is presumptuous. Issue #1369. PR #1379.

**Usability Fixes**

* When creating new items in the project tree via shortcuts, the project tree receives focus. Since
  these actions can be accessed when the project tree does not have focus, a user would have to
  switch focus to be able to open new items. The tree now automatically receives focus when a new
  item is created. Issue #1376. PR #1379.

----

## Version 2.0.5 [2023-02-12]

### Release Notes

This is a patch release that fixes a number of minor bugs and usability issues.

The Project Details dialog now properly updates when another project is opened, and the "Total
editing time" value has a less ambiguous time format. The editor no longer inserts blank lines if
block formats are applied to an empty line. The optional last column in the Novel Tree will now
show all items of the selected type, not only the first, and the column size can be adjusted from
the same menu where the column content is selected. The Open Document build output has been updated
to ODF 1.3 extended format, and passes validation.

An Italian translation has been added, and Russian is currently available for project builds. A
full translation into Russian is on its way.

### Detailed Changelog

**Bugfixes**

* Fixed an issue where the Title, Project Name and Author values of the Project Dialog would not
  refresh when a project was closed and another opened. The issue is with the Qt library and
  caching of the dialog, but novelWriter forces a refresh of the labels. These three were
  previously missing though. Issue #1336. PR #1339.
* Add a check to the data storage class that a path exists before it is returned to other classes
  that uses them for file I/O. Issue #1317. PR #1342.
* Fixed some issues with the Open Document build format as the produced document wasn't compliant
  with the standard. It is now compliant with ODF 1.3 extended format. Issue #1359. PR #1360.

**Usability Fixes**

* The "Total editing time" label on the Project Details dialog now uses the same time format as the
  status bar. That is, HH:MM:SS for times less than 24 hours, and D-HH:MM:SS for times from 24
  hours and above. Issue #1335. PR #1339.
* Fixed an issue where applying block formatting to an empty line would insert a blank line before
  it. This is a consequence of the change from #1175. The line break is now only added if the line
  is _not_ blank. Issues #1349 and #1350. PR #1354.
* The optional third column in the Novel Tree now shows all references for the selected category
  instead of just the first one. The maximum width of the column can also be selected from the
  Novel Tree config menu. Issue #1351. PR #1355.
* The Open Document produced by the build tool now has the necessary title and author meta data set
  so that it can be used in LibreOffice. Other meta data has also been added. Issue #1359.
  PR #1360.

**Internationalisation**

* Existing translations for US English, Norwegian, Brazilian Portuguese, Latin American Spanish,
  and German have been updated. French and Dutch are partially updated. PR #1341.
* Russian project variables have been added. Full translation is forthcoming. Contributed by
  Aleksey (@SKYnv). PR #1341.
* A complete Italian translation has been added. Contributed by Riccardo Mangili. PR #1341.

**Packaging**

* Added App Bundle and DMG packages for MacOS. Contributed by @Ryex. PRs #1276 and #1340.

----

## Version 2.0.4 [2023-01-29]

### Release Notes

This is a patch release that fixes a bug where novelWriter would crash if PyQt5 version 5.15.8 was
installed and imported.

### Detailed Changelog

**Bugfixes**

* Fixed an issue with the version check against PyQt5, which was imported from the wrong package
  when running novelWriter with PyQt5 version 5.15.8, released 2023-01-28. Issue #1324. PR #1325.

----

## Version 2.0.3 [2023-01-08]

### Release Notes

This is a patch release that fixes a few bugs and usability issues. The editing of status and
importance labels in Project Settings should now be a bit more intuitive. Opening a document from
the Outline View that is already open in the editor should now switch to the editor view. The
convert folder to note or document feature in the project tree has also been fixed. Some icons have
been updated and a rendering issue with one of them fixed. Chinese, Norwegian, US English, German
and Spanish translations have been updated as well. A new credits tab has been added to the About
dialog box, replacing the Credits section on the main About tab.

### Detailed Changelog

**Bugfixes**

* Fixed an issue with one of the active icons for the project tree. The SVG paths were not properly
  joined. Issue #1297. PR #1299.
* Fixed an issue where the new open project routine for 2.0 would not check that a project exists
  before trying to open it. This resulted in the open process creating all the expected folders in
  the designated location before realising there was no project there. Issue #1300. PR #1301.
* Fixed an issue with the convert folder to document or note functionality was no longer working.
  The context menu entries were actually just calling the function for converting a file.
  Issue #1305. PR #1306.
* Fixed an issue where the app may crash if an item is added as a child of an item that exists, but
  has invalid settings such that it is rejected by the project tree builder function when the
  project is opened. Now, only items with a parent item that has already been added will be allowed
  into the project tree. The issue was caused by an invalid project file, and is not likely to
  occur during normal use, but such events should still be handled rather than crash the app.
  Issue #1283. PR #1309.

**User Interface**

* The CREDITS.md file has been updated, and its content is now also available in a "Credits" tab in
  the About dialog in the app. The old credits section of the "About" tab has been removed.
  PR #1298.
* Fixed a usability issue where double-clicking an entry in the Outline that belongs to a document
  that is already open in the editor does nothing. Now, the app switches view to the editor when
  the heading is clicked. Issue #1291. PR #1306.
* Change how the editing of status and importance labels work in Project Settings. The form at the
  bottom of the tabs is now always active when a label is selected, and always inactive when none
  is selected. Issue #1290. PR #1308.

**Internationalisation**

* Update Chinese translation. PR #1298.
* Update Norwegian, US English, German and Spanish translations. PR #1311.

**Other Changes**

* An icon theme can now be loaded from the user's data folder alongside a custom user theme.
  Issue #1297. PR #1299.
* Some Inkscape format SVG files have been converted to Plain SVG. PR #1299.

----

## Version 2.0.2 [2022-12-01]

### Release Notes

This is a patch release that fixes a minor issues with syntax highlighting not updating when the
highlighting preferences were changed. It also fixes an issue that broke the FreeBSD release.

### Detailed Changelog

**Bugfixes**

* Fixed an issue where changing the Highlighting Preferences for highlighting quotes, emphasis, and
  multiple or trailing spaces would not reload the syntax highlighter in the editor. The changes
  would only take effect after restarting the app. Issue #1274. PR #1278.

**Packaging and Installation**

* The 2.0.1 release was broken on Linux, but was fixed and the packages rebuilt. However, the
  FreeBSD port was still broken. This release fixes this issue. Issue #1277. PR #1272.

----

## Version 2.0.1 [2022-11-29]

### Release Notes

This is a patch release that fixes a minor issues with loading custom GUI themes that haven't been
updated to include the icon theme setting. The patch also updates the French translation.

### Detailed Changelog

**Bugfixes**

* Fixed an issue where starting the app with a custom GUI theme enabled would not load any icons at
  all if the `icontheme` setting isn't specified. The app now loads the `typicons_light` theme by
  default if no icon theme is set. Issue #1263. PR #1264.

**Internationalisation**

* The French translations has now been completed by @aaribaud. PR #1265.

----

## Version 2.0 [2022-11-28]

### Release Notes

This release includes a major update to the way your project is managed. It also modernises the
user interface. The project file format has also been updated, and your projects will be upgraded
the first time you open them in this release.

There are some major changes under the hood in this release. A lot of the code has been rewritten
and split up into smaller components. A lot of this is to make it more efficient, but also to make
it more modular in preparation for planned future additions. Most of these changes don't affect you
as the user, but there are also a number of big feature changes that you will notice.

#### User Interface Changes

The tabs used to switch between the Project Tree and Novel Tree, as well as between the Editor and
Outline views, have been replaced with a side bar. The side bar is located on the left side of the
main window, and gives you the option to select between "Project Tree View", "Novel Tree View" and
"Outline Tree View". They correspond to the previous tabs.

The side bar also includes a shortcut to the "Build Novel Project" tool. The "Project Details",
"Writing Statistics" and "Settings" buttons that were previously below the project tree are now
located at the bottom of the side bar.

All three views have also been given updates. They each have a label and a toolbar. The Project
Tree View has a dropdown with quick links to all your root folders, which should make it easier to
navigate a large project tree. You can activate the link menu by pressing `Ctrl+L` while in the
Project Tree, so you don't need to move your mouse.

A dropdown menu with all the options for adding new items to your project has also been added to
this toolbar. This too can be activated directly with a shortcut, `Ctrl+N`. More options are
available under the menu button, and there are also a set of move up and down buttons for moving
items.

The Novel Tree View and Novel Outline View have also received toolbars and controls that let you
select which data to show, and customise the view.

#### Changes to Project Structure

A number of changes have been made to how you organise your project in the Project Tree View. For
instance, you are now allowed to add as many root folders as you want, and as many of each kind as
you want. Several users have asked for the ability to add multiple Novel folders, so the old
restriction of only one of each has been removed.

You can now also move documents freely between all folders. The Status or Importance values will
switch place depending on the type of root folder your document is in, but the other value should
be preserved if you move the document back. Previously, they were saved as the same value in your
project, so moving them would imply they were overwritten. The new project file format introduced
with this release has no such restriction.

Your documents are now also able to have other documents as child items. This is another feature
added based on feedback. You no longer need to make a chapter folder and add chapter files inside
it together with the scene documents. You can add the scene documents directly under the chapter
document and drop the folder entirely. If needed, you can convert an existing folder into a
document at any time. However, you are not allowed to convert a document into a folder.

The check mark icon that previously indicated whether a document was included or not in a
manuscript build has been replaced with an active/inactive flag. This was done in preparation for
changes to the Build Novel Project tool which will come in the next release. The active/inactive
flag is now primarily just an indicator to you as the writer whether the document is to be
considered a part of your project or not. That said, an inactive setting still causes it to be
excluded from the Novel Tree View and the Novel Outline View.

The context (right click) menu for the Project Tree has also been updated. You can make nearly all
changes to the item directly from this menu, with the exception of editing the item label, which
still requires a dialog box.

The Split and Merge tools have been rewritten from scratch. You should now have multiple options on
how to structure the resulting document or documents. You can access the new tools from the
"Transform" submenu when right-clicking a project item that supports splitting or merging.

#### Novel and Outline View

The Novel Tree View and Novel Outline View panels have been given a new design. The heading level
is now shown as an indent with a coloured bar that uses the same colour coding as the document
icons. They are technically no longer tree views, but rather a Table of Contents of a specific
novel root folder. If you have multiple novel root folders, you can select which one to view.

In the Novel Tree View, you now also have the option to hide or show a third column of data.
Currently, you can choose between "Point of View Character", "Focus Character" and "Novel Plot". If
you referenced more than one in the document, the column will only show the first entry, so make
sure the most important one is listed first in your document if you use this feature. An arrow icon
is also visible at the end of each row in the tree, and if you click on it, a tool tip should pop
up showing you all the meta data collected for that specific heading in your text.

#### Other Changes

There has been a lot of changes under the hood as well, especially in regards to how the project
structure is handled and saved. The project index has also been almost completely rewritten, and
now collects information about your project more efficiently. This improves the way the project
tree determines which document icon to show you, and it also makes the Novel Tree View more
informative as the data there is updated a lot more frequently.

The New Project Wizard has been updated with some new features, and simplified a bit. The Project
Settings dialog has been updated to reflect some of the same changes.

_These Release Notes also include the changes from 2.0 pre-releases._

### Detailed Changelog

**User Interface**

* The novel tree now updates items that have meta data changes, including for the optional third
  column. Issue #1240. PR #1241.
* When the editor opens or moves on a specific line, the line is now scrolled to the position in
  the editor defined by the typewriter scrolling setting in Preferences. Previously, lines were
  scrolled to the bottom of the editor. Issue #1239. PR #1243.
* When a document is requested opened, but is already open, it is no longer re-opened. Previously,
  this was treated as an implied refresh request, but there are a number of other cases where this
  may be triggered. The main issue here is that it would reset the undo history, which can be
  annoying. Issue #1242. PR #1243.
* The third column in the novel tree now has a max width, and will only display the first reference
  of the list of references for that item. Issue #1238. PR #1245.
* The label at the top of the novel tree becomes a dropdown box when there are more than one novel
  root folder in the project. Issue #1250. PR #1252.
* The author setting in the New Project Wizard and Project Settings is now a normal text box,
  instead of a multi line input box. Only one author value is now saved in the project XML file.
  The field is anyway free text, so the user is free to add multiple authors in the box. For
  projects that already have multiple authors set, the value needs to be set anew. PR #1258.

**Internationalisation**

* German translation has been added by @HeyMyian. PR #1033.
* Other translations have been updated from Crowdin for 2.0. PRs #1251, #1253

**Documentation**

* The documentation has been updated to reflect 2.0 changes. Issue #1070, #1158 and #1181.
  PRs #1248 and #1255.
* Add project XML file format specification. Issue #1012. PRs #1249 and #1254.

**Code Improvements**

* Fixed an issue with circular imports mainly triggered from the test suite. PR #1166.
* Instead of assigning headers in a document a key by its line number, the headings are now
  assigned sequential keys. This makes it easier to detect actual meta data changes, which would
  otherwise be triggered by a change of line number as well. PR #1241.
* Cleaned up the closing project process. Issue #1237. PR #1247.
* The combo boxes to select which novel root folder to display in various locations have been
  merged into a special novel selector class to avoid duplication of code and inconsistent
  behaviour. PRs #1252 and #1253.

----

## Version 2.0 RC 2 [2022-11-13]

### Release Notes

This is a release candidate of the next release version, and is intended for testing purposes.
Please be careful when using this version on live writing projects, and make sure you take frequent
backups.

Please check the changelog for an overview of changes. The full release notes will be added to the
final release.

### Detailed Changelog

Note: This release introduces a new Project XML format with version number 1.5. When the project is
opened, a request to update the file format will show up.

**Bugfixes**

* The custom folders for user defined themes and syntax were not created properly when the app was
  first launched on a new computer. The folders were successfully created on a second launch. The
  error was handled, but reported. This was caused by the folder creation process being in the
  wrong order. Issue #1180. PR #1184.
* Fixed context menu entries for split and merge having inconsistent labels. Issue #1199. PR #1197.

**User Interface**

* The exported status for document items have been renamed to active/inactive. Their icons have
  also been updated. Issues #1196 and #1198. PRs #1200 and #1216.
* The status/importance context menu now shows which label is the current. Issue #1202. PR #1207.
* The status/importance context menu now has a "Manage Labels" action that opens the Project
  Settings dialog at the correct place. Issue #1203. PR #1207.
* Both GUI theme and syntax theme can now be updated without restarting the app. Issue #1171.
  PR #1212.
* The GUI theme now determines which icon theme is to be loaded. It is no longer a separate
  setting. The icon theme can also be reloaded without restart. Issue #1172. PR #1212.
* The block formatting features in the Format menu now also works on empty lines. Issue #1178.
  PR #1214.
* There is now a Format menu entry and shortcut code for synopsis comments. Issue #1177. PR #1214.
* The split document dialog now has the option to move teh source document to trash. Issue #1179.
  PR #1217.

**Other Changes**

* Archived documents are now partially indexed. This mainly means that the item will have the
  correct document icon in the project tree corresponding to its main heading. Issue #1176.
  PR #1183.
* The option to add notes files in the Project Wizard now automatically switches off if there are
  no notes categories enabled. Issue #1192. PR #1201.
* When a project is opened for the first time, the first document in the project is also opened.
  Issue #1219. PR #1223.
* When there is no project open, the toolbars on the Project Tree, Novel View and Outline View are
  disabled. They are enabled only when a project is loaded. Issue #1220. PR #1230.

**Installation and Packaging**

* The AppImage release now has version information in the package name. Issue #1182. PR #1218.

**Code Improvements**

* The main heading of a document is now stored in the item class instead of the index. PR #1183.
* The common module checker functions no longer allow None values. The only one needing it was the
  string checker. A new string checker that allows None has been added for those cases. This makes
  type discovery in the code editor easier. Issue #1185. PR #1188.
* Verbose logging has been removed. The lowest severity level is now DEBUG. Issue #1186. PR #1191.
* Added a number of None checks in the code where especially Qt calls could potentially return
  None, even if they were unlikely to do so. PR #1197.
* Renamed the status bar attribute in the main GUI class as it conflicts with a Qt method.
  Issue #1190. PR #1197.
* The data access methods for the custom config file parser have been improved to better report
  correct type information. PR #1197.
* Saving and loading of XML data is now handled by a separate set of reader and writer classes. The
  reader class is capable of reading all file formats that have been used thus far. The various
  data classes have been improved, and a new XML file format version 1.5 added. Issue #1189.
  PRs #1221 and #1232.
* The index is now automatically rebuilt when the project file format is updated. Issue #1235.
  PR #1236.
* The project folder on disk is now wrapped in a storage class that the project accesses files
  through. It also handles lock files and archiving used for backup. The change is in preparation
  for adding a potential single file format. Issue #1222. PR #1225.
* The Project Wizard now creates the project on disk, and then opens it. This replaces the old
  method where the new project was built directly into the current session. This caused a few
  inconsistencies from time to time, and was a duplicate way of getting a project into the session.
  Issue #1152. PR #1225.
* The Config class has been refactored extensively and now also uses pathlib for all paths. Tests
  are also switched to using pathlib. Issue #1224. PRs #1228 and #1229.
* The updating of tree order method of the project tree class has been updated for better
  performance. PR #1236.

----

## Version 2.0 RC 1 [2022-10-17]

### Release Notes

This is a release candidate of the next release version, and is intended for testing purposes.
Please be careful when using this version on live writing projects, and make sure you take frequent
backups.

Please check the changelog for an overview of changes. The full release notes will be added to the
final release.

**Note:** As of the 2.0 release, novelWriter requires Qt 5.10 or higher and Python 3.7 or higher.

### Detailed Changelog

**Note:** This will no longer be release 1.7, but 2.0 instead due to the major changes to the User
Interface. PR #1146.

**Features**

* The add new documents feature has been made a little smarter and now tries to choose whether the
  added document should be a sibling or a child to the selected document. Issue #1107. PR #1110.
* A folder in the Project Tree can now be converted to a Novel Document or Project Note from the
  item's context menu. This makes sense now that documents can have child items. Issue #1071.
  PR #1128.
* All child elements of an item in the Project Tree can now be collectively expanded or collapsed
  from the context menu. The same action can be triggered on the entire tree from the menu button
  at the top. Issue #1122. PR #1129.
* If using the auto-insert feature for spaces next to punctuation designed for for instance French,
  any existing spaces are first stripped before the correct space character is added. Some users
  find it hard to unlearn the reflex to type the space. Issue #1061. PR #1131.
* The Project Tree now has Quick Links for navigating directly between root folders. This is
  convenient for very large projects. Issue #1137. PR #1165.
* It is now possible to filter out entire root folders on the Build Tool. Issue #1138. PR #1168.

**Bugfixes**

* Fixed a typo in the Lorem Ipsum tool and set a max width for the views bar. PR #1065.
* The language set in the Build Tool is now properly exported to Open Document files. Previously,
  it would be set to English regardless of the user's selection. Issue #1073. PR #1077.
* Since the text editor cursor extends to the right of its position in the window, it would
  disappear under the right-hand margin if it reached the edge. A minimum margin of the width of
  the cursor has been added to the editor, and the same value subtracted from the margin of the
  viewbox. Thus, the cursor no longer disappears. Issue #1112. PR #1113.
* The `Shift+Enter` key combination no longer inserts a Unicode line separator in the text editor.
  Issue #1150. PR #1151.
* Fixed an issue where idle time would not be properly reset when a new project was created.
  Issue #1149. PR #1153.
* Removed the context menu that would appear on the Views Bar, from which the bar could be hidden.
  This is some feature imposed by the Qt library, and it is not wanted. Issue #1147. PR #1153.

**Known Issues**

* An attempt has been made to fix the missing mime icon for novelWriter projects on Linux. The
  newer versions of Nautilus don't seem to display the correct icon due to some changes in the way
  icons are extracted from the theme. The icon displays fine in other places. PR #1068.

**Internationalisation**

* Norwegian and US English translations have been updated. PR #1170.

**User Interface**

* The New Project Wizard has been updated based on user feedback. The "Working Title" setting is
  now called "Project Name". The number of root folders one can create on the options page has been
  reduced to the standard ones. An option to add sample notes has been added, and the option to
  generate chapter folders has been removed. The "Minimal Project" option also no longer creates
  folders. An Archive root folder is automatically added to all new projects, and a Trash folder is
  added to custom projects. PR #1067.
* The border around a lot of Widgets on the main GUI have been removed. PR #1069.
* The Views Bar has been updated since the beta re;ease with better icons, tooltips, and an
  expanding menu on the Settings button. The Build Tool can now also be accessed from the Views
  Bar. PR #1069.
* The editor theme setting in Preferences has been moved back to the General tab where users seem
  to expect to find it. PR #1069.
* A toolbar has been added to the Outline View where the user can select which Novel folder to
  view. A refresh button for a forced reload of the selected Novel folder has been added, and the
  menu to select which columns to show has been added to a new button. This makes it easier to find
  for users instead of having to right-click the table header. Issue #1105. PRs #1063, #1094, and
  #1111.
* The Rebuild Outline and Auto-Update Outline options have been removed from the Main Menu.
  PR #1063.
* The Project Tree has been redesigned. The header is now hidden, and the columns resize
  automatically. A toolbar has been added with buttons for moving items up and down in the tree, a
  button for adding new files, folders and root folders, and a menu button for further options
  affecting the whole tree. These features have mostly bee removed from the Main Menu. PR #1079.
* The context menu of the Project Tree has been rewritten completely. It is now possible to set
  importance and status directly from this menu. Part of issue #973. PRs #1079 and #1105.
* The Edit Item dialog has been replaced with a simple Edit Label dialog. Most of the features
  handled by the old dialog have been moved to the Project Tree context menu. PR #1082.
* The Novel View has been redesigned to match the new Outline View and Project Tree. The header is
  now hidden, and the columns auto-size. The third column can be selected from a set of options, or
  be hidden entirely. A button with a menu can be used to select which Novel folder to show.
  Issue #1041. PR #1084.
* An arrow icon has been added behind each item in the Novel View. Clicking it, will pop up a
  tooltip showing the collected meta data for the heading the item represents. PR #1088.
* The Project Details dialog now supports multiple novel folders. Issue #1078. PRs #1130 and #1167.
* The Split and Merge tools have been rewritten to work with the new feature of allowing documents
  to have child documents. The tools have also had more options added to them. The feature is now
  accessible through the Project Tree item's context menu, and is no longer available from the Main
  Menu. Issues #1072 and #1032. PRs #1148 and #1154.

**Installation and Packaging**

* AppImage distribution has been added by @Ryex. Issue #1091. PR #1092.

**Code Improvements**

* A new test project generator function has been added to replace the dependency on the New Project
  tools in the app itself. This ensures that changing the in-app feature doesn't affect the entire
  test suite. Over time, this generator function should also replace the minimal sample project
  saved in the test suite. PR #1067.
* The index class has been rewritten. The index data is now stored in a hierarchy of objects rather
  than a set of nested dictionaries. The `itemIndex` holds all the data collected from the project,
  and the `tagsIndex` is a reverse lookup index for linking tags back to where they are used. The
  reading/writing of the index to disk between sessions is now handled by pack/unpack functions in
  each object. The index will be regenerated when the user first opens a project as it has been
  completely restructured. PR #1074.
* The index instance is now an instance of the project class, not the main GUI. PR #1074.
* The Outline View has been restructured into a single parent widget in the same manner as the
  Novel View was in the previous pre-release. Related to #1041. PR #1063.
* A lot of main GUI objects have been given new names in the code to better represent what they do.
  PR #1081.
* The converter for the old 1.0 project structure has been simplified. Mostly to reduce the amount
  of code and number of translation labels needed for it. It now produces a single error if
  something went wrong. PR #1083.
* A number of unused icons have been removed from the code base. PR #1164.
* All checks for Qt versions below 5.10 have been removed. PR #1174.

**Not Implemented**

* An idea to make the indexer run in the global thread pool was not implemented. Issue #1076.
* Feature #997 is now obsolete due to the changes made to the Edit Item dialog in #1082.
* Feature #1106 is not implemented. It proposes to hide the option to select Novel folder if there
  is only one. We will see if this is really needed based on user feedback.

----

## Version 2.0 Beta 1 [2022-05-17]

**Note:** The 1.7 release cycle was renamed 2.0 on 2022-10-06. See #1144.

### Release Notes

This is a beta release of the next release version, and is intended for testing purposes. Please be
careful when using this version on live writing projects, and make sure you take frequent backups.

Please check the changelog for an overview of changes. The full release notes will be added to the
final release.

### Detailed Changelog

**Features**

* A simple tool to add Lorem Ipsum placeholder text has been added to the Insert menu. PR #1028.
* Status and Importance flags can now be reorganised in Project Settings. Issue #1035. PR #1040.
* It is now possible to create multiple Root Folders of the same kind. This makes it possible to
  add multiple Novel root folders in a project, for instance. Issue #967. PR #1031.
* All documents can now be dragged and dropped anywhere in the project tree. The document layout
  may be converted in the process. PR #1031.
* Documents in the project tree can now have other documents as child documents. Issue #1002.
  PR #1047.
* Folders in the project tree that are not empty, can now be moved to trash. PR #1048.
* Empty folders are deleted on request, and not moved to trash. Issue #1052. PR #1055.

**User Interface**

* The tabs under the project tree and to the right of the main window have been replaced with a
  toolbar on the left hand side. The toolbar has a set of buttons to change view between Project,
  Novel and Outline. The three buttons that were available under the project tree have been moved
  to the bottom of the new toolbar. Issue #1056. PR #1057.
* When a document changes from a project document to a note, and back again, the Status flag
  setting is preserved. Previously, the Importance setting would overwrite it during the
  conversion. PR #1030.
* Item labels, Status labels, and other labels on the GUI are now run through a "simplify" function
  before being accepted. This functions strips out all white spaces and consecutive white spaces
  and replace them with single plain white spaces. This is a safer format to store in XML, and also
  makes sure there aren't invisible characters floating around in the labels. PR #1038.
* Due to the changes to how drag and drop works, there are no longer any restrictions on folders
  and documents. Only root folders remain restricted in terms of moving. Root folders can only be
  reordered with the Move Up and Move Down commands. PR #1047.
* The label for the highlighting of redundant spaces in the Preferences dialog has been updated to
  better reflect what it does. Issue #1043. PR #1046.
* The New Project Wizard will now try to check if the path selected for the new project can
  actually be used before letting the user proceed to the next page. Issue #1058. PR #1062.

**Internationalisation**

* Dutch translations have been added by Martijn van der Kleijn (@mvdkleijn). PR #1027.

**Functionality**

* Documents that are missing in the project index when a project is opened are automatically
  re-indexed. This also handles cases where the cached index is missing. PR #1039.

**Installation and Packaging**

* Python 3.6 is no longer supported. PR #1004.
* Ubuntu 18.04 packages will no longer be released, due to dropping Python 3.6. Issue #1005.
  PR #1014.

**Project File Format**

* The item nodes in the content section of the main project XML file have been compacted. It now
  consists of a main item node and meta and a name node. All settings have been made attributes of
  one of these three nodes, except the item label which is the text value of the name node. The
  file format version has been bumped to 1.4. Issue #995. PR #993.
* Both Importance and Status flag values are now saved to the project file. This means if a
  document changes layout, the value is no longer lost. PR #1030.

**Code Improvements**

* The linting settings have been updated to select between mutually exclusive options in
  pycodestyle. PR #1014.
* The Tokenizer class has been converted to an abstract base class. PR #1026.
* The class handling Status and Importance flags has been completely rewritten. The flags are now
  handled using a unique random key as reference rather than relying on the text of the label
  itself. This makes it a lot easier to rename them as there is no need to update project items.
  PR #1034.
* Many of the decisions regarding where items are allowed to belong has been delegated to the
  NWItem class that holds the item. Some is also handled by the NWTree class that holds the project
  tree. A new maintenance function in the NWTree class will also ensure that the meta data of an
  item is correct and up to date. This is especially important after an item has been moved, but is
  also checked when items are initially loaded. PRs #1031 and #1054.
* Item handles are now generated using the standard library random number generator. The new
  handles have the same format as the old algorithm, so they are compatible. PR #1044.

----

## Version 1.6.6 [2022-10-25]

### Release Notes

This is a bugfix release that fixes a minor issues with following tags in the editor. It is now
possible to also follow tags that contain spaces.

### Detailed Changelog

**Bugfixes**

* Fix a bug where only the word under the cursor would be looked up when the user tried to follow a
  tag in the editor. The lookup function now uses the same parser for the `@`-line as the syntax
  highlighter does, so they should behave consistently. Issue #1195. PR #1209.

----

## Version 1.6.5 [2022-10-13]

### Release Notes

This is a bugfix release that fixes a few minor issues. The idle time for new projects would be
artificially inflated as the clock was not reset when the project was first created. This only
affects the first entry in the writing statistics. A scaling issue for the Preferences dialog has
also been fixed. It only affected screens with UI scaling enabled. Lastly, typing `Shift+Enter` in
the text editor now creates a regular line break instead of a special line separator. The line
separator serves no purpose in plain text, and was producing inconsistencies in how text is
processed and displayed.

### Detailed Changelog

**Bugfixes**

* Fixed a bug where the idle time was not properly zeroed when a new project was generated after
  the wizard was closed. The idle time would be calculated from the time the previous project
  closed, thus inflating the value. Issue #1149. PR #1159.
* Fixes an issue where the window size of the Preferences dialog would have the GUI scaling factor
  applied twice when the dialog was closed, resulting in the dialog growing in size each time it is
  opened. Issue #989. PR #1159.

**Other Changes**

* The text editor no longer creates a Unicode line separator (U+2028) when the user presses
  `Shift+Enter`. The line separator serves no purpose in a plain text editor, and the code in
  general treats them as regular line break. This caused the line separator to display differently
  before and after saving. The line separator character is now automatically replaced by a
  paragraph separator. Issue #1150. PR #1159.

----

## Version 1.6.4 [2022-09-29]

### Release Notes

This is a bugfix release that fixes a critical bug in the insert non-breaking spaces feature. It
basically no longer worked in the 1.6.3 release. This release also fixes a minor issue where the
text cursor sometimes disappears when reaching the right-hand edge of the text editor window.

### Detailed Changelog

**Bugfixes**

* Fixed a bug in the auto-replace feature of the editor that caused a crash when using the insert
non-breaking spaces feature was used. Issue #1118. PR #1120.
* Back ported a bugfix from 1.7 RC1 that resolves an issue with the text cursor sometimes
disappearing at the right-hand edge of the text editor. Issues #1112 and #1119. PR #1120.

----

## Version 1.6.3 [2022-08-18]

### Release Notes

This is a bugfix release that fixes a rare problem causing novelWriter to crash if the spell
checker language setting was configured to an empty value.

A few other minor issues have also been fixed: The project language setting is now properly
exported to ODT documents. Spaces are no longer inserted automatically in front of colons in
certain meta data settings when the feature is enabled (it is primarily used for French). Lastly,
the slider splitting the editor and viewer panels can no longer be dragged until the viewer
disappears. It was not necessarily obvious how the viewer panel could be restored in such cases.

### Detailed Changelog

**Bugfixes**

* Fixed an issue where the project language setting was not exported when building Open Document
  files. Issue #1073. PR #1087.
* Fixed an issue where the splitter in the main window could be dragged until it hid the document
  viewer panel. This is no longer possible. Issue #1085. PR #1087.
* Fixed an issue where an empty spell check language setting would crash novelWriter. Issue #1096.
  PR #1098.
* Added a checker that blocks the automatic insertion of spaces in front of special characters in
  the cases where the character is a colon in either a meta tag, or as part of the synopsis
  keyword. This feature is used for certain languages like French and Spanish. Issue #1090.
  PR #1099.

----

## Version 1.6.2 [2022-03-20]

### Release Notes

This is a bugfix release that fixes a couple of minor issues. Projects containing one or more empty
documents would trigger a rebuild of the index each time the project was opened. This has now been
fixed. Another fix resolves an error message being written to the console logging output when a new
document was created. Both errors were harmless.

### Detailed Changelog

**Bugfixes**

* Fixed an issue where projects containing empty documents would trigger an index rebuild on open,
  but the empty document would be skipped due to a check that skips empty documents. As a
  consequence, the index would be rebuilt each time the project was opened. Empty documents are now
  added to the index, resolving this issue. Issue #1020. PR #1022.
* Fixed an issue where the shasum calculation would be performed when a new document was created,
  which would fail as the file did not yet exist. The error was handled, but an error message was
  printed to the console log. The shasum is now no longer called if the file doesn't already exist.
  Issue #1021. PR #1023.

----

## Version 1.6.1 [2022-03-16]

### Release Notes

This is a bugfix and patch release that fixes two recursion/loop issues. One would potentially
cause a crash if the window was resized rapidly, and one would cause a hang with certain search
parameters in the editor's search box. The Latin American Spanish translation has also been
updated.

### Detailed Changelog

**Installation**

* When using the new installer on Windows, the project file mime type icon path would not be
  correctly configured in registry. The correct path is now used. PR #1006.

**Internationalisation**

* The Latin American Spanish translation has been updated with two missing translation strings.
  PR #1017.

**Bugfixes**

* Fix a bug where rapidly resizing the main window could trigger the recursion detector in Python
  if done on a slower system. The actual issue may be a race condition or similar, and the change
  made at least makes it harder to trigger. PR #1007.
* With some document searches, it was possible to trigger an infinite loop in the function that
  counts results. It seems to be caused by the QTextEdit widget's find function returning a
  successful result status, but no actual result selection. The fix will now write a warning to the
  log and exit in such cases. The number of results is also now capped at 1000. Issue #1015.
  PR #1016.

----

## Version 1.6 [2022-02-20]

### Release Notes

This release does not introduce any major new features, but is instead a collection of minor
improvements and tweaks based on user requests. There are also a number of changes under the hood
to improve the structure and performance of novelWriter.

Some key improvements to the user interface are:

* The max text width setting in Preferences now also applies to the document viewer, and the
  setting itself on the Preference dialog has been simplified a bit.
* When text is selected in the document editor, the number of words selected is displayed in the
  editor's footer area.
* The search tool in the document editor now shows the number of results in the document.
* The Enter and Ctrl+O keyboard shortcuts should now work the same way in all tree views.
* It is now possible to set a blank section title format on the Build Novel Project tool and get
  empty paragraphs in the output. Previously, a blank format would just remove the section break
  entirely. This change allows the user to define hard and soft scene breaks using level three and
  four headings. The scene and section titles can be hidden completely with two new switches added
  to the user interface.

Other feature changes include:

* The project index is now automatically rebuilt in the event it is empty or incomplete when the
  project is opened.
* The user can now add their own syntax and GUI theme files in the app folder in their user area on
  the host operating system. Where the custom files must be added is described in the
  documentation.
* A Windows installer is yet again provided for novelWriter. If you have novelWriter installed
  using another method, make sure you uninstall it properly first as the two methods are not
  compatible.
* Release versions for Ubuntu 21.04 have been dropped, and added for the upcoming Ubuntu 22.04.
* Most translations have been updated. A Dutch translation is in the works.

In addition to these changes, the documentation has been completely restructured and a new theme
added. The theme has a light and a dark mode.

_These Release Notes also include the changes from 1.6 Beta 1 and RC 1._

### Detailed Changelog

**User Interface**

* The default OS font is not always suitable for editing documents. The default editor font is now
  Arial on Windows and Courier on macOS; if those fonts are available on the platform. Issue #988.
  PR #990.
* Added some some random error messages from Discworld to the error dialog shown when novelWriter
  crashes. They are visible on the dialog title bar if the title bar is visible on the platform.
  This is just a fun addition made to note the #1000 addition to novelWriter. PR #1000.

**Installation**

* Dropped the Ubuntu 21.04 release as it is now deprecated, and added a release package for the
  upcoming Ubuntu 22.04. PR #987.

**Internationalisation**

* The French, Norwegian and Portuguese (Brazil) translations have been updated. #992.

**Documentation**

* Some minor improvements have been made to the Introduction section of the documentations.
  PR #991.

----

## Version 1.6 RC 1 [2022-02-06]

### Release Notes

This is a release candidate for the next release version, and is intended for testing purposes.
Please be careful when using this version on live writing projects, and make sure you take frequent
backups.

Please check the changelog for an overview of changes. The full release notes will be added to the
final release.

### Detailed Changelog

**Features**

* Added switches to hide scene and section breaks on the Build Novel Project tool. This means the
  section format can now be used like the scene format in that it is possible to leave them blank
  to insert an empty paragraph into the manuscript. Issue #972. PR #974.
* The project index is now automatically rebuilt if any of the project files are missing in it when
  the project is opened. This also solves the issue of an empty index being silently ignored.
  Issue #957. PR #975.

**User Interface**

* Remove the descriptive labels for all menu entries that were displayed on the status bar. They
  generally just restated what the menu item label already said, so they weren't very helpful.
  Removing them, as well as removing or joining a number of other labels and tooltips, reduced the
  amount of words needing translating for i18n by about 25%. PR #969.

**Installation**

* A Windows setup installer build option has been added again to the main setup script. It builds
  a setup.exe file with Python and dependencies embedded, based on the minimal zip file of the
  source for Windows. PRs #981 and #983.

**Bugfixes**

* Fix an issue on Windows where a crash would occur if project and backup paths were on separate
  drives. Issue #954. PR #955.
* Fix a JSON error in the Chinese project file translations. PR #963.
* Make sure the document save call doesn't crash when renaming the temp file to the permanent file
  name. This caused a crash on a mapped Google Drive. Google Drive on Linux is not supported, but
  trying to use it still shouldn't cause a crash. Issue #960. PRs #961 and #976.

**Internationalisation**

* Move the whole i18n effort onto Crowdin. This required a few changes to the way i18n files are
  generated and named. PRs #964, #965, #968, and #970.

**Documentation**

* Remove outdated reference to `pylupdate5` as a dependency for i18n. The needed code is now
  included with the i18n framework in the source. PR #963.
* Add a note in the documentation that if the Launchpad PPA is used on Debian, the end point for
  Ubuntu 20.04 must be used. This is due to a change in the compression algorithm used in later
  releases. Issue #956. PR #976.
* Add a new theme for the documentation, and restructure it with better introduction and overview
  sections. PR #978.
* Add information on how to customise novelWriter to the documentation. Issue #892. PR #984.

----

## Version 1.6 Beta 1 [2022-01-04]

### Release Notes

This is a beta release of the next release version, and is intended for testing purposes. Please be
careful when using this version on live writing projects, and make sure you take frequent backups.

Please check the changelog for an overview of changes. The full release notes will be added to the
final release.

### Detailed Changelog

**Features**

* When text is selected in the editor, the word counter in the editor's footer bar shows the number
  of selected words instead of the total document word count. Feature Request #896. PR #899.
* The way page breaks are automatically and manually added has been improved: The Title format no
  longer has an automatic page break, Partition and Chapter formats now always have a page break,
  Scene and Section headers can now have page breaks added manually, and empty scene header format
  will now result in a larger gap between scenes. Feature Request #912. PR #916.
* The Enter, Return and Ctrl+O keyboard shortcuts now open the selected document or item on the
  tree that has focus. That is, on the Project Tree, Novel Tree, or in the Outline Tab. Previously,
  these key strokes only affected the Project Tree. Feature Request #913. PR #945.
* The search tool in the document editor now shows the number of search results when the search
  button is clicked. When the replace tool is used, this number changes if the search result does.
  Feature Request #645. PRs #946 and #947.

**Other Changes**

* The icon themes have been merged and reduced to two complete themes, and the Preferences switch
  for additional dark icons has been removed. The user either selects the Typicons Dark or Light
  theme. No need to match further settings. PR #893.
* Custom GUI themes and syntax themes can now be loaded from the user's data path. The actual
  storage path is determined by the OS. Part of Feature Request #892. PR #893.
* A number of text messages and labels on the GUI have been improved. Issue #923. PR #926.
* The switch in Preferences to disable fixed width text in the editor has been removed. Instead,
  the user just sets the fixed with setting to 0 to disable it. The settings is now also applied to
  the document viewer as well. Issue #924. PR #943.
* The Open Document export file produced from the build tool is now more LibreOffice and OpenOffice
  friendly by using the same default styles as these editors do. Issue #948. PR #949.
* When a document is saved from the document editor, the disk on file is checked for external
  changes before it is overwritten. Such changes can arise from editing the file from another tool
  at the same time, from file sync issues, or even from file system issues. If an inconsistency is
  discovered, the user is asked to confirm the overwrite. Issue #878. PR #890.

**Internationalisation**

* A couple of missing translations, and typos, have been fixed. PRs #921 and #926.
* Latin American Spanish translation has been added by Tommy Marplatt (@tmarplatt). PR #927.

**Bugfixes**

* Fixed an issue where greater or lesser than symbols used in text paragraphs which also has
  formatting tags would cause the formatting tags to be shifted in HTML output. Issue #929. PR 928.
  This fix was backported to 1.5 as patch 1.5.2. A secondary bug was reported in Issue #950, fixed
  in PR #951, and backported to 1.5. as patch 1.5.4.

**Documentation**

* Documentation has been updated to reflect changes and new features. PRs #903, and #916.
* The Readme file for internationalisation has been updated and improved. Contributed by Tommy
  Marplatt (@tmarplatt) PR #917.

**Installation and Packaging**

* The Cantarell font is no longer included in the source and releases. PR #893.
* The way icons are loaded is now simpler and there is no longer a bunch of fallback options. The
  icon sets have been reduced to just two complete folders of coloured Typicons: one for dark and
  one for light backgrounds. PR #893.
* Fixed a couple of issues in the Windows setup scripts where the user never saw the error message
  reporting on missing Python as the window would close before the user would be able to read the
  error. PR #903.

**Code Improvements**

* Cleaned up log output, formatting, docstrings, and various other code structure and debug related
  parts of the source. PRs #904, #926, #930, and #947.
* Optimised various code snippets, either for performance or readability. The code now makes more
  use of Python list comprehension and built-in functions for iterables. PRs #904, and #926.
* Tightened up many of the internal classes, making attributes private, and add setter and getter
  functions where that makes sense. PRs #904, #931, and #937.
* The tools for adding and updating translation files have been improved. The Qt-specific `.pro`
  file has been dropped, and instead the setup tool will scan the entire source tree each time
  language files are updated. TS files can also be specified to the command, or if none are
  specified, all files are updated. PR #915.
* The language file update command in the setup tool now uses the pylupdate6 tool from PyQt6, which
  has been included directly in the `i18n` folder. This tool uses the newer TS file format, which
  the standard PyQt5 tool does not. Related to #911. PR #920.

----

## Version 1.5.5 [2022-01-05]

### Release Notes

This is a bugfix release that fixes an issues with the backup tool crashing the app if the project
path and backup path are on different drive locations. This issue only affects Windows.

### Detailed Changelog

**Bugfixes**

* Fixed a bug with using the commonpath command in Python which will raise an error if the two
  paths don't have a common root. This is particularly an issue on Windows where the paths can be
  on different drives. The command was used in the project backup function, and has now been
  replaced by a safer check. Issue #954.

----

## Version 1.5.4 [2022-01-04]

### Release Notes

This is a bugfix release that fixes an issues with rendering HTML from a document, either in the
viewer or the build tool, when there is a greater or lesser than symbol in a text block that isn't
a plain text paragraph, like for instance a comment or a heading. Any such document would fail to
render.

### Detailed Changelog

**Bugfixes**

* Fixed a bug where a greater or lesser than symbol would crash the html converter loop if the text
  block did not have a format with a 'NoneType is not iterable' error. Most blocks that are not
  plain text have the format set to 'None'. Issue #950, PR #951.

----

## Version 1.5.3 [2021-12-31]

### Release Notes

This is a bugfix release that fixes two cosmetic issues. The first fix resolves and issue with the
emphasis of partition or chapter items in the project tree not changing when the item is changed to
a scene item. The second fix changes how the Create Root Folder submenu works. Instead of disabling
the menu entries that are no longer available, they are instead removed. Disabled menu entries are
not displayed correctly in all colour themes.

### Detailed Changelog

**Bugfixes**

* The syntax themes lack a proper colouring for disabled menu entries. The only place menu entries
  are disabled is in the Create Root Folder menu, so the simplest solution was to just replace the
  enable/disable logic with switching on and off visibility like other menus in novelWriter do.
  Issue #918.
* The if-condition that determined whether an item in the Project Tree were to receive a bold and
  underline formatting for its label lacked the logic to disable these when the item should not
  receive it any longer. I.e., when a chapter was converted to a scene, the emphasis remained.
  Issue #935.

----

## Version 1.5.2 [2021-12-12]

### Release Notes

This is a bugfix release that fixes two issues. The first is an issue with an error in the HTML
output if a paragraph has alignment or indentation tags while at the same time containing
emphasised text. The second is an issue where the application cannot load a project with spell
checking enabled if there is something wrong with the spell check package.

### Detailed Changelog

**Bugfixes**

* When the HTML converter replaced grater than or smaller than symbols with the corresponding HTML
  entities. the position of the formatting tags following in the text would be shifted, but the
  positions were not updated. This is now solved by updating these positions when such a symbol is
  encountered. This issue has been backported from 1.6 development. Issue #929.
* If the pyenchant package is installed, but the underlying enchant library is broken in one way or
  another, the pyenchant package will error, causing novelWriter to crash. All calls to the
  pyenchant package has now been wrapped in try/except blocks to prevent this. Issue #933.

----

## Version 1.5.1 [2021-10-23]

### Release Notes

This is a bugfix release that fixes two issues. One related to the Project Details dialog missing
its translated labels for non-English languages, and a fix concerning switching focus to the
project tree when the Novel tab is visible. If the Novel tab is selected, the focus shift now
correctly gives focus to the Novel tree.

### Detailed Changelog

**Bugfixes**

* The Project Details dialog source file was previously in the wrong source code folder, and was
  moved to the correct location in the previous release. However, the translation framework still
  pointed to the old location. The reference has been fixed and the missing translation strings
  restored.
* Pressing the `Alt+1` key to switch focus to the Project Tree while the Novel Tree was in focus
  would still give focus to the Project Tree, which would be invisible. The focus is now correctly
  given to the Novel Tree when the tab is visible. Issue #913.

----

## Version 1.5 [2021-09-19]

### Release Notes

This release reduces the number of document layouts from eight to two. The full list of changes is
described in the "Novel Document Layouts" section below.

Due to this change, the main project file for your projects will need to be updated when you first
open them in novelWriter 1.5. This is done automatically. The index is updated as well. When this
conversion is done, you can no longer open the project in an older version of novelWriter.

You may also have to make a handful of changes in your novel documents as novelWriter will not make
any automated changes to your actual text. However, the changes are minimal and in any case only
affects the way your manuscript looks like when exported via the Build Novel Project tool. These
details are also described below.

From this release on, Debian packages will be provided for Mint, Ubuntu and Debian users. A new
[PPA](https://launchpad.net/~vkbo/+archive/ubuntu/novelwriter) has also been created. This allows
users to install and update novelWriter automatically on these Linux distros.

#### Novel Document Layouts

The main change in this release is the significant simplification of document layouts. Previously,
there were seven different layouts available for novel documents, in addition to the one layout for
project notes. The original intention of these layouts were partially to define some default
formatting behaviour when exporting your project, and partially as a way to indicate whether a
specific document was a partition, chapter or scene.

With this release, all the seven layouts for novel documents have been merged into a single layout
called simply "Novel Document". The other layout, "Project Note", remains unchanged. The
functionality provided by the various novel layouts have been implemented in other ways, and a few
new formatting codes have been added to accommodate the formatting functionality lost with the
removal of the layouts. They are all available in the Format and Insert menus.

The changes you need to make to your project should be limited to altering a handful of titles and
maybe insert a page break code here and there. The only title formats you need to update are those
for the main novel title and for your unnumbered chapters, if you have any.

Novel titles need to be altered from `# Novel Title` to `#! Novel Title` and unnumbered chapters
from `## Chapter Name` or `## *Chapter Name` to `##! Chapter Name`. That is all. For inserting page
breaks, you can add a single line with the command `[NEW PAGE]` where you want the break to be
inserted. As before, page breaks are automatically inserted in front of all partition and chapter
titles.

You will find these changes described in more detail in the documentation in the
"[Format 1.3 Changes](https://novelwriter.readthedocs.io/en/latest/usage_projectformat.html#a-prjfmt-1-3)"
section.

#### GUI Changes

Due to the above changes, the GUI has been altered a bit. The main changes are in the project tree.
These changes are also reflected in the details panel below the project tree, and to a lesser
extent in the Outline tab.

The layouts were previously a way to indicate the purpose of a specific novel document, like
whether it was a chapter or scene. With these layouts gone, the distinction is instead indicated by
other visual means.

The project index will now record the level of the first header of your document, and select a
different icon for documents with a partition, chapter or scene header. These are colour coded as
green, red, and blue respectively. The project notes have also received a new icon, with a yellow
colour code. Due to this change, the grey icon themes have been removed.

In addition, novel documents with a partition or chapter header will have the document label viewed
as bold and underlined. This feature can be disabled in Preferences if you want a cleaner look in
the project tree.

#### Other Changes

Several improvements have been made to the project index, which means the index will be
automatically rebuilt when you open a project for the first time in the new version. You will get a
notification about this.

The ODT export tool has also been improved. The code that writes out text paragraphs has been
rewritten and now conforms more closely to the Open Document standard. Most of these improvements
will not be noticeable to you as a user, but you may notice that the exported document will now
allow multiple consecutive spaces. Previously, two spaces, or more, would be concatenated into a
single space in the exported document.

The internal spell check tool has been removed. If you want spell checking, you must install the
Spell Enchant tool. The internal spell checker was only ever added because the Python package for
Spell Enchant was not available on 64-bit Windows. This was corrected over a year ago. The main
issue with the internal spell checker was that it only included English, and the large dictionary
files had to be shipped with novelWriter.

Finally, a PDF version of the documentation should now be shipped with your install package. If it
is available, a "User Manual (PDF)" option should be visible in the Help menu. This should give you
access to the documentation also when you don't have an active internet connection.

_These Release Notes also include the changes from 1.5 Beta 1, Beta 2, and RC 1._

### Detailed Changelog

**Installation and Packaging**

* Most packages built by the setup script have a sha256sum file generated alongside it. PR #886.
* Snapshot packages version numbers have been fixed so they work properly with the PPA. PR #887.

**Internationalisation**

* The French translation has been updated by @jyhelle. PR #901.

**Code Improvements**

* Removed some redundant and leftover code in the project class associated with dialog boxes during
  conversion and checking of project file formats. PR #889.

----

## Version 1.5 RC 1 [2021-09-10]

### Release Notes

This is a release candidate of the next release version, and is intended for testing purposes.
Please be careful when using this version on live writing projects, and make sure you take frequent
backups.

### Detailed Changelog

**Bugfixes**

* Fixed a bug where the setting for how often the word counter is run was not saved between
  sessions. PR #882.
* Fix an issue where the information on the Project Details dialog would not be updated if the Qt
  library had cached the dialog since last time it was opened. Issue #842. PR #883.

**Features**

* The internal spell checker has been removed. It was only ever added for use on Windows as the
  PyEnchant tool was no longer maintained and not available for 64-bit Windows. This is no longer
  the case. Having two alternative spell checkers complicated the code a great deal, and the
  internal spell checker also required full word lists to be distributed with novelWriter. PR #875.
* Added a setting in Preferences to change how the word count on the status bar is calculated. The
  new setting allows the project notes to be filtered out, leaving only the word count for novel
  files. Feature request #857. PR #882.

**Installation and Packaging**

* The command line command for starting novelWriter after running the standard setup has been made
  lower case. PR #873.
* A PDF version of the documentation can now be built from the main setup script and is by default
  distributed with the install packages. The PDF manual can be opened from the Help menu. This is
  a more accessible solution to looking up the documentation without an internet connection. The
  old method depended on the Qt Assistant being installed. PRs #873 and #879.
* The setup script can now build standard `.deb` packages for Debian and Ubuntu. Issue #866. PRs
  #876 and #879.
* The icons for novelWriter have been updated and rearranged, and the installation of these
  simplified a bit. PR #879.
* The setup script can now build packages for deployment on the Ubuntu PPA (Launchpad). PR #880.

**Internationalisation**

* The US English and Norwegian translation files have been updated. PR #884.

**Documentation**

* The documentation on how to setup and install novelWriter has been updated. PRs #880 and #881.

----

## Version 1.5 Beta 2 [2021-08-26]

### Release Notes

This is a beta release of the next release version, and is intended for testing purposes. Please be
careful when using this version on live writing projects, and make sure you take frequent backups.

### Detailed Changelog

**Features**

* A new dialog has been added to the Help menu for checking for new updates. It will only check for
  full releases, not pre-releases. The updates are not installed automatically, but a link to the
  website is provided. PR #863.

**Other Changes**

* The grey Typicons themes have been removed. The Typicons colour themes have also been renamed.
  The user configuration will update the theme setting to replace the grey icon theme for dark or
  light background automatically. PR #869.

**Internationalisation**

* The US English and Norwegian translation files have been updated. PR #870.

**Documentation**

* The Windows Setup section of the documentation has been updated and simplified. PR #865.

**Code Improvements**

* The novelWriter main package folder has been renamed from `nw` to `novelwriter`. This will make
  it easier to create packages for novelWriter at a later stage. Especially packages which will
  require adding the main source files to the Python install location. PR #868.

----

## Version 1.5 Beta 1 [2021-08-22]

### Release Notes

This is a beta release of the next release version, and is intended for testing purposes. Please be
careful when using this version on live writing projects, and make sure you take frequent backups.

### Detailed Changelog

**Bugfixes**

* Fix an inconsistency on the minimum required version of Qt and PyQt between the config files and
  the code. PR #846.
* Ensure that an item's status setting is parsed after its class when parsing the main project
  XML. This is just a precaution as the XML writing function always writes the class setting first.
  PR #852.
* On Windows, the Python icon is shown on the task bar when novelWriter is run directly from code.
  This has now been fixed by setting a unique application ID. Issue #860. PR #861.

**Open Document Exports**

* The ODT file writer class has been improved, and the code that writes out paragraphs and header
  section to the XML has been completely rewritten. The new algorithm is more robust and follows
  the open document standard more closely. It still diverts from the standard in a few cases, but
  these are the same points where Open Office and Libre Office diverts. Issue #783. PR #843.
* The previous exporter class would sometimes insert additional line breaks in the generated XML
  for paragraphs. This does not break with the open document standard, but it was unintentional and
  trivial to fix. PR #843.
* Some final clean-up was included in PR #859.

**Novel Layouts**

* All novel layouts, that is "TITLE", "PAGE", "BOOK", "PARTITION", "UNNUMBERED", "CHAPTER" and
  "SCENE" have been merged into a single layout "DOCUMENT". The "NOTE" layout remains unchanged.
  The special formatting of level one header on the title page and chapter headers for unnumbered
  chapters is now handled by a modified header formatting code. Issue #835. PR #837.
* A formatting code for manually inserting page breaks in the text has been added. In the process,
  similar codes were added to insert vertical spaces in the text. Issue #835. PRs #837 and #848.
* Dropping the layouts also triggered several changes to how project items are now displayed. The
  difference between document types is now indicated with a combination of icons and item label
  emphasis. The last column in the project tree also now only shows the item status or importance,
  not item class and layout. The Item Details panel below the tree has also been updated to show
  a usage description instead of layout as the last entry. Issue #835. PRs #847, #849 and #852.

**Other Features**

* A warning will pop up when you launch an alpha version of novelWriter. Since the main branch is
  now also the development branch, people may run novelWriter directly from source without checking
  out a release version. Alpha versions are not considered stable. PR #844.
* Two new settings have been added to Preferences. One to control how much information is shown in
  the last column of the project tree, and one to control whether emphasis is used to indicate
  which novel documents contain a level one or two header. PRs #847 and #852.
* The label on the first column of the project and novel trees have been renamed to "Project Tree"
  and "Novel Outline", respectively. PR #852.
* The Help > User Manual (Online) menu entry sends you to the online documentation, and the local
  documentation is handled by Help > User Manual (PDF), replacing the old Qt Assistant
  implementation. PRs #856, #859 and #862.

**Documentation**

* The documentation has been updated and extended to cover the new layout behaviour and to provide
  information and instruction on how to update the project with the new formats. PRs #850, #851 and
  #855.
* The technical section of the documentation has been updated, and information on how to run tests
  has been added. PR #859.

**Code Improvements**

* The loading and saving of user preferences in the config class has been improved a bit and the
  code modernised to the current recommended practice for the ConfigParser module. PR #826.
* The index class has been improved. Some data fields that were not being used have been dropped.
  In addition, a new function has been added that provides a custom indentation scheme for JSON
  files. The default indentation inserts far too many line breaks. The new function only indents up
  to a certain level. Indenting the JSON files is useful for people who use version control
  software on their projects. The limited indentation scheme reduces the number of diff lines as
  well as reduces the overall file size. PR #840.

----

## Version 1.4.2 [2021-08-30]

### Release Notes

This is a patch release fixing an issue with the auto-replace feature for single and double quotes.
The issue appears when using the new indent and text alignment codes followed by a quote symbol,
and quotes following a tab or non-breaking space.

**Bugfixes**

* Any single or double straight quote following a whitespace other than a regular space, or a left
  indent or right align set of angle bracket codes without a space following them, would be
  erroneously replaced by a closing quote instead of an opening quote. Issue #874.

----

## Version 1.4.1 [2021-07-27]

### Release Notes

This release fixes a couple of minor issue with some of the dialog boxes. The fix was accidentally
left out of release 1.4.

### Detailed Changelog

**Bugfixes**

* The way margins are determined in the paged dialogs used many places, including Preferences, has
  been improved. These margins would sometimes be set to zero when they shouldn't. PR #834.
* Dialogs that are non-modal are no longer duplicated when opened multiple times. Instead, the
  existing dialog is moved to the front. PR #834.

----

## Version 1.4 [2021-07-27]

### Release Notes

This release contains some new features and a lot of code refactoring. Among the main new features
is paragraph alignment and indentation. Regular line breaks within paragraphs are now also
supported. The changes are described in more detail below.

#### Internationalisation

Translation files have been added for Simplified Chinese by Qianzhi Long.

#### Line Breaks

The way line breaks inside paragraphs work has been changed. A single line break is now treated as
a proper line break and will show up in the document viewer and exported documents. A single line
break does not start a new paragraph, but forces a break inside the paragraph like a Shift + Enter
does in most rich text editors. Two line breaks is still needed to start a new paragraph.

The old syntax of adding two spaces at the end of a line to force a line break within a paragraph
will still work as before, so there is no need to change your existing text if you've used this
feature. However, there is a new highlighting feature that will show you where in the text you have
redundant spaces. If you are used to having double spaces between sentences, you may want to switch
off this highlighting feature in Preferences as it will also detect those.

A helper function has been added to the Format menu that can look through a paragraph and remove
line breaks in case you've been using line breaks inside your existing text under the assumption
that the exporter and viewer will ignore them.

I hope this change will not be too inconvenient. I believe the new behaviour will make more sense
for most people. Especially considering some of the feedback I've gotten on how line breaks work.
The original implementation was following the Markdown standard, but since novelWriter is not a
proper Markdown editor and instead just borrows from Markdown, this behaviour always seemed a bit
unnecessary.

#### Text Alignment and Indentation

The default text alignment is left or justified based on your preferences. For documents with the
layout set to Title Page or Partitions, the default is centred. However, sometimes you may want to
override this default. A new set of codes have therefore been added to allow specifying alignment
as well as additional text margins on individual paragraphs.

The logic of the syntax is as follows:

A single angle bracket will push the text away from the edge it points away from. Therefore, a
single `>` before the paragraph, or a single `<` after the paragraph, will add indentation on the
respective side. It's perfectly valid to do this on both sides at the same time.

A double set of angle brackets will push the text all the way towards the opposite side. Therefore,
a double set of `>>` before the paragraph will indicate right alignment, and a double set of `<<`
after the paragraph will force left alignment. Also here both can be used at the same time, which
results in the paragraph being centred.

Format menu entries and keyboard shortcuts have been added so that you don't have to memorise these
codes.

_These Release Notes also include the changes from 1.4 Beta 1 and RC 1._

### Detailed Changelog

**Internationalisation**

* US English and Norwegian translations have been updated by @vkbo. PR #825.
* French translations have been updated by @jyhelle. PR #829.

----

## Version 1.4 RC 1 [2021-07-12]

### Release Notes

This is a preview release of novelWriter 1.4. It contains some new features and a lot of code
refactoring. This release is a testing release, and may contain bugs. Please be careful when using
this version to work on your projects.

### Detailed Changelog

**Internationalisation**

* Translation files have been added for Simplified Chinese. The translation has been provided by
  Qianzhi Long (@longqzh). PR #817.

**Code Improvements**

* Improve PEP8 compliance for the source code. PRs #816 and #820.
* The way messages are written to the logging tool has been improved. PR #818.
* Some improvements to parsing and encoding of HTML has been added. PR #821.
* Test coverage of the document editor has been improved. PR #787.

----

## Version 1.4 Beta 1 [2021-06-13]

### Release Notes

This is a preview release of novelWriter 1.4. It contains some new features and a lot of code
refactoring. This release is a testing release, and may contain bugs. Please be careful when using
this version to work on your projects.

### Detailed Changelog

**Bugfixes**

* A number of calls for the pop-up alert box were missing translation wrappers. That means they
  could not be translated into other languages. The alerts have been fixed, but the PR does not add
  the missing translations. PR #806.
* A duplicate error message from the index class has been removed. PR #758.

**Features**

* Single line breaks are now treated as proper line breaks within paragraphs. Paragraphs are still
  separated by two line breaks like before. This means that it is no longer necessary to leave two
  spaces at the end of the line to force a line break. This is a rather obscure and little known
  feature taken from Markdown, and it isn't very intuitive. Issue #785. PR #786.
* It is now possible to specify text alignment and additional indentation on individual paragraphs
  in the text. Both features use a similar syntax that I hope is fairly intuitive. Menu entries and
  keyboard shortcuts have also been added to make it easier to use these features. Issues #595 and
  #803. PR #804.

**Code Improvements**

* Class initialisation has been made consistent. All GUI classes now inherit the main window as its
  parent class, and all other classes inherit the main project class as its parent. Since the
  project class and the main window class have pointers to each other, all needed pointers are
  available from their respective classes. PR #758.
* The document class has been changed from a reusable class to a class that is intended to wrap a
  single document via its handle. The class was originally written for the document editor where
  the reusable approach made more sense. But it is much simple to create and destroy them in other
  parts of the code when they are not reusable. PRs #758 and #760.
* The document class no longer generates any pop-up alerts. Errors are recorded and retrieved and
  displayed by the parent or caller class. PR #758.
* Refactored the code of the editor class to make it more isolated by making most class variables
  private. PR #779.
* Made similar changes to the viewer class and item details class. PR #780.

----

## Version 1.3.3 [2021-06-13]

### Release Notes

This patch release fixes a potential file encoding issue when running setup on Windows, and a minor
issue with the project word count not being updated immediately when a file is deleted. In
addition, the keyboard shortcuts to change focus between the project tree, the editor, the viewer,
and the outline panel, have been changed for Windows users. They keyboard shortcuts were
interfering with the Alt codes used for special characters. The shortcuts are unchanged for Linux
and macOS.

### Detailed Changelog

**Bugfixes**

* Fix an issue with file encoding when extracting version information from the source code during
  setup on Windows. This seems to be a limited issue, but the changes make the relevant function
  more fault tolerant. Issue #805. PR #807.
* The project word count on the status bar was not always updated when a file was permanently
  deleted from the project. This has now been resolved. Issue #799. PR #810.
* The keyboard shortcuts to change focus will on Windows interfere with the alt key codes as the
  focus shortcuts used `Alt+` to `Alt+4`. On Windows, these are now instead `Ctrl+Alt+1` to
  `Ctrl+Alt+4`. Part of issue #740. PR #808.

**Source Code**

* Remove a redundant line in the source code. PR #802.
* Make the XML parse for project items a little less panicky when encountering unexpected XML tags.
  Generally, this shouldn't be a problem, but the XML parser should silently ignore unexpected tags
  when parsing the project file. This may occur if a project is opened in an earlier version of
  novelWriter. If so, a warning is issued anyway, so it is safe to disregard unrecognised tags as
  the user has already actively selected to proceed and been sufficiently warned. PR #809.

----

## Version 1.3.2 [2021-05-30]

### Release Notes

This is a patch release that fixes some minor issues. One issue was with the split tool, which
would drop the last line from the source document during a split if it was missing a final line
break. A minor issue with the display of word counts on the details panel under the project tree
has also been fixed. In addition, the setup script commands for Linux have been improved a bit.

### Detailed Changelog

**Bugfixes**

* The details panel under the tree would sometimes show character, word and paragraph counts even
  when there was no document selected. This has now been fixed. Issue #781. PR #782.
* The split document tool would drop the last line of the source document. This is generally not a
  problem if the last line has a line break after it, but if it doesn't, it is lost in the split.
  This was caused by an offset error when calculating the split positions in the file and has been
  resolved. Issue #795. PR #796.

**Installation**

* Due to an error in the setup script in the past, a desktop icon was created for novelWriter when
  running the `xdg-install` command. This is no longer the case, but the old icon was still left on
  some user's desktops. The setup script will now remove that icon if it exists when the
  `xdg-install` or `xdg-uninstall` commands are run. PR #784.

----

## Version 1.3.1 [2021-05-06]

### Release Notes

This is a patch release primarily to fix a problem with the Qt translation library used to make
novelWriter available in multiple languages. One of the function calls made to the library was
added recently, in Qt 5.15, which many users on Linux will not have installed on their system. The
issue could be resolved by updating the library, but it's an unnecessary and inconvenient
restriction.

### Detailed Changelog

**Bugfixes**

* The code to load translation files for the main GUI was using a function in the QTranslate class
  that was added in version 5.15, which means novelWriter could not start on a lower version of the
  Qt library if translation files were present. We don't want to force users to use Qt 5.15, so the
  call has been removed. Issue #773. PR #774.

**Other Fixes**

* When generating a new project on Windows, the code that generates the new documents in the
  project would create duplicate handles, causing a warning to be printed. The warning is harmless
  as the collisions are handled. They are caused by the resolution of the clock available to Python
  on Windows being in the tens of millisecond range, much slower than the code generates the new
  project files. The solution was to append a counter to the timestamp from the clock, ensuring
  that the seed is always unique. Issue #769. PR #776.

----

## Version 1.3 [2021-05-02]

### Release Notes

The main feature of the 1.3 release is internationalisation. The release introduces support for
Portuguese, French, and Norwegian for the main GUI, in addition to the default English. The
settings for choosing the GUI language can be found in the main Preferences.

The implementation is such that the projects themselves can use a different language than the one
selected for the GUI. To allow for better support for multiple language projects, the Build Novel
Project tool has the added option to select the language of the injected text into exported
documents. In particularly for the number words that can be added for chapter headers. Available
languages here are the same as mentioned above for the main GUI, plus German.

Settings have also been added in Preferences to allow for automatic injection of spaces or non-
breaking spaces in front of, or behind, certain characters. These are features generally available
in text editors for French, but the implementation in novelWriter simply makes them a free text box
where you can list all characters or symbols where you want a space added automatically.

The translation files for this release have been provided by Bruno Meneguello for the Portuguese
translation, by Jan Lüdke (jyhelle) for the French translation, by Veronica Berglyd Olsen for the
Norwegian translation as well as the minor modifications for US English, and Marian Lückhof
provided the translation file for chapter numbers in German.

The work to rewrite novelWriter to allow for internationalisation was done by Bruno Meneguello and
Veronica Berglyd Olsen.

_These Release Notes also include the changes from 1.3 Beta 1 and RC 1._

### Detailed Changelog

**Bugfixes**

* Fixed an issue when saving a document from the Build Novel Project tool when the previous path
  used for a file dialog no longer existed. The dialog defaults to show the same folder as last
  time it was opened, but should default to the user's home folder if that path no longer exists.
  There was a bug in this default behaviour that resulted in a critical error. Issue #761. PR #762.
* Remove a duplicate error message triggered by a broken cached index file. The two error messages
  reported on the same error. The first of them was also not included in the translation framework.
  PR #759.

**Installation**

* The setup script, and file locations for the translation files, have been updated such that the
  translation files are available in both the PyPi package and in the Minimal Install packages.
  PRs #753, #764 and #765.

**Code Maintenance**

* The source code files for dialogs and tools have been moved out of the main `gui` source folder.
  The `gui` folder now only contains sub-elements of the main GUI class. PR #754.

----

## Version 1.3 RC 1 [2021-04-18]

### Release Notes

This is a release candidate of 1.3. The primary feature of release 1.3 is the addition of
internationalisation (i18n) of novelWriter. The release introduces support for Portuguese, French,
and Norwegian in addition to the default English.

There have been no major changes since the release of 1.3 Beta 1, but the bugfixes and improvements
from version 1.2.3 have been included.

### Detailed Changelog

**Internationalisation**

* The Portuguese translation has been updated and should now be complete. Thanks again to Bruno
  Meneguello (@bkmeneguello). PR #742.

*The changes since 1.3 Beta 1 also include the changes of release 1.2.3.*

----

## Version 1.3 Beta 1 [2021-03-28]

### Release Notes

This is a pre-release of 1.3. The primary feature of release 1.3 is the addition of
internationalisation (i18n) of novelWriter. The release introduces support for Portuguese, French,
and Norwegian in addition to the default English.

This is a beta release. Use with caution on live project.

### Detailed Changelog

**Internationalisation**

* Added support to the source code for internationalisation of the GUI. Thanks to Bruno Meneguello
  (@bkmeneguello) for doing most of the work. Issue #93. PRs #673, #680 and #684.
* Build Novel Project localisation has been added as well. This is separate from the GUI
  localisation as the project may not be written in the same language as the GUI is set to. PRs
  #676 and #682.
* The text editor's auto-replace features now support inserting spaces automatically when replacing
  quotes, as well as in front of major punctuation. These features are common for writing tools
  supporting French and Spanish for instance. Issue #703. PR #704.

**User Interface**

* The Preferences dialog has been updated to be more responsive to varying text label lengths due
  to different needs for different languages. PRs #687 and #711.
* The Project Settings dialog has been improved to be more consistent and user friendly across the
  Status, Importance and Auto-Replace tabs. Issue #691. PR #695.
* The About dialog has been updated to contain more information on contributions. PR #698.

**Translations**

* Portuguese translation added by Bruno Meneguello (@bkmeneguello). PRs #673, #681, #686 and #697.
* Norwegian translation added by Veronica Olsen (@vkbo). PR #679.
* German translation added (Build tool only) by Marian Lückhof (@Number042). PR #683.
* French translation added by Jan Lüdke (@jyhelle). PRs #692, #711 and #713.
* American English added by Veronica Olsen (@vkbo). PR #693.

**Installation**

* Added i18n support to the setup script. PRs #673 and #729.

**Code Maintenance**

* The ISO lookup dictionary for language codes has been removed and replaced with the lookup
  features available in Qt5 through QLocal. The remaining two source files in the constants folder
  have been moved up a level as well. PRs #673 and #730.

----

## Version 1.2.3 [2021-04-18]

### Release Notes

This patch fixes a bug where the user's word list (personal dictionary) was not saved properly for
new projects. The added words were thus "forgotten" the next time the project was opened.

In addition, uninstall commands have been added to the main setup script to make it easier to clean
up icons (Linux and Windows) and registry keys (Windows) if the user wishes to uninstall
novelWriter.

### Detailed Changelog

**Bugfixes**

* Fixed an issue where the initial file for the user dictionary for a new project would not be
  created the first time a word was added to it. This caused the words the user added to the
  dictionary to not be loaded the next time the project was opened. Issue #733. PR #734.
* Some of the `setup.py` commands could not run if the PyQt5 packages were missing due to an import
  command extracting the version number from the main `nw` package. This was not technically a bug
  as the choice to do it this way was made deliberately, but a function has been added to the
  `setup.py` script to allow reading the version number without having to import the `nw` package.
  PR #749.

**Installation**

* An `xdg-uninstall` option has been added to `setup.py` to uninstall the icons installed into the
  system by the `xdg-install` command. PR #736.
* Likewise, a `win-uninstall` option has been added to `setup.py` to uninstall the icons installed
  into the system by the `win-install` command. Issue #743 and discussion #739. PR #749.
* Improvements have also been made to the `setup_windows.bat` script, and a complementary
  `uninstall_windows.bat` has been added as well. PR #749.

----

## Version 1.2.2 [2021-03-28]

### Release Notes

This patch release is a bug fix release addressing some inconsistencies and issues with the
document header buttons when Focus Mode is active. The keyboard shortcuts for search and replace
should now also work in Focus Mode. In addition, the setup script for novelWriter has been improved
when installing on Windows.

### Detailed Changelog

**Bugfixes**

* The way Focus Mode worked when activated through the menu and through the document header button
  were inconsistent. The header button would deactivate the edit, search and close buttons, while
  the menu entry would not. These two methods now call the same set of functions to ensure the
  behaviour is consistent. PR #717.
* Closing the document while in Focus Mode now ends Focus Mode. Previously, the editor would be
  left stuck in Focus Mode with no way to exit. PR #717.

**User Interface**

* The keyboard shortcuts for the search and replace tool now also work in Focus Mode. Previously,
  the menu entries and their shortcuts were deactivated in this mode. Issue #716. PR #717.

**Installation**

* The setup script command do build minimal install archive files now also generate SHA 256 sum
  files. PR #724.
* The setup script will now copy the `novelWriter.py` file to `novelWriter.pyw` if it doesn't exist
  when the `win-install` command is run. Issue #727. PR #728.

----

## Version 1.2.1 [2021-03-21]

### Release Notes

This patch release is a bug fix release addressing issues with the document editor's search and
replace tool. Due to some recently added restrictions on when various tools are active, depending
on which part of the main window has the user's focus, the search tool keyboard shortcuts and
buttons were blocked when they shouldn't. This release resolves these issues.

### Detailed Changelog

**Bugfixes**

* Fixed an issue with the search bar where the button and shortcut actions would be blocked unless
  the document itself had focus. This focus check was added for all the text altering functions,
  but should not affect search and replace. The search and replace actions now bypass the regular
  action pipeline with the focus check. Issue #708. PR #709.

**Documentation**

* Improve the instructions for setup on Linux when manually installing using the `setup.py` script.
  Previously, the documentation wasn't very clear on the difference between a user space install
  and a system wide install. Neither did it explain how to install `setuptools` if the package is
  missing. Issue #714. PR #715.

----

## Version 1.2 [2021-03-14]

### Release Notes

This release is mainly focused on the Build Novel Project tool. Completely new export classes have
been written to support Open Document and Markdown exports. In addition, the way document layouts
are handled have been automated a little to assist the user in keeping header levels and document
layout flags in sync. The third new addition is the ability to record and log idle time during a
writing session to improve the writing statistics information as requested by several users.
Finally, it is now possible to directly edit the project dictionary via a new, simple GUI dialog.

#### The Build Novel Project Tool

The main changes for this release are to the Build Novel Project tool. The Open Document export, as
well as the Markdown export, is now handled entirely by code written for novelWriter. Previously,
these export features depended on the underlying Qt library's save routines connected to the
preview document shown in the build dialog. Using this method of export both meant that the content
of the document was dependent on the preview being generated first, and it also meant that the
exported document had limited support for novelWriter-specific features and custom formatting. The
new export class should generate a much better result, especially for the Open Document formats.
The Open Document standard is supported by Open Office, Libre Office, Google Docs, Microsoft Word,
and probably a number of other applications too. The Markdown export hasn't changed a lot, but
should be a slight improvement on the previous export feature.

These changes to the build tool also imply that the saving process is now independent of the
content of the preview window, meaning you don't have to rebuild the preview before saving, which
was previously the case. To make this more consistent, the PDF export option has been moved to the
print button as it is actually a print-to-file feature under the hood, not technically a proper PDF
export format. It is exactly the same as printing to file from the print preview dialog.

In addition to the changes to the export features, the Build Novel Project tool now also has
controls for line height, which applies to all rich text export formats, and the option to replace
unicode characters with appropriate html entities for html export.

#### Document Layout Automation

Among other changes in this release are a few improvements to the process of creating and changing
documents. When a new document is first created, the header is generated from the assigned label
and layout.

In addition, for some document layouts, when the user changes the header level of the first header
of the document, the document layout setting is updated accordingly. This should reduce the need
for the user to maintain two ways of assigning the role of a given document. This automation only
applies to combinations of header level and current document layouts where there is no ambiguity.
For instance, changing the header level in a "Scene" document from level 3 to 2 changes the
document layout automatically to "Chapter". But changing the first header of a "Book" layout
document from 1 to 2 does not change the document's layout as the "Book" layout is a generic
document layout and it's perfectly reasonable for its first header to be a chapter header.

Keep in mind that novelWriter treats documents with layout "Book", "Chapter" and "Scene" exactly
the same during exports. The distinction is only meant as a way to indicate the purpose of a
document in the project tree. This new automation is meant to assist in keeping this information up
to date. The other layouts do have an effect on formatting during export, and are generally left
alone.

#### The Session Timer and Idle Time

Another change that has been requested by a couple of users is to have the session timer in the
status bar stop counting when the user is inactive (idle). This feature is optional, and can be
controlled from Preferences. The definition of "idle" in this context is either that the user is
active in a different application than novelWriter (loss of focus) or that the user has not made
any changes to the current document for a given amount of time. The time threshold is by default
five minutes, but can be altered in Preferences.

In addition, the idle time is also recorded in the session log, and can be viewed in the Writing
Statistics dialog and exported with the rest of the information. The idle time is recorder in the
logs regardless of whether the status bar clock takes idle time into consideration or not. So even
if you turn off the idle time switch in Preferences, the other idle time setting still affects the
writing stats log entries.

#### Other Changes

The user dictionary of the project, where words added to the dictionary from the document editor
go, can now be viewed and edited with a new "Project Word List" tool in the "Tools" menu.

A small additional feature added is also the ability to undo the last move of an item in the
project tree. The keyboard shortcut for this is `Ctrl+Shift+Z`, or it can be accessed from the
menu. The feature can only undo the last move, but it includes both documents moved to trash, moves
by up/down keypress or menu entries, and drag and drop moves.

A new keyword has been added to mark characters in the story. The new keyword is intended to tag a
character as the focus character for a chapter or scene. This is useful for stories where the
point-of-view character and the focus character are different.

Lastly, two bugfixes have been made as well. The Empty Trash feature was no longer working due to
an earlier fix solving another issue. The feature has now been restored. In addition, the indexer
now checks that a keyword (tag or reference) is valid before saving it to the index. Previously, an
invalid keyword could be saved to the index and potentially crash the application.

_These Release Notes also include the changes from 1.2 Beta 1 and RC 1._

### Detailed Changelog

**Bugfixes**

* Fixed an issue where a typo in a tag or reference using the `@` character would add an invalid
  entry into the project index. The invalid keyword would be saved to the index cache, invalidating
  the index on next load. For earlier versions of novelWriter before 1.1.1, it would also cause a
  crash. Invalid keywords are now rejected during indexing. Issue #688. PR #689.
* The "Empty Trash" option was no longer working due to an earlier fix that added a requirement
  that the project tree has focus to allow the emptying to proceed. Since the Empty Trash feature
  opens a dialog, the tree loses focus, and the deletions are therefore ignored. The focus check is
  no longer considered when emptying the trash. Issue #701. PR #702.

**Documentation**

* The documentation has been updated to reflect the changes in 1.2, and a few corrections pointed
  out by @jyhelle applied. PR #700.

----

## Version 1.2 RC 1 [2021-03-02]

### Release Notes

_The Release Notes have been moved and merged into the 1.2 notes._

### Detailed Changelog

**Bugfixes**

* If a tag or reference keyword was mistyped, it would still be indexed and put into the index.
  This caused the index to be deemed invalid on the next loading of the project, triggering a
  rebuild. A check has been added to the code parsing the lines starting with `@` to ensure only
  valid keywords are written into the index. Issue #688. PR #690.

**New Features**

* Added a tool to edit the project's user dictionary. This is the dictionary where the "Add Word to
  Dictionary" actions from the document editor go. The dialog tool allows for listing, removing and
  adding words to this dictionary. Issue #665. PR #669.

**User Interface**

* Pressing the `F2` key when in the document editor will open the Item Editor for the open document
  instead of the one selected in the project tree. PR #664.
* The shortcut for deleting an item in the project tree has been changed from `Ctrl+Del` to
  `Ctrl+Shift+Del`. This change was also backported to version 1.1.1. Resolves #629. PR #664.

----

## Version 1.2 Beta 1 [2021-02-11]

### Release Notes

_The Release Notes have been moved and merged into the 1.2 RC 1 notes._

### Detailed Changelog

**New Features**

* A full Open Document exporter has been written and added for the Build Novel Project tool. This
  replaces the previously used Qt Save to ODT which just saved the content of the preview window to
  an ODT file. The Qt pathway was very limited and didn't generate proper formatting classes. The
  new export class can generate both full `.odt` and flat XML `.fodt` files. The formatting support
  of this exporter is equivalent or better than the HTML5 exporter, which was previously the best
  supported option. Solves issue #611. PRs #607, #652, #660, and #654.
* A full Markdown exporter has been written and added for the Build Novel Project tool. This too
  replaces a Qt feature that was used to save the content of the preview window into a markdown
  file. The exporter allows for both standard markdown and GitHub flavour markdown. The only
  relevant difference being that the latter allows strike through text. Issue #617. PR #650.
* The Build Novel Project tool now has a "Line height" property that is applied to the preview, and
  to the HTML5 and Open Document export formats. Discussion #653. Issue #654. PR #660.
* The Build Novel Project tool now has an option to convert Unicode characters to HTML entities on
  export to HTML5. Previously, some symbols were converted while others were not. This option
  provides a more consistent "all or nothing" option. PR #660.
* The last file or folder move in the project tree can now be undone from the Project menu or by
  pressing `Ctrl+Shift+Z`. PR #632.
* When a document header level is altered in a novel file of layout type Scene, Chapter,
  Unnumbered, or Partition, and that document is saved, the document's layout setting as seen in
  the project tree is updated to reflect the new level of that heading. This helps reduce the
  duplication of effort by the user to keep this information in sync. See discussion #613. This is
  an acceptable solution to #614. Issue #618. PR #620.
* The session timer now records the amount of time the user is idle. Idle is defined to be when the
  application window does not have focus, and when the user hasn't made any changes to the document
  open in the editor for a specified amount of time. The default is 5 minutes. The idle time is
  recorded to the session log and can be shown in Writing Statistics. Optionally, the status bar
  session timer can also be set to pause when the user is considered idle. Issues #606 and #651.
  PRs #656 and #661.
* It is now possible to tag a character as the focus character for a give section of text. This is
  useful for cases where the point-of-view character differs from the main character of the story,
  or the part of the story. Issue #605. PR #662.

**User Interface**

* A document's class and layout is now displayed next to its status or importance in the document
  editor footer bar. PR #628.
* When a new document is created, the header of the file is automatically generated based on the
  document's tree label, and the level determined by the selected layout. Issue #530. PR #628.
* On the Build Novel Project GUI, the PDF option has been moved from the "Save As" button to the
  "Print" button. This more accurately reflects what it actually does: print the content of the
  preview to a PDF using the printer pathway. This also means that all remaining items on the "Save
  As" dropdown list now can be executed regardless of the content of the preview window. They all
  run their own separate build process. This resolves #611. PR #650.
* Export to plain text has been dropped. PR #617.

**Code Improvements**

* The index class now scans every element of the loaded index cache before accepting it. This means
  that any unrecognised content will trigger a full re-indexing. This is particularly useful when
  opening an index that was saved by a later release. Every entry that requires a lookup is checked
  to avoid potential key errors for instance. All values are also checked for correct data type.
  The new check is extensive, but still fast enough that it only adds a few milliseconds to the
  startup time. PR #619.

**Code Maintenance**

* Cleaned up some redundant code after PR #637. PR #638.

----

## Version 1.1.1 [2021-02-21]

### Release Notes

This patch makes a couple of minor improvements to the GUI. The keyboard shortcut for deleting
entries in the project tree has been changed from `Ctrl+Del` to `Ctrl+Shift+Del` to free up that
shortcut for the document editor. It is now possible to use the shortcut for deleting the word in
front of the cursor, a common and useful feature of many text editors.

The way the negative word count filter option works on the Writing Statistics tool has been changed
to be more intuitive. Enabling this filter now appears to remove all negative entries without
altering the other entries. Previously, the removed negative counts would be included in the
following entries to make it consistent with the total word count. In addition, writing sessions
shorter than five minutes, and with no change in the word count, are no longer recorded in the
session log file.

Other changes include improving the speed of the internal spell checker, used when the Enchant
spell check library isn't available. The internal spell checker is no longer significantly slower,
but is still lacking in functionality compared to Enchant.

### Detailed Changelog

**User Interface**

* The default GUI font on Windows is now Arial. It works better with the Qt framework than the
  default system font. If Arial is missing, it falls back to the bundled font Cantarell. PR #655.
* The way word changes are calculated on the Writing Statistics tool has changed when the option to
  exclude negative word counts is active. Previously, the entries with negative counts were
  filtered out, but the change in count was still applied to the next line, altering the value.
  Now, the GUI will instead just drop the lines that are negative and keep the other lines
  unchanged. This is more intuitive, but it also means that the total count now longer matches the
  sum of the lines. PR #659.
* The keyboard shortcut for deleting entries in the project tree has been changed from `Ctrl+Del`
  to `Ctrl+Shift+Del`. The `Ctrl+Del` shortcut is thus free to be used exclusively by the editor to
  delete the word in front of the cursor. Having the same shortcut do different things depending on
  which area of the GUI has focus is a bit confusing. Related to #529. PR #666.

**Other Improvements**

* The internal spell checker, which is used when the Enchant library isn't available, has been
  given a significant speed improvement by caching the imported dictionary as a Python `set`
  instead of a `list`. The `set` has a hashed key lookup algorithm that is significantly faster.
  PR #668.
* Sessions shorter than 5 minutes, and with no word count changes, are no longer recorded in the
  session stats log file. PR #685.

**Installation**

* The PyPi packages now include the `setup.py` file, which makes it possible to install icon
  launchers for novelWriter on both Linux and Windows after installing with `pip`. PR #655.

----

## Version 1.1 [2021-02-07]

### Release Notes

The main change in this release is the addition of a new tab to the project tree on the left side
of the main window. The regular project tree is now on a tab named "Project", while a new tab named
"Novel" displays a simpler version of the information on the main "Outline" page. It lists all the
headers of the novel part of the project, as well as the word count and point-of-view character of
each section. This is an alternative way to navigate the novel part of the project. The various
tree views are now also kept better in sync when the user selects various documents and headers.

In addition, a new information dialog named "Project Details" has been added. It replaces the
"Details" tab in "Project Settings", and adds more information about the novel part of the project.
In particular, a "Table of Contents" in the "Contents" tab displays a summary of the main parts
and chapters of the project, their total word counts, and an estimated page count. This was made in
response to users asking for ways to estimate the total page count of the project. The page count
is estimated based on a words per page setting, which can be changed on the dialog window.

Since the tabs below the project tree now add some extra room on the GUI, some convenient buttons
have been added in the same area, with direct access to "Project Details", "Writing Statistics" and
"Project Setting".

A few other minor changes have been made as well. The Preferences dialog has been improved with
clearer categories and hopefully better help text. Some new options have been added too. They allow
syntax highlighting of multi-paragraph quotes. The highlighter can now optionally accept quotes to
be left "hanging", that is, no closing quote in the same paragraph.

_These Release Notes also include the changes from 1.1 RC 1._

### Detailed Changelog

**Bugfixes**

* A `None` check in the details panel below the project tree was missing, resulting in an
  occasional error message being printed to the logging output. The error was otherwise handled, so
  this is mainly a fix to prevent the error message. PR #639.

**User Interface**

* The word counts in the Novel tree are now updated each time a file is saved. Issue #636, PR #637.
* A "Remove" button has been added to the "Open Project" dialog. Previously, recent project entries
  could be removed by pressing the `Del` key, but no obvious other methods were present on the GUI.
  PR #639.
* When the search function is activated, the text in the search box is automatically selected.
  Issue #645, PR #639.

**Installation**

* The minimal zip release package tool in `setup.py` has been improved to generate tailored
  packages for each operating system. The old `pyinstaller` build command has been removed, but the
  manual build path for a Windows setup.exe file has been kept. PRs #643 and #644.

----

## Version 1.1 RC 1 [2021-01-31]

### Release Notes

This is a preview and test release for version 1.1.

A few new features have been added. The primary change is that the project tree on the left side of
the main window now has two tabs. The regular project tree is now on a tab named "Project", while a
new tab "Novel" displays a simpler version of the information on the main "Outline" page. It lists
all the headers of the novel part of the project, as well as the word count and point-of-view
character of each section. This is an alternative way to navigate the novel part of the project.
The various tree views are now also kept better in sync when the user selects various documents and
headers.

In addition, a new information dialog named "Project Details" has been added. It replaces the
"Details" tab in "Project Settings", and adds more information about the novel part of the project.
In particular, a "Table of Contents" in the "Contents" tab displays a summary of the main parts
and chapters of the project, their total word counts, and an estimated page count. This was made in
response to users asking for ways to estimate the total page count of the project. The page count
is estimated based on the word count, and can be changed on the dialog window.

Since the tabs below the project tree now adds some extra room on the GUI, some convenient buttons
have been added, with direct access to "Project Details", "Writing Statistics" and "Project
Setting".

A few other minor changes have been made as well. The Preferences dialog has been improved with
clearer categories and hopefully better help text. Some new options have been added too. They allow
syntax highlighting of multi-paragraph quotes. The highlighter can now optionally accept quotes to
be left "hanging", that is, no closing quote in the same paragraph.

### Detailed Changelog

**User Interface**

* Added a Novel tab under the project tree where the user can navigate the novel's layout of
  chapters and scenes, similar to the Outline view, but next to the document editor. The Outline
  view and Novel/Project trees now also behave more in cooperation. When files on one are selected
  or moved, the other will follow and update. Issues #541 and #185, PR #538.
* Added a Project Details dialog that lists project details (moved from Project Settings' Details
  Tab) and a Table of Contents tab where details on chapter level is displayed. This table also
  shows an estimated page count and estimated page location of each chapter. Issue #528, PRs #555,
  #598 and #603.
* Added three buttons below the project tree that connects to Project Details, Writing Statistics,
  and Project Settings. PR #555.
* The settings and tabs in the Preferences dialog have been re-arranged into more tabs with less
  options on each tab. PRs #577 and #624.
* Minor changes to margins and alignments of widgets on the main GUI. PR #565.
* Added a keyboard shortcut to change focus to the Outline tab. The focus change now also ensures
  that the main GUI also switches to the tab where the focus is shifted. Issues #609 and #612,
  PR #615.
* The cursor should now also be visible when opening a blank document and the editor has focus.
  Issue #608, PR #621.

**Text Editor**

* Added support for multi-paragraph quote (dialogue) highlighting. This feature is optional, and
  can be enabled/disabled in Preferences. Issue #546, PR #577.
* Add several new symbols to the Insert menu/ Issue #602, PRs #603 and #604.

**Other Changes**

* Trigger a save document call before the Build Novel Project tool starts the build. This ensures
  that unsaved changes in the editor are included in the build. Issue #610, PR #616.

**Code Maintenance**

* Reformatting of source file headers and adding license headers to all test source files. Test
  source files are now also organised into subfolders. PR #563.

----

## Version 1.0.4 [2021-02-03]

### Release Notes

This patch release fixes a couple of minor issues with the Preferences dialog and the behaviour of
one of the keyboard shortcuts.

Aside from these fixes, the main point of this patch is to add new setup features for novelWriter
on Windows. A Windows installer will no longer be provided for the foreseeable future, and instead
functionality has been added to the main setup script to create desktop and start menu icons.

### Detailed Changelog

**Bug Fixes**

* Fixed an issue with the Preferences dialog where the setting for justified text was mixed with
  the setting for fixed text width. This meant that the justified text setting could potentially
  get overwritten when the Preferences were changed and saved. Issue #623, PR #625.
* Fixed an issue with the Open Project dialog where the list of recent projects would contain
  duplicate entries if the dialog was opened multiple times. PR #627.

**User Interface**

* The `Ctrl+Del` keyboard shortcut is now only active when the project tree has focus. Since this
  is also a common shortcut in many applications for deleting the next word ahead of the cursor,
  the activation of the delete file function when the editor has focus is unexpected to some users.
  Issue #629, PR #631.

**Installation**

* A new command has been added to the `setup.py` script. The new command, `win-install`, will
  create a desktop and start menu icon for novelWriter when run in the source folder. A windows
  batch file, `setup_windows.bat`, has also been added. Running this file from the source folder,
  either by command line or by double-click, will install dependencies from PyPi and set up the
  icons and file association with novelWriter project files. This should make it easier to run
  novelWriter from the source folder on Windows. PRs #634, #641 and #642.

**Documentation**

* The documentation on how to setup and install novelWriter has been extended and reorganised into
  one file per operating system. Some of the other documentation files have also been moved to a
  different section. PR #634.

----

## Version 1.0.3 [2021-01-24]

### Release Notes

This patch release fixes a minor bug sometimes encountered when running novelWriter from command
line on Windows. In addition, the Solarized Dark and Solarized Light themes have been added to the
selection of GUI and syntax themes by a user contribution.

The main change in this release is to the install scripts and the documentation related to
installing and running novelWriter. The primary change is a different method of packaging the app
for Windows. Instead of building an `.exe` file, the new setup instead builds a runnable zip file
`.pyz`. The executable would often be mistakenly flagged by virus control software due to the
packaging tools. This is a known problem with pyinstaller and similar tools, but such warnings are
always concerning even if they are false positives.

### Detailed Changelog

**Bug Fixes**

* Fix crash when starting novelWriter from command line on Windows from a different mounted drive
  than where it is installed. This was caused by a relative path lookup that defaulted to the wrong
  current directory. This works on Linux/macOS which have a common root path, but not on Windows.
  Issue #581, PR #587.

**User Interface**

* Added Solarized Dark and Solarized Light GUI and syntax themes. PR #578 by @nullbasis.
* The Typewriter Scroll Mode now works better in combination with the Scroll Past End feature. The
  scroll mode still only works when there is actually any document to scroll into, but previously
  it would also not work until the total length of the document reached 40% of the height of the
  editor window. This was quite confusing. This limit is now reduced to 10%, which means that as
  long as the Scroll Past End option is enabled, the Typewriter Scroll will always work according
  to its settings. Issue #589, PR #593.

**Installation**

* Merged the `make.py` script into `setup.py`. PR #584.
* Added a second way to build distributable packages of novelWriter for Windows. The new method
  does not use any of the current package tools that produce a Windows executable of the app. These
  packages tend to cause false virus warnings. This new method uses the Python tool `zipapp` to
  bundle novelWriter as an executable `.pyz` file, and adds Python embeddable and library
  dependencies into the same folder. The folder itself can be distributed as-is, or a Windows
  installer executable can be generated with `setup.py setup-pyz`. Issue #580, PR #584.

**Documentation**

* Updated documentation, main README and Contribution Guide to make them more consistent and to
  improve installation instructions. Based on issue #586 and input from @mgrhm. PR #592.

**Other Changes**

* The HTML generator now adds line breaks after `div` blocks used to wrap tag/reference lines. This
  makes the output easier to process by scripts, but has no impact on browser rendering and import
  into other applications. PR #597.

----

## Version 1.0.2 [2021-01-19]

### Release Notes

This patch release fixes a few minor cosmetic issues, a minor issue with the indexer, and a bug
when adding words to the user's own spell check dictionary. Additionally, the documentation has
been updated based on user feedback, and some install issues resolved.

### Detailed Changelog

**Installation**

* The dependency list was missing in the setup configuration for PyPi due to a bug in the
  `setup.cfg` file. The dependencies have been moved to a different section where the setup tool
  now picks them up properly. Issue #570, PR #573 by @stranger-danger-zamu.

**Bug Fixes**

* Fixed an issue with note files being moved between a non-novel root folder and a novel root
  folder without clearing its index entry in the former note or novel index. This would cause
  duplicate entries for such a file. PR #558.
* Fixed a cosmetic issue where the meta data panel below the project tree was not cleared when the
  project was closed. PR #559.
* Fixed an issue where the main window title would not be cleared when a project was closed, and
  the new title not set when a new project was first created. Issue #560, PR #561.
* The editor context menu option to "Add Word to Dictionary" should also be visible when there are
  no spell checker suggestions. The entry was erroneously added under an if-condition that excluded
  it in those cases. Issue #574, PR #575.

**Documentation**

* Fixed some typos and spelling mistakes in the documentation, and reworded parts of the text that
  were unclear. The technical page has also been extended with more information on project folder
  structure. PR #557.
* Clarify install instructions, and remove the duplicate instructions in the README file and
  replace them with a brief section. The full instructions are in the documentation. Issues #566
  and #570, PR #576.

----

## Version 1.0.1 [2021-01-10]

### Release Notes

This release is mainly to bring the documentation up to date, as I forgot to update the install
instructions in the original 1.0 release. I also forgot to change the various settings and help
texts that describe novelWriter as under initial development (beta state).

Some minor improvements have been made to the "Edit Project Item" dialog and some restrictions on
the settings available for documents created in the "Outtakes" folder relaxed. A few minor issues
with the document and project changed icons on the status bar have also been resolved. The
indicators were previously set to changed status even if no actual change had been made to the
project.

### Detailed Changelog

**User Interface**

* Added the Outtakes folder to a list of root folders that will allow the setting of file layouts
  otherwise only permitted under the Novel root folder. It makes sense to permit the files in this
  folder to have the same extended settings that Novel files have. PR #552.
* The text input and dropdown boxes of the Edit Project Item dialog box now extend when the dialog
  window is resized. Previously, the space between the label and the box would stretch instead,
  which isn't very useful. PR #552.
* The document and project changed status icons on the status bar are now set to unchanged status
  when the project is opened. In addition, an issue with the status being set to changed on various
  events that were not actual changes to the document or project has been resolved. For instance,
  changing the size of the document editor would flag the document itself as changed. PR #554.

**Documentation**

* Updated the install instructions of the documentation and the main readme file, as well as the
  current development status as listed on PyPi. PRs #550 and #551.

----

## Version 1.0 [2021-01-03]

### Release Notes

Based on my own testing and usage, and no serious bugs discovered in quite some time (aside from a
few corner case issues), it appears that novelWriter is stable enough for a 1.0 release. Thanks to
all the new users who keep providing feedback on bugs, cosmetic issues, or suggesting improvements
and new features. I'm glad to hear that others find my application useful, and I will keep making
improvements as I get new suggestions and have new ideas myself. At the same time, I will continue
to keep novelWriter simple and clean and avoid feature-bloat.

This release mainly fixes cosmetic and other minor issues to the user interface and makes a few
minor improvements to some less used features. Aside from this, nothing major has changed since the
last release candidate.

This release concludes over two years of tinkering with this project. The project grew out of
numerous lunch and coffee discussions with my colleague Marian Lückhof at my former job. We were
both looking for a tool for writing novels on Linux that suited our needs. We started assembling a
wish list of features that has become novelWriter. In addition, users on GitHub have continued to
test new features, provide very helpful feedback, and make new suggestions for improvements.
Especially the feedback from @johnblommers has been helpful during much of the initial development
time. Over the last months more users have started posting ideas and feedback. Thanks to all of you
for your contributions.

The 1.0 release is intended as a first release of the core features of novelWriter. That does not
mean that all planned features have been fully implemented. There is a long list of ideas and
suggestions to consider and implement. New ideas and suggestions are welcome. Either as feature
requests in the issue tracker, or if not fully formed, can be discussed on the
[discussions page](https://github.com/vkbo/novelWriter/discussions).

### Detailed Changelog

**Bugfixes**

* Fixed a minor cosmetic issue with the checkbox next to the "Distraction Free Mode" entry in the
  menu where its checkmark wouldn't always correspond to the current state of the mode. PR #532.
* When opening the "Writing Stats" dialog in a new project where there is no session log file yet,
  an error dialog would pop up to complain the file is missing. A missing file is not an error, and
  should just be quietly ignored. PR #535.
* Don't enforce string data type in meta data lines written to the head of documents. Some of the
  entries can potentially be of NoneType, and the enforced type will then cause a crash. PR #539.
* Fixed a couple of faulty checks in the index and outline details panel. The checks were not
  reachable by user actions, but put in place to capture coding errors. PR #549.

**User Interface**

* The placeholder text in the "Build Novel Project" tool was referring to the name of the build
  button by a previous label. It now refers to the label that is on the current button. PR #535.
* Add "Move Item Up" and "Move Item Down" to the project tree context menu. These connect to the
  same function as the same entries in the Tools menu. PR #535.
* Block the Item Editor for the root Trash folder. PR #539.

**Other Changes**

* The special "Orphaned Files" folder has been dropped. Since the document class saves most of the
  document meta data to the header of document files, it is no longer strictly necessary and it
  does complicate the code behind the project tree as the orphaned folder isn't a tracked folder
  and therefore needs a fair bit of customised code to fit into the rest of the tree data model.
  Files found in the project's storage folder that do not exist in the project file will now be
  imported into the main project tree based on a set of fallbacks. All recovered files are prefixed
  with the word "Recovered". Issue #540, PR #543.
* Changed the way novel headers are added to the Outline view in cases where the strict logic of
  header levelled isn't obeyed. Previously. a scene header not under a chapter would be added to a
  previous chapter. That may be a bit confusing. Now, instead, a scene outside a chapter will just
  be bumped up one level. PR #549.

**Documentation**

* Fixed some minor typo or wrong word errors in the contributing guidelines. PR #537 by Curtis
  Gedak @gedakc.
* Fixed minor grammar and typo issues in documentation. PR #544 by Curtis Gedak @gedakc.
* Updated documentation with latest changes and rewritten some sections to make the terminology
  more consistent. PR #548.

**Code Improvements**

* Also enforce the maximum line length in text documents. PR #534.
* Updated various parts of the code where a question message box is opened and redirected the call
  to the main GUI class. This was done mostly for consistency, but the feature was added earlier to
  ensure that core classes do not depend on Qt libraries. PR #535.

----

## Version 1.0 RC 2 [2020-12-13]

### Release Notes

This second release candidate for 1.0 comes with only minor changes and improvements, and a handful
of minor bugfixes.

Among the improvements is the addition of all the possible @-keywords for tags and references to
the "Insert" menu under the sub-menu "Tags and References". The "Help" menu has also received a few
improvements and additional links to useful webpages. This release also adds a "Release" notes tab
to the "About novelWriter" dialog. The release notes are displayed automatically the first time you
launch novelWriter after updating to a new version.

Among the fixes is better support for high resolution screens. A few elements on the GUI did not
scale properly, among them the document editor and viewer header and footer. These were clipped on
high res screens due to an underlying issue with the Qt widget underestimating how much space it
required to accommodate the text. Unfortunately, dragging the novelWriter app between screens of
different scaling factors is not currently supported. However, the GUI should scale properly to the
scaling factor on the screen it is opened on.

The work leading up to this release has mostly been focused on improving the test coverage of the
source code of novelWriter. This helps to ensure that the code does what it is intended to do, and
is able to handle corner cases and unexpected external errors and user actions that may occur.
While writing these tests, a number of minor potential issues have been uncovered and handled. Most
of these are corner cases that may not even be reachable by unexpected user actions.

Hopefully, these changes have resulted in an even more stable version of novelWriter. If no more
issues are discovered, the next release will be the final version 1.0 release.

### Detailed Changelog

**Bugfixes**

* The headers and footers of the document editor and viewer would be clipped on high DPI monitors.
  This was due to the QWidget holding these did not automatically scale in the layout. The proper
  height of these are now calculated and enforced instead of relying on automated scaling.
  Issue #499, PR #502.
* Fixed a few inconsistencies in scaling of toggle switches, the form layouts, and the margins of
  the Item Editor when viewing on a high DPI screen. PR #502.
* Switching syntax theme live would not update all colours in the editor and viewer. This has now
  been fixed. PR #516.
* Using the Tools menu to move items up or down in the project tree, without selecting an item to
  move, would cause a crash. The move actions are now quietly rejected if no item is selected.
  Issue #521, PR #522.

**User Interface**

* Added all the possible keywords for tags and references to the Insert menu. Since the list was
  growing long, the Insert menu entries have been split up into four sub menus according to the
  previous grouping. Issue #501, PR #503.
* A "Release Notes" tab has been added to the "About novelWriter" dialog where the latest release
  notes can be displayed. PR #508.
* Menu entries that will open the "Releases" and "Discussions" pages on the novelWriter GitHub repo
  has been added to the Help menu. PRs #509, #511 and #520.
* The help text of many of the Preferences options have been clarified and rewritten. PR #516.
* Added two greyscale syntax themes. These will match with the greyscale icon themes to produce a
  GUI without colours. PR #516.

**Other Changes**

* The Windows installer now properly sets up the mime type for novelWriter, meaning novelWriter
  project files can be opened from the Explorer directly into novelWriter. PR #511.
* It is now possible to create new files in the Outtakes root folder from the context menu.
  Issue #517, PR #519.

**Test Suite**

* The tests for the core classes of novelWriter have been completely rewritten. Every class or
  source file of the core functionality (everything handling the actual project data and documents,
  as well as the meta data) is now covered by its own test module with a 100% coverage for each
  module. PR #512.
* Likewise, the base tests have been rewritten to cover the `Config` class, the `main` function
  that launches the app, and the error handling class. The structure matches the core tests from
  #512. PR #514.
* The GUI tests have been reorganised to match the new test structure, and somewhat improved, but
  some parts still need additional coverage. PR #527.

----

## Version 1.0 RC 1 [2020-11-16]

### Release Notes

This is the first release candidate for the upcoming release of novelWriter 1.0.

Since the fifth beta release about four weeks ago, not much has been changed in novelWriter. A few
minor tweaks have been made to the GUI.

A number of features and tools are now automatically switched off when there is no project or
document open for those features to act upon. Previously, this was a bit inconsistent, although no
serious bugs have been reported or encountered.

Most of the minor changes in this release should not be noticeable to most users. However, there
are a couple of noticeable changes.

**Typewriter Mode**

The "Typewriter Mode" of the editor has been improved. Essentially, this feature is a sort of smart
scroll. It tries to keep the cursor stationary in the vertical direction, and will try to scroll
the document up when the cursor skips to a new line while typing (or down in case of backspaces).
This is similar to the way a typewriter scrolls the paper when hitting the return key. It improves
the writing experience as the current active line will stay at the same eye height level on the
screen.

Previously, the feature would lock the cursor to a given vertical position defined by the user.
Now, instead, the cursor will remain stationary in the vertical direction at any position the user
sets it to by mouse click or keyboard navigation. The user can define a minimum distance from the
top where this feature is activated. These changes makes it more flexible in terms of where the
focus is in the editor. The feature can be controlled from the main Preferences.

**Switching Syntax Theme**

It is now possible to switch syntax highlighting theme without restarting novelWriter. Previously,
changing the theme would only half-way update the document, header and footer background and text
colours. The new settings would not be fully applied until the application was shut down and
started again, thus making it a bit tedious to look through syntax themes to find the one you want.

Switching main GUI theme still requires a restart.

### Detailed Changelog

**Installation**

* A new setup option `setup.py xdg-install` will install the desktop integration (icons, mime and
  launcher) using the OS' `xdg-utils`. This is a more standardised way of installing these
  elements, and replaces the previous `launcher` option. PR #484.

**Bugfixes**

* The Details Panel below the Outline Tree View was not cleared when a project was closed, and
  whatever was listed there was still present if a new project was opened. The panel is now reset
  when a project is closed. Issue #490, PR #491.

**User Interface**

* The Typewriter Mode feature has been improved to keep the cursor stationary at any point in the
  editor viewport as long as the cursor is at a user-defined minimum distance from the top of the
  viewport. The mouse, arrow and page keys do not trigger a reposition. The new behaviour is
  similar to that of the Gutenberg editor in WordPress. PR #482.
* The document editor and viewer are now properly updated when the user switches syntax theme.
  There is no longer a need to restart novelWriter first to apply the changes. PR #487.
* Some minor GUI changes include: don't run the background word counter when there is no document
  open, make the split panels of the Build Novel Project tool non-collapsible, and set the initial
  column widths of tree views to more sensible values. PR #489.
* Block various menu actions, like split and merge documents, project backup, inserts, etc, when
  there is no project open. None of these being active caused any errors as these actions were all
  handled by the various tools, but they shouldn't even trigger when there is no project or
  document to perform the action on. PR #492.
* Clarify the message of the Close Project and Exit novelWriter dialogs. Previously, it may have
  seemed to some users that clicking "No" would allow the closing to proceed without saving
  changes. This is not true as changes are saved automatically when editing a project. The dialog
  text should now make this clearer. Issue #494, PR #495.

**Other Changes**

* The index cache file `meta/tagsIndex.json` now has line breaks and indents. This makes it easier
  to version control if the user really wants to track this file. PR #483.
* The format of the meta data at the top of document files has been changed to be easier to parse,
  and easier to extend with new settings. It is also more human-readable in cases where the user
  opens a document file with other software. PR #486.
* Remove the `ToC.json` file and improve the `ToC.txt` file. There latter now has additional
  information and the format has been improved slightly to be easier to parse if read by an
  external program or script. PR #493.

**Code Improvements**

* There has been some clean-up of comments and docstrings, as well as optimisation and merging of a
  few functions that were implemented in multiple places. PR #485.
* Move some of the constants defined in various other classes into the appropriate constants
  classes, and make all constants upper case variables. PR #489.

----

## Version 1.0 Beta 5 [2020-10-18]

**Important Notes**

* The minimal supported Python version is now 3.6. While novelWriter has worked fine in the post
  with versions as low as 3.4, neither 3.4 nor 3.5 is tested. They have also both reached end of
  life. There are a couple of good reasons to drop support for older versions. PR #470.
  * Python 3.6 introduces ordered dictionaries as the standard.
  * The format string decorator (`f""`) was added in 3.6, and is much less clunky in many parts of
    the code than the full `"".format()` syntax.
  * Especially 3.4 has limited support for `*var` expansion of iterables. These are used several
    places in the code.

**Bugfixes**

* Fixed a bug in the Build Novel Project tool where novelWriter would crash when trying to build
  the preview when running a version of the Qt library lower than 5.14. Issue #471, PR #472.

**User Interface**

* An option has been added in Preferences to hide horizontal or vertical scroll bars on the main
  GUI. These options will hide scroll bars on the Project Tree, Document Editor, Document Viewer,
  Outline Tab and on the controls of the Build Novel Project tool. Scroll bars take up space, and
  as long as the project doesn't contain very long documents, scrolling with the mouse wheel is
  enough. The feature is of course entirely optional. PRs #468 and #469.
* It is no possible to enable scrolling past the end of the document with a new option in
  Preferences. Previously, the editor would just allow scrolling to the bottom of the document. The
  new option adds a margin to the bottom of the document itself that allows for scrolling past this
  point. This avoids having to type text at the bottom of the editor window. PRs #468 and #469.
* A new feature called "Typewriter Scrolling" has been added. It basically means that the editor
  window will try to keep the cursor at a given vertical position and instead scroll the document
  when the cursor moves to a new line, either by arrow keys or while typing. The position can also
  be defined in Preferences. The scroll bar uses an animation effect to perform the scrolling to
  avoid abrupt jumps in the editor window. PRs #468 and #474.
* The line counter in the Document Editor footer now shows the location in the document in terms of
  percentage. This is convenient for very large documents. PR #474.
* A "Follow Tag" option has been added to the Document Editor context menu. This option appears
  when right-clicking a tag value on a meta data line. PR #474.
* When applying a format from the format menu to a selection of multiple paragraphs (or lines),
  only the first paragraph (or line) receives the formatting. The editor doesn't allow markdown
  formatting to span multiple lines. Issue #451, PR #475.
* The syntax highlighter no longer uses the same colour to highlight strike through text as for
  emphasised text. The colour is intended to stand out, which makes little sense for such text.
  Instead, the highlighter uses the same colour as for comments. PR #476.

**Other Changes**

* Since support for Python < 3.6 has been dropped, it is now possible to use `f""` formatted
  strings in many more places in the source code where this is convenient. This has been
  implemented many places, but the code is still a mix of all three styles of formatting text. PR
  #478.
* Extensive changes have been made to the build and distribute tools. The `install.py` file has
  been dropped, and the features in it merged into a new file named `make.py`. The make file can
  now also build a setup installer for Windows. The `setup.py` file has been rewritten to a more
  standardised source layout, and all the setup configuration moved to the `setup.cfg` file. PRs
  #479 and #480.

----

## Version 1.0 Beta 4 [2020-10-11]

**Bugfixes**

* When the Trash folder didn't exist because nothing had been deleted yet, the lookup function for
  the Trash folder's handle returned `None`. That meant that any item with a parent handle `None`
  would be treated as a Trash folder in many parts of the code before the Trash folder was first
  used. This caused a few decision branches to make non-critical mistakes. In particular the
  project tree context menu. This issue has now been fixed with a new check function that takes
  this into account. PRs #452 and #453.
* If an older project was opened, one with a different project file layout than the more recent
  versions, a dialog asked whether the user wants the project updated or not. However, the function
  that moves files to their new location would actually start working before the dialog asked for
  permission. The permission would only be applied to the project XML file. Now, the check is still
  run before the dialog, but the action of moving files around are postponed to after the
  permission has been given and the project XML file parsed. PR #453.
* If there were multiple headings in a file, and the last paragraph did not end in a line break,
  the word counter for the individual sections would miss the last paragraph of the last section
  due to an indexing error. This has now been fixed. PR #453.
* The last cursor position of a document in the editor would only be saved if the document had been
  altered. It is now also saved in the cases where the user makes no changes. PR #460.
* When using an aspell dictionary for spell checking, words containing a hyphen would be
  highlighted as misspelled. This is not the case for hunspell dictionaries. The hyphen is now
  taken into account when splitting sentences into words for spell check highlighting. PR #462.
* Some of the file dialogs would fail with a non-critical error when the cancel button was clicked.
  The cancel is now captured consistently in all instances where such a dialog is used, and the
  calling function exited properly. PR #463.

**User Interface**

* Some minor changes to the text formatting on the Recent Projects dialog. PR #452.
* The Build Novel Project tool has been improved. The settings side panel is now scrollable, and
  the document and settings panel now have a movable splitter between them. This gives more
  flexibility to the sizes of the various parts. PR #459.
* A new option to replace tabs with spaces has been added to the Build Novel Project tool.
  Previously, they were always replaces for HTML output. However, converting them to the HTML code
  for a tab is actually convenient for later import into for instance Libre Office, which then
  converts them back to regular tabs. Issue #458, PR #459.
* Non-breaking spaces have been removed from the HTML conversion of keywords and tags. Issue #458,
  PR #459.
* An upper limit of how large a document the Build Novel Project tool can view has been set. It is
  10 megabytes of generated HTML. The tool will still build larger documents, but they aren't
  displayed. This also limits which options are available in the "Save As" list for such large
  documents. Only native novelWriter exports are supported in such cases. The limit is an order of
  magnitude larger than a typical long novel. PR #460.
* The language indicator in the status bar now has a tooltip stating what tool and spell check
  dictionary provider is being used. PR #462.
* All representations of integers, mostly word counts, are now presented in the same way. They
  should all use a thousand separator representation defined by the local language settings. PR
  #464.
* Many parts of the GUI have had a spin/wait cursor added for processes that may take a while and
  will block the GUI in the meantime. PRs #460, #463 and #464.
* A line counter has been added to the footer of the document editor next to the word counter. It
  makes it easier to compare the position in the document when also accessing it in an external
  editor. PR #466.

**Improvements for macOS**

* The native macOS menu bar now pulls the correct menu entries into the first menu column. PR #463.
* The application name in the main menu would state Python instead of novelWriter. As long as the
  `pyobjc` package is installed, the label will now correctly state novelWriter. PR #463.
* Install and run instructions for macOS have been added to the main README. PR #463.

**Editor Performance**

* The syntax highlighter now remembers what type of line every line in the document is. This means
  that certain types of lines can be re-highlighted without having to process the entire document
  again. This is particularly useful for refreshing the highlighting of keywords and tags after the
  index has been rebuilt. PR #460.
* On a few occasions, the entire document in the editor would be reloaded in order to update the
  layout and formatting. This is not only slow for big documents, it also resets the undo stack.
  Instead, the entire document is "marked as dirty" to force the Qt library to update the layout,
  which is much faster. PR #460.
* For very large documents (in the megabyte range), the repositioning of the cursor when the
  document was opened would sometimes interfere with the rendering of the document itself. This
  could potentially cause the editor to hang for up to a couple of minutes. Instead, the
  repositioning of the cursor is now postponed until the document layout size has reached past the
  character where the cursor is to be moved. This mode is only used for documents larger than 50
  kilobytes. PR #460.
* The document editor will no longer accept single documents larger than 5 megabytes. This
  restriction has also been applied to the Build Novel Project tool. For reference, a typical long
  novel is less than 1 megabyte in size. PR #460.

**Other Changes**

* The command line switches `--quiet` and `--logfile=` have been removed. They were intended for
  testing, but have never been used. The default mode of only printing warnings and errors is quiet
  enough, and logging to file shouldn't be necessary for a GUI application. PR #453.
* A number of if-statements and conditions in the code that were intended to alter behaviour when
  running tests, mostly to stop modal dialogs from blocking the main thread, have been removed.
  These types of changes to the program flow when running tests have now been reduced to a minimum,
  and modifications instead handled with pytest monkeypatches. PR #453.
* The `QtSvg` package is no longer in use by novelWriter. The internal dependency check has been
  removed. PR #457.
* It is no longer possible to set the user's home folder as the root directory of a project. The
  home folder is the default lookup folder in many cases, so it's easy to do by mistake. PR #457.
* The background word counter has been rewritten to run on an application wide thread pool. This is
  a more appropriate way of running background tasks. PR #462.

**Test Suite**

* Major additions to the test suite, taking the test coverage to 91%. PR #453.
* Test coverage for Linux (Ubuntu) for Python versions 3.6, 3.7, and 3.8 are now separate jobs. In
  addition, Windows with Python 3.8 and macOS with Python 3.8 is also tested. All OSes are piped
  into test coverage, and they all have status badges. PRs #453 and #454.

----

## Version 1.0 Beta 3 [2020-09-20]

**Bugfixes**

* After recent changes, the `Edit Project Item` entry (or shortcut `F2`) in the menu would cause an
  error. Other means of triggering the edit dialog for a selected item were working fine. The error
  was caused by a dummy variable being sent by the menu QAction element that was caught by a new
  optional variable in the dialog function. All other menu actions have been wrapped in lambda
  functions to prevent this from happening again. PR #448.
* The Merge Tool was permitting a merge on an empty list of files to be merged. This would result
  in a new, empty file. The Merge Tool will now stop if the list of files is empty. PR #448.
* The orphaned file handling function would cause an error if the orphaned file was empty. This
  would trigger a secondary issue with uninitialised variables, which has also been fixed. PR #448.
* The context menu on the Project Tree would not show the `New File` and `New Folder` options on
  root folders if there were no Trash folder present. This weird bug was caused by the filter
  getting a `None` Trash handle and therefore assuming all root folders were Trash folders as they
  too have parent handle `None`. PR #452.

**User Interface**

* The Last Opened column in the Open Project dialog now has a fixed width font, and the Words
  column has a thin space between number and multiplier unit to make it easier to read. PR #452.

**Code Improvements**

* Minor improvements have been made to the core project classes to improve encapsulation and
  better ensure consistency between the different data structures that store the novel project in
  memory. PR #447.
* Some unused or redundant code has been removed, and in some places, functions have been merged to
  reduce code repetition. PR #449.

**Test Suite**

* A lot more tests have been added and test coverage improved. PR #449.

----

## Version 1.0 Beta 2 [2020-09-13]

**Bugfixes**

* If the horizontal scroll bar appeared at the bottom of the document editor or viewer, for
  instance if a long, un-wrappable line was entered, the scroll bar would sit on top of the
  document footer. The footer bar now properly moves out of the way when the horizontal scroll bar
  appears. Issue #433, PR #434.

**New Features**

* It is now possible to set a different spell check language for a project than the one set in the
  main Preferences. It is only possible to select a different language, not a different spell check
  tool. The setting is managed in the first tab of the Project Settings dialog. Issue #368,
  PR #437.
* The document editor now has the Cut/Copy/Paste options in the main context menu. In addition,
  Select All, Select Word, and Select Paragraph have been added to the menu. The latter two will
  select the word or paragraph under the mouse pointer, not the cursor as the main menu entries do.
  Issue #438, PR #439.
* The document viewer has a new custom context menu with Copy, Select All, Select Word and Select
  Paragraph with identical functionality and look to the context menu entries in the document
  editor. PR #439.
* The document view panel now has a back navigation and forward navigation history of 20 documents.
  The navigation is activated by two buttons in the header, menu entries and keyboard shortcuts in
  the `View` menu, and by navigation buttons on the mouse. Issue #441, PR #442.
* Clicking on a document in the project tree with the middle mouse button will now open the
  document in the document viewer. PR #443.
* Added an edit and a search button to the top left corner of the document editor, in the header.
  The edit button opens the edit item dialog for the open document, and the search button toggles
  the search box for the document. PR #445.
* Added show/hide comment and synopsis buttons to the bottom right corner of the document viewer,
  in the footer. These toggle on and off the rendering of these elements in the viewed document.
  The corresponding settings in Preferences have been removed. PR #445.

**Feature Improvements**

* The document split tool now asks for permission before generating the documents. This adds a
  final confirmation before generating a lot of new documents that it can be tedious to clean up if
  the action was activated by mistake. PR #436.
* Both split and merge tools now preserve the document status or importance value from the source
  item. Previously, it would be reset to the default value. PR #436.

**Test Suite**

* Improved test coverage. PR #446.

----

## Version 1.0 Beta 1 [2020-08-30]

**Bugfixes**

* Not technically a bug, but the clearing of the document editor footer bar, both during start-up
  and when a document was closed, would print two ERROR messages to the terminal window. These were
  benign, but are now prevented from occurring by a slight change in the logic. Issue #418,
  PR #420.
* Fixed spell check highlighting for words separated by a forward slash, which was treated as a
  single word. Issue #427, PR #428.

**New Features**

* A new root folder has been added. It is named "Outtakes" by default, and functions as an archive
  folder for any file that the user wants to take out of the main project tree. The file retains
  its meta data, is editable, and is always excluded from builds. It is not possible to create
  files in this folder, but you can create subfolders for organising them. PRs #415, #416 and #419.
* Support an alternative apostrophe. There is a unicode character defined for this, but the regular
  right hand single quote symbol is the recommended character. However, sometimes this confuses the
  syntax highlighter. The alternative character bypasses this, and may also be useful for languages
  that don't use the same type of symbol for these. PRs #429 and #430.

**Feature Improvements**

* The way the enter and tab keys work in the document editor have been improved. If the search or
  replace text box has focus, the tab key switches between them, and the enter key always triggers
  the button that is to the right of the box with focus. If the editor has focus, the tab and enter
  keys work as expected for a text editor. PRs #412 and #413.
* The keyboard sequence `Ctrl+Shift+Z` is now again an alternative to `Ctrl+Y` for the redo
  functionality. PR #413.
* It is now possible to drag and drop files into the Trash folder. PR #415.
* Files moved to Outtakes or Trash are now cleared from the index, except their word counts. All
  tags and references are thus out of the project. They are automatically put back in when the file
  is dragged into the main project tree again. PR #416.
* Tabs and tab stops are now rendered properly in the document viewer. Since the `setHtml` function
  of the Qt widget used here strips tabs, they were previously just converted to eight spaces. This
  prevented the tabs from aligning vertically like they do in the editor. The stripping of tabs is
  now bypassed by replacing them with a placeholder text, and reverting the replacement after the
  document content has been set. This change also applies to the preview in the Build Novel Project
  tool, and therefore also the print and print to PDF functions. PR #419.
* The syntax highlighter is now better at detecting what is a single quoted string and what is an
  apostrophe in a word. PR #430.

**Other Changes**

* A hard maximum project tree folder depth of 30 has been added. Level 28 is the last level where a
  folder can be created, to allow for one more level of files. There is no particular reason for
  the number 30, it was mostly a matter of picking a number. 30 is assumed to be excessive. It is
  hard to navigate a project tree with that many folders. The value was set because many places in
  the code there was a soft limit of 200. If you created more, various parts of the code would stop
  working. PRs #416 and #421.
* The dialog for reporting unhandled errors has been changed and a new custom Qt subclass written.
  It does essentially the same thing as the standard QErrorMessage box did, but adds the feature of
  a clickable link to the issues tracker on GitHub, and a monospace formatted traceback for the
  issues ticket. In addition, a crash that pops this dialog will now trigger an attempted
  controlled shutdown of novelWriter. Before, it would try to keep running, but often leave
  novelWriter in a half defunct state. PR #417.

**Test Suite**

* Added better test coverage of the Project Load dialog and the Project Outline tool. PR #423.
* Switched from Travis-CI to GitHub actions for running Python tests. PRs #424, #425 and #426.
* All tests can now be run independently of other tests on a function level. Before, this was only
  possible on a test file level. Issue #431, PR #432.

----

## Version 0.12.1 [2020-08-16]

**Bugfixes**

* Some of the insert menu functions were broken due to a left-over comma in the insert source code
  converting the insert text from a string to a tuple. This is a quirk of the Python language and
  unfortunately not caught as a syntax error. Issue #409, PR #410.

**Feature Improvements**

* The Select Paragraph feature in the Edit menu now selects only the paragraph itself, without the
  leading line break. This was previously handled entirely by the Qt library, which does this for
  some reason. Issue #395, PR #405.
* A chapter heading in a file with a different layout than `Unnumbered` can now also be flagged as
  an unnumbered chapter heading by adding an asterisk to the beginning of the title text. This
  only affects the number assignment and counter when running the Build Novel Project tool. The
  rest of the app ignores the asterisk. Issue #402, PR #406.

----

## Version 0.12 [2020-08-15]

**User Interface**

* Added a New Project Wizard that can, in addition to create the previous minimal new project, also
  create a project with pre-defined root folders and chapter and scenes. It is also possible to
  create a copy of the example project from the source code. Either from the `sample` folder in the
  source, or from a `sample.zip` file generated by the `setup.py` script and saved to the
  `nw/assets` folder. PR #366.
* When the user clicked cancel on the colour dialog in Project Settings, the icon would be reset to
  black. Instead, the colour should remain unchanged. A check that the user actually selected a
  colour has now been added. Issue #395, PR #403.

**Other Changes**

* Cleaned up code using `flake8` tool and added it as a permanent check on pull requests. The tool
  filtered out a number of unused variables and imports, which wastes CPU time and memory. Every
  bit helps. PRs #394, #397 and #401.
* Added contributing guide, code of conduct and issue templates. Direct push to main, and PR #398.

----

## Version 0.11.1 [2020-08-09]

**Bugfixes**

* The modality of the dialogs have been made more consistent and a few issues with conflicting
  settings resolved. Mostly the latter relates to some dialogs both having the `exec_()` call and
  the `show()` call. The former implies modal, the latter does not, and the latter usually took
  precedence. All dialogs are now modal with the exception of the Writing Statistics and Build
  Novel Project tools. PR #389.

**User Interface**

* The Help menu entries for the documentation have been improved a bit. If the local copy of the
  documentations is present (both files are checked now), and the Qt Assistant is installed, the
  "Documentation (Local)" entry is visible with `F1` as keyboard shortcut. The "Documentation
  (Online)" is always visible with `Shift+F1` keyboard shortcut. The `F1` key redirects to this too
  if the local copy isn't available. PR #386.
* The Writing Statistics tool now has the ability to set a cap between 100 and 100 000 words on the
  word count histogram bars. This is useful if the user has added a large chunk of text, in which
  case the histogram bar is dominated by this one entry. Now, anything on and above the cap value
  will have a full bar, and all other entries scale from 0 to the cap value. PR #387.

**Documentation**

* The main index page of the documentation now has a build date on it. PR #390.

**Other Changes**

* The Travis CI build system has been altered to first check that the tests pass for Python 3.8,
  for then to move to the other supported Python versions. These are currently 3.6 and 3.7. Python
  3.9 will be added when it is released in October. PR #388.
* Some clean-up of the source code, mostly in terms of unused imports and missing docstrings.
  PR #391.

----

## Version 0.11 [2020-08-08]

Note: The source code has now switched to a default branch named `main` ahead of the changes
planned by GitHub. See their [notes](https://github.com/github/renaming) for more information.

**Bugfixes**

* The `pytest` config file now sets the local source path as the first search path for the main
  novelWriter package. This ensures that the tests can always find the correct version of the code
  when running tests. PR #381.
* The `install.py` script was expecting an older file layout for assets files. This has now been
  updated to the curren file layout. PR #380.

**User Interface**

* A set of new exception handling functions have been added. Recoverable errors will now pop an
  error dialog with the error message and a traceback for the user. The application will not
  generally exit on such errors, unless it causes Python itself to abort. It is possible to copy
  and paste the error message so it can be used for a ticket in the issue tracker. PRs #376 and
  #378.

**Documentation**

* The full documentation for novelWriter, available at
  [novelwriter.readthedocs.io](https://novelwriter.readthedocs.io/) has been rewritten. It was
  drifting out of sync with the development of the code. In addition, many improvements have been
  made to the reStructuredText formatting of the documentation source by providing better
  cross-reference linking and highlighting. The main repository README file has been updated to
  match. PRs #375, #382, and #384.
* The main `setup.py` script has been updated to also build documentation for the Qt Assistant when
  given a `qthelp` flag. The compiled help files are copied into the `nw/assets/help` folder, and
  bundled with the source when pushed to PyPi. The GUI has been altered to open the local help
  files instead of redirecting to the online documentation if the local files are both present and
  the Qt Assistant is installed. PR #375 and #379.

**Other Changes**

* Some minor changes to the source code has been made to more correctly use the Python
  `__package__` variable. PR #376.

----

## Version 0.10.2 [2020-07-29]

**Bugfixes**

* Fixed a crash when using the replace part of search/replace when using regular expressions for
  the search. The replace code assumed the search field was a string, which isn't the case when
  using RegEx, rather itb is a QRegularExpression or QRegExp object. This has now been resolved. In
  addition, the replace feature has been improved to make sure that it only replaces text selected
  by an actual search, not any user selected text. Issue #371, PRs #372 and #373.
* The Tokenizer class used for converting novelWriter markdown to other formats produced some
  invalid escape sequence warnings. The warnings did not seem to affect the results, but have
  nevertheless been fixed. PR #370.

**Features**

* Insert menu entries to insert single and double open and close quote symbols have been added.
  These are the symbols selected as the quote symbols in Preferences. They also have keyboard
  shortcuts associated with them. PR #367.

----

## Version 0.10.1 [2020-07-11]

**Bugfixes**

* Any error encountered when converting a project from the old project folder structure to the new
  were not properly propagated to the origin of the call. Any errors of warnings occurring in the
  process would previously not have been reported properly. These are no reported in a pop-up
  dialog. PR #359.

**User Interface**

* The tooltip of the search/replace Regular Expression option has been updated to state the feature
  only works for Qt 5.3 or higher. PR #359.
* The menus have been restructured a bit. The search options have been moved to a new Search menu.
  The menu order has been changed to a more standard order. The Build Novel Project tool moved to
  the Tools menu. The full screen distraction free mode is now named Focus Mode everywhere in the
  GUI, source code and settings files. Previously, different names were used in different places.
  PR #361.
* Tooltips have been added to main GUI buttons without a button text. PRs #361 and #363.

**Features**

* The search/replace Regular Expression option now uses the newest QRegularExpression tool instead
  of the older QRegExp tool if the Qt version is 5.13 or above. Otherwise, it still uses the old.
  The main benefit of the newer tool in this context is better Unicode support. PR #360.
* The Build Novel Project tool can now generate Roman numbers for chapter markers. Both upper and
  lower case is supported. PRs #362 and #363.

**Other Changes**

* The install scripts now try to create folders before copying icons. PR #364.
* The manifest file now lists the root assets folder, so that it is included in the PyPi build.
  PR #364.
* The .desktop template file has the correct categories set according to the FreeDesktop standard.
  PR #364.

----

## Version 0.10 [2020-06-30]

**Note:** If the project file is opened by this version of novelWriter, the project file can no
longer be read by an earlier version due to the change of how autoReplace settings are stored.

**User Interface**

* The Session Log dialog, now named Writing Statistics, has been redesigned and now has a few more
  filter options. This update also fixes the filtered time count properly. The dialog now shows a
  histogram of words added in a given session, or optionally, on a given date. The filtered log
  data can also be saved as a JSON or CSV file, the latter suitable for importing to a spread
  sheet. The new dialog tool required a new session log file format, so the new session log has
  been given a new file name. The old log file will be left untouched in the project's `meta`
  folder. For projects created prior to this change, the log will record a word count offset that
  will be subtracted from the first entry such that the first word diff will always be 1 instead of
  the total word count of the entire project. Such a large word diff would otherwise saturate the
  histogram. PRs #339 and #349.
* The document editor panel has received a footer bar like the one recently added to the document
  view panel. The footer bar currently shows the status level of the document, and the document
  word count. In addition, the word counter shows the change in count for the current session in
  the same way project word count and change is shown in the status bar. The document word count
  has been removed from the main window status bar. PR #348.
* The document editor footer can optionally be hidden in Distraction Free mode. PR #351.
* The Italic and Bold menu entries have been renamed to Emphasis and Strong Emphasis, which is more
  in line with what they represent in Markdown and HTML. They are still rendered as Italic and
  Bold in the document viewer, but the HTML export is using the `<em>` and `<strong>` tags.
  PR #350.
* Due to several issues with the formatting of emphasised text using `*`, `**`, and `***` wrappers,
  especially when using nested emphasis, the syntax for emphasis (italic) and strong (bold) has
  been reverted to use `_` and `**` wrapping, respectively. This removes the ambiguity, and
  resolves the corner cases. It was possible to resolve the issues by using a custom written parser
  that takes care of all valid combinations, but such a parser would be a bit too slow for use in
  syntax highlighting. I decided therefore to stick with RegEx parsing, and keeping those RegExes
  as short and fast as possible while enforcing the basic formatting rules. Separating the notation
  for emphasis and strong is commonly recommended when writing Markdown anyway, so it is a sensible
  compromise between speed and flexibility. This PR partially reverses PR #310. Issue #353,
  PR #355.
* The syntax highlighter now properly highlights overlapping formatting, including emphasised text
  inside of highlighted quotes. PR #355.
* The colour highlighting of emphasis, strong and strike through, can now be switch off in
  Preferences. The syntax highlighter will still apply the italic, bold and strike effects.
  PR #357.
* The project path in the Details tab of Project Settings can now be selected and copied to
  clipboard. Issue #354, PR #356.

**Other Changes**

* The way the auto-replace settings are stored in the project XML file has been changed in order to
  be more consistent with other features, and to avoid a potential pitfall in defining the tag name
  from a user-entered string. The project class retains its ability to read the old format of the
  file, and will save in the new format. The file format of the project XML file has been bumped to
  1.2. PRs #344, #346 and #347.

----

## Version 0.9.2 [2020-06-26]

**Bugfixes**

* The project tree word counts were getting mixed up when a file was moved to the trash folder, or
  permanently deleted. This has now been fixed, and moving a file should give a zero net change of
  project word count. Permanently deleting it will result in a negative net change. Issue #333,
  PR #335.

**User Interface**

* There is a feature in the project tree class that ensures that the tree item being acted on is
  visible in the tree. It is called when you for instance click the header of an open document. It
  was also activated when opening a document from the tree view with either double-click by mouse,
  or by using the Enter key. This meant that the tree view would often move, which made it hard to
  mouse click on items after each other since you ended up chasing a moving target. This feature is
  now disabled for document open. In addition, the scroll into view feature has been added to the
  search/replace call to move into the next document when reaching the end of the current document.
  This was requested in Issue #332. PR #334.
* The Build Novel Project tool will now display the build time of the document in the preview
  window in order for the user to know if it is potentially out of date. The timestamp is given, as
  well as a fuzzy time string, indicating the age of the content. Issue #331, PRs #336 and #337.

**Documentation**

* The documentation has been updated to clarify the correct formatting for italic, bold and
  strike through formatting tags. Issue #220, PR #338.

----

## Version 0.9.1 [2020-06-21]

**Bugfixes**

* Fixed a serious bug in the replace part of the search/replace function that caused novelWriter to
  crash when the replace text function was called. Issue #327, PR #328.

----

## Version 0.9 [2020-06-21]

**Core Functionality**

* Underline text formatting has been removed. It is not standard HTML5, nor Markdown, and was
  previously implemented using the double underscore notation that in standard Markdown is
  rendered as bold text. Instead, novelWriter now renders a single `*` or `_` wrapping a piece of
  text _within_ a paragraphs as italicised text, and a double `**` or `__` as bold text. The
  keyboard shortcuts and automatic features _only_ support the `*` notation. A triple set of `***`
  are treated as both bold and italicised. PR #310.
* Strike through formatting has been added back into novelWriter using the standard Markdown `~~`
  wrapping. PR #310.
* Added support for thin spaces and non-breaking thin spaces. PR #319.
* The `Ctrl+Z` key sequence (undo) would not go through the wrapper function for document action
  for the document editor, but act directly on the document. This caused some of the logic
  preventing conflict between auto-replace and undo to be bypassed. This has now been resolved by
  blocking the keypress itself and let the menu action handle the key sequence. Issue #320,
  PR #321.
* The dialog window size and column width setting for the auto-replace feature in Project Settings
  are now preserved between closing and opening the dialog. Issue #322, PR #324.

**User Interface**

* The Open Project dialog will now ask before removing an entry from the recent projects list.
  PR #309.
* The text emphasis functions, either selected from the menu or via keyboard shortcuts, will now
  try to respond to the command in a more meaningful way. That is, the text editor will try to
  toggle the bold or italics features independently of each other on the selected text. A menu entry
  to apply both at the same time has also been added. PR #310.
* The document editor search tool has been completely rewritten. It now appears as a search box at
  the top of the document, and has a number of toggle switches added to it. You can modify the
  search tool to be case sensitive, select only whole words, use regular expression search strings,
  loop when reaching the end, and continue the search in the next file in the project tree. For the
  replace feature, you can also select to have the feature try to preserve the case of the replaced
  word. Issues #84 and #305, PR #314.
* A dialog has been added for selecting quotation mark style. These are now used in the Preferences
  dialog instead of a plain text edit box. PR #317.
* Added an insert menu for inserting special symbols like dashes, ellipsis, thin and non-breaking
  spaces, and hard line breaks. PR #319.
* A menu option to replace straight single and double quotes in a selected piece of text has been
  added. This uses the same logic as the auto-replace feature. Issue #312, PR #321.
* When pressing `Ctrl+R` while the document editor has focus, the edited document will be viewed or
  refreshed in the document viewer. Previously, the selected document in the project tree had
  priority. The document is also now saved before loaded in the viewer, ensuring that it shows the
  very latest changes. Issue #143, PR #323.
* The selection in the project tree should not scroll into view when just opening the document.
  This can be quite annoying if loading several documents in sequence by double-clicking as the
  target may move just when you're about to click. PR #325.

**Other Changes**

* Added the file's class and layout to the meta data string of saved document files. This meta data
  is only used to restore the file meta information into the project if it was lost from the
  project file. It is also useful information when reading the file in external tools. PR #308.

----

## Version 0.8 [2020-06-14]

**Bugfixes**

* The HTML converter, used for the document view window as well as the Build Novel Project tool,
  would crash novelWriter if a file included an `@tag:` entry with no actual tag name following it.
  In addition to fixing this issue, the call to the converter is now also wrapped in a `try/except`
  construct to prevent crashes caused by potential edge cases in document content. If the rendering
  fails, the view window will show an error message instead of the intended document. Issue #298,
  PR #299.
* Clipping of the descended part of fonts in the document title bar has been fixed. Issue #295,
  PR #300.
* When clicking a tag in the editor while the viewer was closed, nothing would happen. Now, the
  viewer is first opened before navigating to the source of the reference tag. Issue #294, PR #306.
* The missing optional rendering of synopsis comments in the document view panel has been added.
  Mentioned in Issue #301, PR #311.

**User Interface**

* A details panel below the Outline tree view has been added. The panel shows all the information
  of a selected row in the tree view above, including hidden columns, and some additional
  information. The tags and references also become clickable links that when clicked will open in
  the document viewer. PR #281.
* Icons have been added to the Title and Document columns in the Outline. The titles get a new icon
  indicating the header level, while the documents get the already existing document icon. PR #302.
* Added a context menu to the project tree for easier access to some of the most use actions on the
  tree. PR #282.
* Improved the support for High DPI screens. Margins and box sizes that were hardcoded should now
  scale. User settings should also scale back and forth when switching between scale factors. Issue
  #280, PR #285.
* The total edit time of a project is now displayed on the Details tab of the Project Settings
  dialog. PR #290.
* The title bar in the document editor now has a full screen button and a close button, and in the
  document viewer a reload button and a close button. The full screen button toggles the
  distraction free mode, and the reload button regenerates the document being viewed to update any
  changes that may have been made to it. PRs #293, #300, #303 and #306.
* The References panel below the document viewer has been redesigned. It now sits in a resizeable
  panel below the document, and its controls sit in a footer bar in the document itself. The
  functionality of the feature is otherwise unchanged, but the buttons have received new icons.
  PRs #304 and #306.
* The option to render comments and synopsis in the document view panel has been added to
  Preferences. The toggle option for comments that was previously in the menu has been removed.
  PR #311.

**Project Structure**

* The way GUI states of switches, column widths, etc., is saved has been improved a bit during the
  High DPI updates. PRs #285 and #286.
* Some settings have been moved around to more appropriate sections in the project XML file. The
  project load function still reads the values from the previous location if opening an older
  project file. PR #288.
* A file opened in the Trash folder is no longer "Read Only". The feature was rather arbitrary, and
  also required a GUI element to notify the user of the fact. Any file can now be edited. PR #292.

**Code Structure**

* The core classes making up the project itself were previously merged into a single source code
  file. This file was getting a bit big, so they have been split up again. PR #289.
* A lot of Inkscape meta data has been removed from the SVG icons, reducing the file sizes quite a
  bit. PR #291.
* Opening and closing of files are now properly handled also when using the ConfigParser tool.
  Previously, files were not properly closed after the content had been read, leaving the handles
  open until the Python garbage collector handled them. PR #300.

----

## Version 0.7.1 [2020-06-06]

**Bugfixes**

* For some fonts (especially Ubuntu) the minimum column width in the tree widgets would be
  estimated to be too large. It especially meant that the "include when exporting" flag had a
  column much wider than it needed to be. This setting is now overridden with the known size of the
  icon, plus a 6 pixel margin. PR #278.
* Correctly fixes issue #273, which was actually due to an old css setting from early development.
  PR #287.

**User Interface**

* The Build Novel Project tool now has an option to not style the text before printing or exporting
  to file. PR #276.
* When opening an item in the project tree, the focus remains on the tree and no longer switches to
  the editor. It makes it easier to flip through files and look at them by pressing enter
  repeatedly. PRs #278 and #287.
* Added a title icon and document icon to the outline view. PR #278.
* The timeline class root folder now has a calendar icon instead of a clock. PR #287.
* Regrouped the options on the Build Novel Project tool a bit. They are now sorted into Titles,
  Format, Text and File categories, with more consistent labelling. PR #278.
* A link colour has been added to the Build Novel Project tool. It's the same colour as the header.
  PR #287.

**Other Changes**

* Reduced the number of files and folders in the source code a bit. PR #277.

----

## Version 0.7 [2020-06-01]

**Bugfixes**

* Fixed a bug where novelWriter might crash if a file is deleted immediately after being created,
  and also additional points-of-failure if the project was new. PR #267.

**User Interface**

* The back-references list in the project view panel now shows references to any tag in the open
  document, not just the first tag. Issue #227, PR #234.
* Clicking a tag now tries to scroll to the header where the tag is set. The index needed a couple
  of minor changes for this feature, so this will invalidate the old index for a project saved with
  an older version, and require a new to be built. This is done automatically. PR #234.
* Moved the Close button on the "Build Novel Project" dialog to the area with the other buttons
  since we anyway increased the size of that area. PR #256.
* Updated the unit for Preferences > Editor > Big document limit from `kb` to `kB`. Issue #258,
  PR #260.
* Added Typicons-based coloured icon set also for light GUI background. PR #265.
* The export check mark that was added to the Flags column in the project tree in Version 0.6 has
  been moved to its own column, and been replaced with a proper icon. The details panel below it
  has been updated as well. PR #268.
* Icon sizes are now calculated based on the size of the text, and all text and icons should scale
  relative to the default GUI font size. PR #268.
* The font family and size of the main GUI font can now be changed in Preferences. For Windows,
  this defaults to Cantarell 11pt, which is now shipped with novelWriter. On other systems it
  defaults to the system font. Special accommodations had be made for Ubuntu where the font size of
  the tree widget was not updated automatically (Issue #273). PRs #269, #270, #274 and #275.
* There are no Monospace fonts on the main GUI any more. Where fixed width is needed, the size is
  calculated beforehand with Qt's font metrics class. PR #271.
* Fonts are now selected via the system's font dialog rather than the font combo box. PR #270.
* Word, character and paragraph counts are now updated on the project tree details panel if the
  file currently being edited is also selected in the tree. PR #272.
* The Build Novel Project dialog now shows the previous generated content when it's opened.
  PR #272.
* The Build Novel Project tool can now export the HTML and NWD output into a JSON data file. This
  file is convenient if the user wants to post-process the output with for instance Python, or one
  of the other numerous languages that can read JSON files. PR #272.

**Project Structure**

* The project folder structure has been simplified and cleaned up. We also now freeze the main
  entry values in the main XML file. The XML file is now given version 1.1, and no further core
  changes to its structure will be made without bumping this version. We're also locking it to only
  be opened by version 0.7 or later. An old project file is converted on first open. PRs #253 and
  #261.
* When a project is closed, two table of contents files are written to the project folder. They are
  named `ToC.txt` and `ToC.json` and are there for the user's convenience if they want to find a
  specific file from the project in the data folders. As discussed in Issue #259, PRs #261 and
  #262.
* The expanded node flag from the project tree was also saved for file entries, which cannot
  actually be expanded. These flags are no longer saved in the XML file. PR #261.

**Other Changes**

* Dropped the usage of `.bak` copies of document files. This was the old method to ensure the
  document data was written successfully, but it uses twice the storage space. Instead, writing via
  a temp file is the current safe way to save files. PR #248.
* The project class now records the accumulated time in seconds a project has been opened. This
  data is not yet displayed anywhere, but it is being tracked in the project XML file. PR #261.

**Test Suite**

* Added tests for Build Novel Project, Merge Folder and Split Document tools. PRs #263 and #264.

----

## Version 0.6.3 [2020-05-28]

**Bugfixes**

* It was possible to have the backup folder set to the same folder as the project, resulting in an
  infinite loop when `make_archive` was building the zip file. This crash of paths is now checked
  for before moving to the archive step. Issue #240, PR #241.
* Fixed an issue with the Build Novel Project tool on Ubuntu 16.04 LTS where the dialog wouldn't
  open. Issue #243, PR #246.

**User Interface**

* Renamed the "Generate Preview" button on the "Build Novel Project" tool to "Build Novel Project".
  You must actually click this to be able to export or print. Issue #237, PR #238.
* Added font family and font size selectors to the "Build Novel Project" tool. You may want a
  different print font than used in the editor itself. Issue #230, PR #238.
* Removed the "Help" feature in "Build Novel Project" and instead added detailed tooltips.
  Issue #250, PR #249.
* Changed the title formatting codes for "Build Novel Project" to something less verbose. The old
  codes are translated automatically. Issue #247, PR #249.
* A margin of the viewport (outside the document) has been added to the document editor and viewer
  to make room for the document title bar. Previously, the title bar would sit on top of the
  document's top margin, which would sometimes hide text that would otherwise be visible (when
  scrolling). PR #236.
* Fixed an alignment issue for the status icon on the project tree details panel. Mentioned in
  #235, PR #239.
* Removed the `Xo` icon for NO_LAYOUT in the project tree details panel. Mentioned in #235,
  PR #239.
* Added a "Details" tab to the "Project Settings" dialog, which also lists the project path. Issue
  #242, PR #239.

----

## Version 0.6.2 [2020-05-28]

* Botched release. Replaced with 0.6.3. Crashes when Build Novel Project is opened.

----

## Version 0.6.1 [2020-05-25]

**Bugfixes**

* The Outline view now takes into consideration the exported flag, and does not show excluded files
  in the outline. PR #224.
* Page layout format was ignored when exporting project. The formatting of this layout has now been
  added. PR #224.
* If multiple headings were present in a file, the sorting of headings in the Outline view would
  follow a text sort not a numerical sort of the line numbers. That is, it would be sorted as "1",
  "10", "2", "20", etc. This has been fixed. PR #226.
* The text justification in the preview in the  Build Novel Project was following the main
  Preferences settings, not the Build settings. This did not affect the formatting of the exported
  file itself, but the preview is now made consistent with the build settings. Issue #228, PR #231.

**User Interface**

* Recent projects in the open project dialog can be removed from the list by hitting the delete
  key. PR #225.
* Moved the browse button to after the path box in the open project dialog. PR #225.

**Other Changes**

* The three remaining dependencies now have a minimum version set. PR #224.
* Moved the sample project up one folder level. PR #224.

**Documentation**

* The export page in the documentation erroneously stated that line breaks could be added to titles
  by adding `%\\%`. The correct syntax is `\\`. Issue #229, PR #231.

----

## Version 0.6 [2020-05-24]

**Bugfixes**

* Fixed a bug in validation of `@tag:` meta tags where one or more spaces before the `:` would
  still pass as a valid tag, but the keyword index array would be missing those spaces in its
  counter. This mainly affected the highlighting of keywords, which would be misaligned. PR #206.

**User Interface**

* The Export Tool has been removed and replaced by a new tool called "Build Novel Project". The new
  tool has the same filtering options as the Export Tool, but with more formatting options for
  titles. It also has a preview window to display the generated document. A Save As button provides
  exports to HTML, novelWriter Markdown, plain text, PDF and Open Document format. LaTeX export has
  not been ported over, and interfacing with Pandoc is no longer supported either. Although, as
  before, the HTML export can be converted with Pandoc to other formats outside of novelWriter. The
  new tool also supports printing. PRs #204, #220 and #221.
* The Project Settings, Preferences, Item Editor, Merge Documents, and Split Documents dialogs have
  been redesigned. The ones with tabs now have vertical tabs on the left with horizontal labels.
  The dialog design should be more compact, and have room for more tabs for future settings.
  PR #212.
* A new icon, as well as a mimetype icon for the project files, have been designed and added to the
  app. PRs #213 and #214.
* The About dialog has been completely redesigned to allow more information. PR #217.
* The Open Project dialog has been cleaned up and made more readable. The project paths have been
  moved out of the list, and are now displayed when an item is selected instead. Icons have been
  added, and the New project dialog can also be triggered from this dialog. PR #218.
* The document stats have been added to the details panel below the project tree. PR #219.

----

## Version 0.5.2 [2020-05-21]

**Bugfixes**

* When running on Windows 10, some of the buttons were missing icons. More fallback icons have been
  added to ensure that all current buttons have a fallback path that always ends in an icon.
  PR #211.

**User Interface**

* The statusbar has been redesigned a bit. The block icons showing document and project saved
  status have been replaced by LED icons. The statistics has been moved to a separate label, and
  most of the detailed stats moved to its tooltip. PR #210.
* Default icon theme is now `Typicons Grey Light`. PR #211.
* Clicking on the document header selects the document in the project tree, but this functionality
  has been enhanced to also ensure the document is expanded and visible in the tree. If it's
  scrolled out of view, the tree will scroll it into view. PR #215.
* Syntax highlighting of text in quotes can now be turned off in Preferences. PR #215.

**Core Functionality**

* Checking for version dependencies and a few packages (aside from PyQt5) is now done later in the
  start-up so that it is possible to alert the user with a dialog box instead of terminal error
  messages. PR #210.
* Made a few minor changes to the code so novelWriter can run with Python 3.4.3 and Qt 5.2.1, that
  is, it runs on last version of Ubuntu 14.04. This level of compatibility is not guaranteed to
  remain in the future, but for now, the changes have no impact on functionality. PR #210.

----

## Version 0.5.1 [2020-05-14]

**Bugfixes**

* Fixed a bug where only some of the text would be rendered in the editor window when a large text
  document was loaded. The text is there in the buffer, but the rendering process was interrupted
  by the function that recalculates margins. This recalculation was added with the document tiles
  in 0.5. The re-rendering of the text could be triggered by opening the search bar, indicating
  that it was caused by the shifting of the vertical document frame. PR #208.

**User Interface**

* The icon theme functionality of novelWriter has been reworked. For the default system theme, very
  little has changed. It should still load whatever the system provides, but this doesn't work for
  all icons on Windows 10 for instance. It is now possible to select between three icon themes in
  the Preferences dialog, independent of the GUI theme. Using a theme breaks the dependency on the
  operating system to provide standard icons. Qt provides some, but not all needed by novelWriter.
  PR #207.
* Added a check that warns if the project file was saved with a newer version of novelWriter as
  that may cause meta information to be lost. This warning will remain there until the file format
  is finalised. This is an issue with preserving certain settings, not the project structure
  itself. PR #205

**Debugging**

* Reduced the number of command line switches needed for debug runs. PR #205.

----

## Version 0.5 [2020-05-09]

This release of novelWriter has a number of feature updates, bringing it one step closer to initial
feature completeness for a version 1.0 release.

In the pipeline for 1.0 is a completely new export tool with improved and added options, including
printing. Further improvements are also planned for the new Outline View added in this version.
When these additions are completed, novelWriter will start moving towards a 1.0 release via release
candidates. I'm hoping to wrap up this year and a half long stage of initial development soon so
that I can spend more time using it than creating it.

**Additional thanks** to @countjocular for PRs #173 and #174, and to @johnblommers for all the
helpful feedback and issue reports for the new features added in this, and previous releases.

### Notable Changes

* The Timeline View dialog is now gone. Instead, the main window area has been split into two tabs.
  The first, the "Editor", contains the Document Editor and Viewer panels. The second, the
  "Outline", contains a new Outline View of the novel part of the project, broken down into a tree
  view of all the project headings. All meta data associated with each part of the novel can be
  viewed in further columns, selectable from a drop down menu by right-clicking the header. These
  columns can also be rearranged.
* Both the Editor and Viewer panels now have a header showing the document label as seen in the
  Project Tree. Optionally, the full path of the document can be viewed. Clicking this header will
  select the document in the Project Tree, making it easier to find where the document belongs in
  the structure.
* A project load dialog has been added when novelWriter is launched. It will show you your recently
  opened projects, let you browse for those that aren't listed, or create a new project. More
  features will be added to this dialog later on.
* The Preferences dialog has been completely redesigned to make it easier to find the various
  settings and understand what they do.

### Detailed Changelog

**Features**

* An Outline View panel has been added to the main GUI window. The Outline View can show all meta
  data associated with a novel heading in a column-wise manner. The Timeline View feature has been
  dropped in favour of the new Outline View. PRs #140, #181 and #191.
* A synopsis feature has been added. It allows a comment to be flagged as a synopsis comment to be
  picked up by the indexer and displayed in the GUI. Currently available in the Outline View.
  PRs #140 and #191.
* A document title bar has been added to the top of the editor and viewer. These show the document
  label as seen in the project tree. Optionally, the full document path can be shown. Clicking the
  title will highlight the document in the project tree. PRs #192 and #194.

**User Interface**

* A Project Load dialog has been added, which pops up when novelWriter is launched. It allows for
  opening other recent projects, browse for projects, or start a new project. This replaces the
  former Open and New Project features, as well as the Recent Projects menu entry. PRs #177 and
  #183.
* The command line switches for debugging have been changed a bit. Higher level of debugging now
  includes the lower levels, preventing the need for specifying for instance both debug and verbose
  debug. PR #182.
* The Preference dialog has been completely redesigned. The options are now displayed vertically,
  in four tabs instead of two, and with more informative text explaining what they do. Some
  previously unconnected options have also been added. PR #193.

**Bug Fixes**

* The `install.py` script has been fixed to reflect changes in storage location of the themes.
  PR #174.
* Fixed a bug with launching Preferences without Enchant spell checking installed. PR #190.
* A minor issue with running backups with no backup path set has been fixed. The backups would be
  written into the source folder, or wherever novelWriter was launched from, which is a very messy
  fallback. PR #195.

**Documentation**

* Some outdated links and a number of typos and spelling errors have been corrected. PR #173.
* Documentation has been brought up to date with the current set of features of novelWriter.
  PR #202.

**Project Structure**

* Opening a project now writes a lock file to alert the user if the same project is opened more
  than once. The warning can be ignored if the user wants to proceed. PR #179.
* Two new meta tags have been added to the project file to store a counter for the number of times
  the project has been saved or autosaved. The meta information is not currently displayed in the
  GUI, but could be added to an About Project dialog in the future. The PR also adds checks to
  ensure XML attributes exist before attempting to load them. PR #180.
* A single line of document meta data is now written to the top of document files. They mainly
  serve to identify the file content if one opens the file directly in an external editor, but also
  assist the Orphaned Files tool to identify the files when they are found, but missing from the
  project tree. PRs #200 and #201.

**Code Improvements**

* For the Outline View, the `NWIndex` class has been restructure and extensively rewritten. It is
  more fault tolerant, and will automatically rebuild a corrupt index loaded from cache. PR #140.
* The way that dialog options (which options were selected last time a dialog was open) has been
  rewritten. All data is now stored in a single JSON file in the project meta folder. PR #175.
* Since the config class is instantiated before the GUI, error reporting to the user was tricky. An
  error cache has now been added to allow non-critical errors to be displayed after the GUI is
  built. PR #176.
* All source files now have the minimal GPLv3 license note at the top. PR #188.
* Also added license info to the command line output. PR #189.
* Large chunks of the code has been restructured. Mainly the non-GUI parts, which have mostly been
  merged into a new `core` folder. Several classes which are only used by a single object have been
  merged into the same file, reducing the total number of source files a bit. PR #199.

----

## Version 0.4.5 [2020-02-17]

**Features**

* A project can now be opened from the command line by providing the project path to the launching
  script. PRs #164 and #166.

**User Interface**

* Added functionality to split a document into a folder of multiple documents, and also to merge a
  folder of documents into a single document. PRs #159 and #163.
* It is now possible to permanently delete files from the Trash folder. This can be done
  file-by-file or by using the Empty Trash option in the menu. PRs #159 and #163.
* When running the spell checker, a wait cursor is displayed. This will alert the user that
  novelWriter is working on something when, for instance, a very large document is opened and
  initial spell checking is running. PR #158.

**Bug Fixes**

* Fixed a few keyboard shortcuts that were not working in distraction free mode. PR #157.
* Added a check to ensure the user does not drag and drop an item into the Orphaned Items folder.
  Since this folder is not an actual project item, novelWriter would crash when trying to change
  the dropped item's parent item to the Orphaned Items folder. Now, instead, the drop event is
  cancelled if the target folder is Orphaned Items. PR #163.

**Code Improvements**

* The way project files are saved has been altered slightly. When a project file or document file
  is saved, the data is first streamed to a temp file. Then the old storage file is renamed to
  .bak, and and the temp file is renamed to the correct storage file name. This ensures that the
  storage file is only replaced after a complete and successful write. PR #165.
* The cache folder has been removed. It was used to store the 10 most recent versions of the
  project file. Instead, the previous project file is renamed to .bak, and can be restored if
  opening from the latest project file fails. Any additional restore capabilities should be ensured
  by backup solutions, either the internal simple zip backup, or other third party tools. PR #165.
* The dependency on the Python package `appdirs` has been dropped. It was used only for extracting
  the path to the user's config folder, a feature which is also provided by Qt. PR #169.

----

## Version 0.4.4 [2020-02-17]

* Botched release. Replaced with 0.4.5.

----

## Version 0.4.3 [2019-11-24]

**User Interface**

* Added keyboard shortcuts and menu entries for formatting headers, comments, and removing block
  formats. PR #155.
* Disable re-highlighting of open file when resizing window. This is potentially a slow process if
  the spell checker is on and the file is large. There is no need to do this just for re-flowing
  text, so it is now disabled on resize events. Issue #150, PR #153.
* Improved the speed of the syntax highlighter by about 40% by not using regular expressions for
  highlighting block formats and by skipping empty lines entirely. PR #154.

**Bug Fixes**

* Fixed an issue when closing the import file dialog without selecting a file, the import would
  proceed, but fail on file not found. The import is now cancelled when there is no file selected.
  PR #149.
* Fixed an issue with markdown export where it did not take into account hard line breaks. Issue
  #151, PR #152.
* Fixed a crash when running file status check when the project contains orphaned files. PR #152.

----

## Version 0.4.2 [2019-11-17]

**User Interface**

* Distraction free mode now also hides the menu bar, but all keyboard shortcuts used for editing
  remain active. The rest are disabled. PR #142.

**Bug Fixes**

* Fixed various issues with spell checking highlighting. The highlighting and the editor didn't
  always agree on what words were spelled wrong. PR #141.
* The status bar now shows what spell checking language is actually loaded. Previously, it just
  showed the language selected in the settings. That was a bit misleading as the available
  dictionaries can change due to the change in installed dictionary on the system. PR #145.

----

## Version 0.4.1 [2019-11-10]

**Features**

* If no external spell check package is available, novelWriter can now fall back to use a simple
  spell checker based on word similarity comparison provided by the Python standard package
  `difflib`. That means spell checking is always available, although the difflib-based spell
  checker is both slow and lacks many features of other packages. This feature comes with a general
  English dictionary, and a GB and US dictionary. These are just lists of correct words provided by
  aspell. PR #130.
* Language information (spell checker) is now shown on the status bar. In addition, the timer has
  been converted to monospace font and received an icon. PR #136.
* The new icons exist in both dark and neutral mode, and the mode can be set in the preferences.
  This makes it easier to see the icons on a dark system theme. PR #135.
* Distraction free mode, key shortcut `F8`, and full screen mode, shortcut `F11`, are now
  available. This PR also fixes some issues with rescaling of text margins when windows or panels
  are resized. PR #137.

**User Interface**

* Most text boxes now have a character limit. Before, the only limit was the limit set by Qt itself
  of ~32k characters. PR #126.
* Key combination `Ctrl+G` is now an alternative to `F3`, forward search, and vice versa for
  backwards search. This makes more sense on macOS. Issue #124, PR #126.
* The shortcut for the replace feature is now `Cmd+=` on macOS, and remains `Ctrl+H` on Linux and
  Windows. Issue #124, PR #126.
* The sample project in the source code has been improved to better show the features of
  novelWriter as they currently are. The old text was a bit out of date. The new text also explains
  the features it demonstrates. PR #132.

**Bug Fixes**

* Fixed a bug where a long file label would expand the tree pane due to the details panel
  expanding. The label itself will no longer show more than 100 characters, and is word wrapped.
  Issue #120, PR #122.

**Code Improvements**

* The code has been reorganised, import headers been cleaned up, and the code made more or less
  PEP8 compliant. PRs #118, #119, and #138.
* The dependency on the `pycountry` package has been dropped. The feature based on it now uses an
  internal list of country codes for describing spell checker languages. PR #129.
* The themes manager has been improved, and the loading of icons now supports a number of fallback
  steps to ensure something is shown in most cases. The final fallback is the system's own icon
  theme. PR #135.

----

## Version 0.4 [2019-11-03]

**Features**

* The export dialog now allows limited support for exports using Pandoc. The Pandoc conversion is
  run as a stage two of the export process. Pandoc integration is fickly on Windows, but works well
  on Linux. PRs #82 and #104.
* The editor now supports Markdown standard hard line breaks, and exports these correctly to the
  various file formats and to the document view pane. Hard line breaks can be inserted by either
  appending two or more spaces to the end of a line, or by pressing `Shift+Enter`. PR #83.
* The editor now supports and preserves non-breaking spaces. Unfortunately, the preservation of
  these spaces on save and reload is dependent on Qt 5.9 or later. Non-breaking spaces are
  preserved on export to html and LaTeX. PR #87.
* An option to show tabs/spaces and line endings in the document editor has been added to the
  Preferences dialog. PR #90.
* The document view pane now has a "Referenced By" panel at the bottom, showing links to all
  documents referring back to the document being viewed. The panel is collapsible, and has a sticky
  option that will prevent it from updating if links are followed. PRs #109 and #110.
* The tag and reference system no longer has any restrictions on file class. That is, any file can
  have tags and references, and they are indexed by the indexer and displayed as links in the
  document view pane. The timeline view behaves as before, only listing active Novel files.
  PR #114.
* A new root folder type and keyword for "Entities" has been added. These can be useful for
  describing plot elements fitting under such a category. PR #115.

**User Interface**

* Tags and references in the editor are now "clickable" in the sense that pressing `Ctrl+Enter`
  with the cursor on them will open the reference in the view pane. PR #98.
* Warnings triggered when the user tries to use features with missing package dependencies will now
  provide a link to the package website. PR #86.
* Adding the `~` character in file path boxes is now expanded to the user's home directory. PR #94.
* The recent projects submenu no longer has a number prefix, and a "Clear Recent Projects" option
  has been added. PRs #86 and #94.
* Syntax themes based on Night Owl and Light Owl themes have been added. PR #97.
* Read-only files now have a notification popping up at the top of the edit pane, and the files are
  actually not editable. PR #106.
* Tabs are now properly exported in formats where this makes sense. For plain text files, a tab is
  converted to four spaces. For html exports they are converted to a long space, equivalent to four
  spaces. PR #113.
* A toggle button in the Document menu now allows displaying file comments in the document view
  panel. PR #115.

**Bug Fixes**

* Some issues with unicode conversion and LaTeX export have been addressed, but the escaping of
  unicode characters is prone to errors. The user should be careful with using special symbols if
  export to LaTeX is intended. The package `latexcodec` should be able to handle Latin based,
  language specific characters. PRs #73 and #79.
* Fixed some long-standing issues with running novelWriter on Windows. The config folder requires a
  set of two folders to be created on first use, which the config class did not expect. This is now
  resolved. In addition, Python does not default to utf-8 when writing files on Windows, so all
  open statements now have encoding defined. Failing to open files also had the risk of truncating
  them. This has been avoided by distinguishing new files from broken files. PR #81.
* Dark theme was not rendering properly on multiple platforms. This was resolved by forcing the Qt5
  style to "Fusion", which allows further formatting by the novelWriter themes code. The user can
  override the Qt styling option through the `--style=` flag on the command line. PR #96.
* The behaviour of files in the Trash folder has been fixed. These are now read only. PR #106.
* Fixed a bug where the last line of a title or partition page would be ignored on export. PR #113.
* Drag and drop onto the root level of the tree has been disabled. This was anyway only allowed for
  root folder items, but it was tricky to enforce this properly for other files. In order to move
  root folders around now, the move up and down features need to be used instead. #115.

**Installation**

* A script for `pyinstaller` has been added, making it possible to generate standalone executables
  of novelWriter on at least Windows and Linux. PR #91.
* novelWriter has been made `pip install` ready. PRs #107 and #108.

----

## Version 0.3.2 [2019-10-27]

**Documentation**

* The documentation has been rewritten and added to the Read the Docs website. Pressing `F1` or
  `Help > Documentation` in the menu opens the novelWriter documentation page. PRs #68 and #69.

**User Interface**

* Filters have been added to the Timeline View window so unused tags can be hidden, and it's
  possible to select only certain classes of tags to display. PRs #61 and #62.
* The dialog boxes for Timeline View and Session Log now remember the filter choices from previous
  instance for the same project. PR #62.
* When having a document open in the editor, text can be imported into it from a plain text file.
  No formatting conversion of the imported text is performed. That is up to the user. However, this
  allows for importing novelWriter documents from other projects or from a previous export,
  partially addressing request in issue #63. PR #65.
* The Export feature now includes exporting to LaTeX, which allows building PDFs with pdflatex or
  other tools. PR #73.
* Export of a novelWriter flavour markdown file is also supported. This file can be imported back
  in as-is, and almost completes an export-edit-import cycle. A split document into multiple files
  feature will be added soon. PR #73.

----

## Version 0.3.1 [2019-10-20]

**Bug Fixes**

* The backup request dialog should pop up on any change to the project during the last session, not
  just on unsaved changes. PR #58.
* The regex that searches for words for the spell check highlighter was not including unicode
  characters, so it would underline parts of words using unicode characters even if the word was
  spelled correctly. PR #58.
* When having unsaved changes in an open document, while changing editor configuration options, the
  document would be reloaded from disk when the changes were applied. This meant the unsaved
  changes were lost. The document is now saved before the editor is re-initialised. PR #58.

**User Interface**

* Added a GUI to display the session log. The log has been around for a while, and records when a
  project is opened, when it's closed, and how many words were added or removed during the session.
  This information is now available in a small dialog under `Project > Session Log` in the main
  menu. PR #59.
* The export project feature now also exports the project to Markdown and HTML5 format. PR #57.

----

## Version 0.3 [2019-10-19]

**User Interface**

* Added project export feature with a new GUI dialog and a number of export setting. The export
  feature currently only exports to a plain text file. PR #55.

----

## Version 0.2.3 [2019-10-06]

**User Interface**

* The search feature now also allows for replacing text, so the basic search/replace tools in now
  complete. PRs #51 and #52.
* All icons have been removed from the menu, and the dark theme has received a new set of basic
  icons. They are not very fancy, so will perhaps be replaced by a proper icon set later. PR #53.

----

## Version 0.2.2 [2019-09-29]

**Bug Fixes**

* Fixed a bug where loading a config file with the dictionary language set to `None`, or presumably
  a missing dictionary, would trigger a fatal error. PR #47.

**User Interface**

* Added a basic search function for the currently open document. This is a simple interface to the
  find command that exists in the Qt document editor. It will be extended further in the future.
  PR #49.

----

## Version 0.2.1 [2019-09-14]

**Bug Fixes**

* The _Tomorrow_ theme had the wrong set of colours. PR #39.

**Documentation**

* Added the backup feature to the documentation. PR #40.

**User Interface**

* The auto-replace list in project settings is now sorted alphabetically. PR #43.
* Added version checking of the Qt5 and PyQt5 dependencies. Non-essential functionality that
  depends on very recent versions of Qt5 are now switched off if version is too low. Currently only
  affects the custom tab stop length, which requires version 5.10. Issue #44, PR #45.

**Code Improvements**

* Minor changes to the About novelWriter dialog and to how backup filenames are generated. PR #41.

----

## Version 0.2 [2019-06-27]

**Documentation**

* Added documentation in English. The help file opens in the document view pane when the user
  presses `F1` or selects it from the Help menu. PR #27.

**Themes**

* Complete rewrite of how syntax highlighting and GUI themes are handled. These are now set
  separately, and the dark theme uses QPalette to handle the dark colours, which makes the dark
  theme a lot more portable between operating systems. #34 and #35.
* Added the five "Tomorrow" colour themes to list of syntax highlighter themes. PRs #34 and #35.

**User Interface**

* Added a preferences dialog for the program settings. It is no longer necessary to edit the config
  file. PR #30.
* The document viewer remembers scroll bar position when pressing `Ctrl+R` on a document already
  being viewed. PR #28.
* Removed version number from windows title. PR #28.
* The auto-replace items in Project Settings are now editable. PR #29.
* Changed how document margins are handled. This implementation works better and drops the
  difference between horizontal and vertical margins in favour of using the QTextDocument margin
  setting. PR #33.

**Code Improvements**

* Spell checking is now handled by a standard class that can be sub-classed to support different
  spell check tools. This was done because pyenchant is no longer maintained and having a standard
  wrapper makes it easier to support other tools. PR #31.

----

## Version 0.1.5 [2019-06-08]

**Bug Fixes**

* Closing the application with the window X button, and selecting No on the dialog, still closed
  the application. Properly handling the close event now so that the closing is cancelled. PR #21.
* Many of the menu option would cause novelWriter to exit or otherwise make mistakes when clicked
  if no project was open. They all check for this now. PR #23.

**Timeline**

* Added an index to the project that holds the position of all headers in the novel part of the
  project and all tags set in the notes part. It also holds all the links from novel files to
  notes. The relationship can be viewed in a new TimeLineView GUI. It's in the tools menu, and can
  also be opened with `Ctrl+T`. PR #22.
* The spell checker now used this index to highlight keywords/value sets. If the keyword or value
  is not valid, it will not be highlighted and will instead have a wiggly line under it. This also
  checks that references point to valid tags. For this to work, the index has to be up to date. The
  index of a file is saved when the file is saved, but the entire index can be rebuilt by pressing
  `F9`. PR #22.

**Status Bar**

* Redesign of the status bar adding project and session stats as well as a session timer. PR #21.
* Project word count is written to the project file, which is needed for the session word count.
  PR #21.
* Closing a project now clears the status bar. PR #21.

**Editor**

* Spell checker now ignores lines staring with `@`, and words in all uppercase. PR #21.
* A document can be closed, which also clears it from last edited document setting in the project
  file. I.e. it is not re-opened on next start. PR #21.
* Tab width is now by default 40 pixels, and can be set in the config. PR #21.

----

## Version 0.1.4 [2019-05-25]

**Bug Fixes**

* Fixed a bug where an item had to be selected in the tree view for a root item to be created.
  PR #16.

**User Interface**

* The main area can now be split into two, with the document editor on the left and a document
  viewer on the right. PR #13.
* The list of novel document status and plot element importance levels can now be edited through
  the Project Settings dialog. The values are per project, and saved in the main project XML file.
  PR #17.
* Cleaned up opening and closing projects, as well as how new projects are created. A new project
  can also not be saved in a folder already containing a novelWriter project. That was previously
  possible, resulting in the old XML file being overwritten. PR #18.
* Some minor GUI improvements were added, PR #19:
  * Pressing `F2` also opens the edit item dialog, like `Ctrl+E` does.
  * When the document editor and viewer split slider is moved, the editor resizes properly.
  * The document viewer can be closed, expanding the editor to the full window size again.
  * A project can be closed with `Ctrl+Shift+W`, and the menu entry has an icon.
  * Exit button/menu now asks if you want to close.

**Themes**

* The colours for syntax highlighting can now be edited in a config file in the themes folder. The
  main GUI css file also lives in the same folder. The default theme lives in the default
  subfolder, and more folders can be added. Switching themes involve changing the theme setting in
  the main config file to the name of the themes subfolder. PR #15.

**Code Improvements**

* Loading the project with the items in the wrong order is possible. That is, the child item is
  stored before its parent. A saved file should not ever be like that, but an edited file might.
  Even if the file shouldn't be edited manually. PR #16.

----

## Version 0.1.3 [2019-05-18]

**User Interface**

* The cursor position is now saved when a document is saved, and restored when the document is
  opened. PR #12.

**Test Suite**

* Major upgrades to the test suite, now also testing GUI elements. Coverage at 73%. PRs #9 and #11.

----

## Version 0.1.2 [2019-05-12]

**Bugfixes**

* Fixed a critical GUI bug when trying to create new folders and files in the tree.
* Caught a bug when creating a new file, but novelWriter couldn't figure out what class the parent
  item had and returned a `None`. Could not recreate the bug, but added a check for it anyway.

**Code Improvements**

* Changed the way user alerts are generated, and added the alert levels to an enum class named
  `nwAlert`. Also added a new level named `BUG`.

----

## Version 0.1.1 [2019-05-12]

**User Interface**

* Rewritten the spell check context menu. The previous implementation was adapted from a Qt4
  example, but could be improved a great deal. It now also doesn't have the default context menu,
  and allows for adding words to personal word list. Spell checking can also be enabled and
  disabled from the menu, and re-run on a the current document. PRs #1 and #3

**Test Suite**

* Added a unit test framework based on `pytest`. This currently checks basic opening and saving of
  the main config file and the main project file. PR #2

----

## Version 0.1 [2019-05-10]

This is the initial release of a working version of novelWriter, but with very limited
capabilities. So far, the following has been implemented:

* A document tree with a set of pre-defined root folders of a given set of classes for different
  purposes for novel writing. That is, a root item for the novel itself, one for characters, plot
  elements, timeline, locations, objects, and a custom one.
* A plain text editor with a simplified markdown format that allows for four levels of titles, and
  bold, italics and underline text.
  * In addition, the format supports comments with lines starting with a `%`.
  * It also allows for keyword/value sets staring with the character `@`. These will later be used
    to link documents together as tags point to other documents. For instance, a scene file can
    point the keyword `@POV:name` to a character file with the keyword `@THIS:name`.
* The text editor has a set of auto replace features:
  * Dashes are made by combining two or three hyphens.
  * Three dots are replaced with the ellipsis.
  * Straight quotes with your quote format of choice.
* The text editor also allows for wrapping either selected text, or the word under the cursor, in:
  * Bold, italics, or underline tags.
  * Single, or double quotes.
