Inkscape Plugin that exports to Roland CutStudio

Windows installing:

Copy roland_* files to C:\Program Files\Inkscape\share\extensions\
(or Program Files (x86) )

Install Roland CutStudio to the default path.

Mac / Linux+wine:
Does not work yet, the paths need to be adjusted

KNOWN BUGS:

WONTFIX: clipping of paths doesnt work






interna:
CutStudio does not interpret EPS, it only has a crude parser that only works with the EPS-export from certain versions of Corel and Illustrator.

It only knows these commands:
moveto:
1 2 m
lineto:
1 2 m
curveto:
1 2 3 4 5 6 c

UNKNOWN: are groups possible?

closing paths needs to be done by hand (repeat the first point)

