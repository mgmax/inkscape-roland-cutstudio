Inkscape Plugin that exports to Roland CutStudio

Usage:
- Install as described below
- Open inkscape with the file to cut. If you select objects, only the selected objects will be exported.
- Extensions - Roland CutStudio - Open in CutStudio


Windows installing:

checkout git repo or download the ZIP from https://github.com/mgmax/inkscape-roland-cutstudio/archive/master.zip

Copy all roland_* files to the inkscape extension folder, C:\Program Files\Inkscape\share\extensions\   (or C:\Program Files (x86)\... on 64bit systems)

Install Roland CutStudio to the default path: "C:\Program Files\CutStudio" or "C:\Program Files (x86)\CutStudio"

Mac / Linux+wine:
Does not work yet, the paths need to be adjusted

KNOWN BUGS:
CutStudio must be installed in default path - TODO read registry entry "HKLM\Software\Roland DG Corporation\CutStudio\Folder\Path"
WONTFIX: clipping of paths doesnt work
WONTFIX: if there is any object with opacity != 100%, inkscape exports some objects as bitmaps. They will disappear in CutStudio!
WONTFIX: filters (e.g. blur) are not supported





interna:
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
