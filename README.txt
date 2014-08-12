Inkscape Plugin that exports to Roland CutStudio

Windows installing:

Copy roland_* files to C:\Program Files\Inkscape\share\extensions\
(or Program Files (x86) )

Install Roland CutStudio to the default path: "C:\Program Files\CutStudio" or "C:\Program Files (x86)\CutStudio"

Mac / Linux+wine:
Does not work yet, the paths need to be adjusted

KNOWN BUGS:
CutStudio must be installed in default path - TODO read registry entry "HKLM\Software\Roland DG Corporation\CutStudio\Folder\Path"
WONTFIX: clipping of paths doesnt work






interna:
CutStudio does not really interpret EPS like a real EPS reader should. It only has a crude parser that only works with the EPS-export from certain versions of Corel and Illustrator.

It only knows these commands, one per line:
moveto:
1 2 m
lineto:
1 2 m
curveto:
1 2 3 4 5 6 c

UNKNOWN: are groups possible?

closing paths needs to be done by hand (repeat the first point)
