#!/usr/bin/env python2 
# -*- coding: utf-8 -*-
'''
Roland CutStudio export script
Copyright (C) 2014 Max Gaukler <development@maxgaukler.de>

skeleton based on Visicut Inkscape Plugin :
Copyright (C) 2012 Thomas Oster, thomas.oster@rwth-aachen.de

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
'''

import sys
import os
from subprocess import Popen
import subprocess
import shutil
import numpy

def debug(s):
	sys.stderr.write(s+"\n");
elements=[]

for arg in sys.argv[1:]:
 if arg[0] == "-":
  if len(arg) >= 5 and arg[0:5] == "--id=":
   elements +=[arg[5:]] # UNUSED
  elif len(arg) >= 13 and arg[0:13] == "--visicutbin=":
   VISICUTBIN=arg[13:] # UNUSED
  else:
   arguments += [arg]
 else:
  filename = arg

def removeAllButThem(element, elements):
 if element.get('id') in elements:
  return True
 else:
  keepSubtree = False
  for e in element:
   if not removeAllButThem(e, elements):
    element.remove(e)
   else:
    keepSubtree = True
  return keepSubtree

def which(program, extraPaths=[]):
    pathlist=os.environ["PATH"].split(os.pathsep)
    if "nt" in os.name:
        pathlist.append(os.environ.get("ProgramFiles","C:\Program Files\\"))
        pathlist.append(os.environ.get("ProgramFiles(x86)","C:\Program Files (x86)\\"))
        pathlist.append("C:\Program Files\\") # needed for 64bit inkscape on 64bit Win7 machines
    def is_exe(fpath):
        return os.path.isfile(fpath) and (os.access(fpath, os.X_OK) or fpath.endswith(".exe"))
    for path in pathlist:
      exe_file = os.path.join(path, program)
      if is_exe(exe_file):
        return exe_file
    raise Exception(str(program) + str(pathlist))
    

# header
# for debugging purposes you can open the resulting EPS file in Inkscape,
#  select all, ungroup multiple times
# --> now you can view the exported lines in inkscape
prefix="""
%!PS-Adobe-3.0 EPSF-3.0
%%LanguageLevel: 2
%%BoundingBox -10000 -10000 10000 10000
%%EndComments
%%BeginSetup
%%EndSetup
%%BeginProlog
% This code (until EndProlog) is from an inkscape-exported EPS, copyright unknown, see cairo-library
save
50 dict begin
/q { gsave } bind def
/Q { grestore } bind def
/cm { 6 array astore concat } bind def
/w { setlinewidth } bind def
/J { setlinecap } bind def
/j { setlinejoin } bind def
/M { setmiterlimit } bind def
/d { setdash } bind def
/m { moveto } bind def
/l { lineto } bind def
/c { curveto } bind def
/h { closepath } bind def
/re { exch dup neg 3 1 roll 5 3 roll moveto 0 rlineto
      0 exch rlineto 0 rlineto closepath } bind def
/S { stroke } bind def
/f { fill } bind def
/f* { eofill } bind def
/n { newpath } bind def
/W { clip } bind def
/W* { eoclip } bind def
/BT { } bind def
/ET { } bind def
/pdfmark where { pop globaldict /?pdfmark /exec load put }
    { globaldict begin /?pdfmark /pop load def /pdfmark
    /cleartomark load def end } ifelse
/BDC { mark 3 1 roll /BDC pdfmark } bind def
/EMC { mark /EMC pdfmark } bind def
/cairo_store_point { /cairo_point_y exch def /cairo_point_x exch def } def
/Tj { show currentpoint cairo_store_point } bind def
/TJ {
  {
    dup
    type /stringtype eq
    { show } { -0.001 mul 0 cairo_font_matrix dtransform rmoveto } ifelse
  } forall
  currentpoint cairo_store_point
} bind def
/cairo_selectfont { cairo_font_matrix aload pop pop pop 0 0 6 array astore
    cairo_font exch selectfont cairo_point_x cairo_point_y moveto } bind def
/Tf { pop /cairo_font exch def /cairo_font_matrix where
      { pop cairo_selectfont } if } bind def
/Td { matrix translate cairo_font_matrix matrix concatmatrix dup
      /cairo_font_matrix exch def dup 4 get exch 5 get cairo_store_point
      /cairo_font where { pop cairo_selectfont } if } bind def
/Tm { 2 copy 8 2 roll 6 array astore /cairo_font_matrix exch def
      cairo_store_point /cairo_font where { pop cairo_selectfont } if } bind def
/g { setgray } bind def
/rg { setrgbcolor } bind def
/d1 { setcachedevice } bind def
%%EndProlog
%%Page: 1 1
%%BeginPageSetup
%%PageBoundingBox: -10000 -10000 10000 10000
%%EndPageSetup
% This is a severely crippled fucked-up pseudo-postscript for importing in Roland CutStudio
% Do not even try to open it with something else

% Inkscape header, not used by cutstudio
% Start
q -10000 -10000 10000 10000 rectclip q

0 g
0.286645 w
0 J
0 j
[] 0.0 d
4 M q
% Cutstudio Start
"""
postfix="""
% Cutstudio End

%this is necessary for CutStudio so that the last line isnt skipped:
0 0 m

% Inkscape footer
S Q
Q Q
showpage
%%Trailer
end restore
%%EOF
"""

def EPS2CutstudioEPS(src, dest):
    def outputFromStack(stack, n, transformCoordinates=True):
        arr=stack[-(n+1):-1]
        if transformCoordinates:
            arrTransformed=[]
            for i in range(n/2):
                arrTransformed+=transform(arr[2*i], arr[2*i+1])
            return output(arrTransformed+[stack[-1]])
        else:
            return output(arr+[stack[-1]])
    def transform(x, y):
        #debug("trafo from: {} {}".format(x, y))
        p=numpy.matrix([[float(x),float(y),1]]).transpose()
        multiply = lambda a, b: a*b
        # concatenate transformations by multiplying: new = transformation x previousTransformtaion
        m=reduce(multiply, scalingStack[::-1])
        m=m.transpose()
        #debug("with {}".format(m))
        pnew=m*p
        x=float(pnew[0])
        y=float(pnew[1])
        #debug("to: {} {}".format(x, y))
        return [x, y]
    def outputMoveto(x, y):
        [xx, yy]=transform(x, y)
        return output([str(xx), str(yy), "m"])
    def outputLineto(x, y):
        [xx, yy]=transform(x, y)
        return output([str(xx), str(yy), "l"])
    def output(array):
        array=map(str, array)
        output=" ".join(array)
        #debug("OUTPUT: "+output)
        return output + "\n"
    stack=[]
    scalingStack=[numpy.matrix(numpy.identity(3))]
    outputStr=prefix
    inputFile=open(src)
    outputFile=open(dest, "w")
    for line in inputFile.readlines():
        line=line.strip()
        if line.startswith("%"):
            # comment line
            continue
        if line.endswith("re W n"): 
            continue # ignore clipping rectangle
        #debug(line)
        for item in line.split(" "):
            item=item.strip()
            if item=="":
                continue
            #debug("INPUT: " + item.__repr__())
            stack.append(item)
            if item=="h": # close path
                if True or lastCurveCoordinates!=lastMoveCoordinates:
                    assert lastMoveCoordinates,  "closed path before first moveto"
                    outputStr += outputLineto(float(lastMoveCoordinates[0]), float(lastMoveCoordinates[1]))
                else:
                    #debug("skipping unnecessary path-close")
                    pass
                    # endpoint and startpoint are already the same, no need for closing the path
            elif item == "c": # bezier curveto
                outputStr += outputFromStack(stack, 6)
                lastCurveCoordinates=stack[-3:-1]
                stack=[]
            elif item=="re": # rectangle
                    x=float(stack[-5])
                    y=float(stack[-4])
                    dx=float(stack[-3])
                    dy=float(stack[-2])
                    outputStr += outputMoveto(x, y)
                    outputStr += outputLineto(x+dx, y)
                    outputStr += outputLineto(x+dx, y+dy)
                    outputStr += outputLineto(x, y+dy)
                    outputStr += outputLineto(x, y)
            elif item=="cm": # matrix transformation
                newTrafo=numpy.matrix([[float(stack[-7]), float(stack[-6]), 0], [float(stack[-5]), float(stack[-4]), 0], [float(stack[-3]), float(stack[-2]), 1]])
                #debug("applying trafo "+str(newTrafo))
                scalingStack[-1]*=newTrafo
            elif item=="q": # save graphics state to stack
                scalingStack.append(numpy.matrix(numpy.identity(3)))
            elif item=="Q": # pop graphics state from stack
                scalingStack.pop()
            elif item in ["m", "l"]:
                if item=="m": # moveto
                    lastMoveCoordinates=stack[-3:-1]
                elif item=="l": # lineto
                    lastCurveCoordinates=stack[-3:-1]
                outputStr += outputFromStack(stack, 2)
                stack=[]
            else:
                pass # do nothing
    outputStr += postfix
    outputFile.write(outputStr)
    outputFile.close()

if os.name=="nt": # windows
    INKSCAPEBIN=which("Inkscape\inkscape.exe")
else:
    assert False,  "CutStudio on Mac and on Linux-Wine not yet supported,  need to adjust path"
      
assert os.path.isfile(INKSCAPEBIN),  "cannot find inkscape binary " + INKSCAPEBIN
shutil.copyfile(filename, filename+".orig.svg")

assert 0==subprocess.call([INKSCAPEBIN,"-z",filename+".orig.svg","-T", "--export-plain-svg="+filename+".plain.svg"]),  "plain-SVG conversion failed"
#os.unlink(filename+".orig.svg")
assert 0==subprocess.call([INKSCAPEBIN,"-z",filename+".plain.svg","-T", "--export-eps="+filename+".inkscape.eps"]), "EPS conversion failed"
#os.unlink(filename+".plain.svg")
EPS2CutstudioEPS(filename+".inkscape.eps", filename+".cutstudio.eps")

if os.name=="nt":
    DETACHED_PROCESS = 8 # start as "daemon"
    Popen([which("CutStudio\CutStudio.exe"), "/import", filename+".cutstudio.eps"], creationflags=DETACHED_PROCESS, close_fds=True)
#else:
#   Popen(["inkscape", filename+".cutstudio.eps"])
#os.unlink(filename+".cutstudio.eps")

