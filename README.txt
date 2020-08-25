Inkscape Plugin that exports to Roland CutStudio

Usage:
- Install as described below
- Open inkscape with the file to cut. If you select objects, only the selected objects will be exported.
- Extensions - Roland CutStudio - Open in CutStudio


Installing:

checkout git repo or download the ZIP from https://github.com/mgmax/inkscape-roland-cutstudio/archive/master.zip

Copy all roland_* files to the inkscape extensions folder:
- Per-user installation: The path is shown in Inkscape: Edit - Preferences - System - User extensions.
- System-wide installation on Windows (not for "Inkscape Portable"): Use the existing "extensions" folder in Inkscape's installation, usually C:\Program Files\Inkscape\share\inkscape\extensions\ or ...\share\extensions\   (or C:\Program Files (x86)\... on some systems). 

Then restart Inkscape.

On Windows, install Roland CutStudio to the default path: "C:\Program Files\CutStudio" or "C:\Program Files (x86)\CutStudio"

On Mac / Linux, the file is saved as .eps and you have to open CutStudio yourself or copy this file to another PC with CutStudio installed. (CutStudio does not work on Linux, maybe it does with Wine).

KNOWN BUGS:
CutStudio must be installed in default path - TODO read registry entry "HKLM\Software\Roland DG Corporation\CutStudio\Folder\Path"
WONTFIX: clipping of paths doesnt work
WONTFIX: if there is any object with opacity != 100%, inkscape exports some objects as bitmaps. They will disappear in CutStudio!
WONTFIX: filters (e.g. blur) are not supported


Contributing:

I am sorry that the code is so horrible. If anyone feels the desire to burn everything and rewrite it from scratch, please feel free to do so.
If you change the code, please make sure that `python2.7 roland_cutstudio.py --selftest` and `python3 roland_cutstudio.py --selftest` still work.

Internal details:

CutStudio does not really interpret EPS like a real EPS reader should. It only has a crude parser that only works with the EPS-export from certain versions of Corel and Illustrator.

It only knows these commands, one per line:
moveto:
1 2 m
lineto:
1 2 l
curveto:
1 2 3 4 5 6 c

UNKNOWN: are groups possible?

closing paths needs to be done by hand (repeat the first point)
