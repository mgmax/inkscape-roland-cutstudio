#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
'''
Roland CutStudio export script
Copyright (C) 2014 - 2024 Max Gaukler <development@maxgaukler.de>

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

# The source code is a horrible mess. I apologize for your inconvenience, but hope that it still helps. Feel free to improve :-)

import sys
import os
from subprocess import Popen
import subprocess
import shutil
import numpy
from functools import reduce
import atexit
import filecmp
from pathlib import Path
import tempfile
import random
import string
import json
import re
from typing import Optional, List, Union

def message(s: str):
	sys.stderr.write(s+"\n")

def debug(s: str):
    message(s)

# copied from https://github.com/t-oster/VisiCut/blob/0abe785a30d5d5085dd3b5953b38239b1ff83358/tools/inkscape_extension/visicut_export.py
def which(program, raiseError, extraPaths=[], subdir=None):
    """
    find program in the $PATH environment variable and in $extraPaths.
    If $subdir is given, also look in the given subdirectory of each $PATH entry.
    """
    pathlist=os.environ["PATH"].split(os.pathsep)
    if "nt" in os.name:
        pathlist.append(os.environ.get("ProgramFiles","C:\Program Files\\"))
        pathlist.append(os.environ.get("ProgramFiles(x86)","C:\Program Files (x86)\\"))
        pathlist.append("C:\Program Files\\") # needed for 64bit inkscape on 64bit Win7 machines
        pathlist.append(os.path.dirname(os.path.dirname(os.getcwd()))) # portable application in the current directory
    pathlist += extraPaths
    if subdir:
        pathlist = [os.path.join(p, subdir) for p in pathlist] + pathlist
    def is_exe(fpath):
        return os.path.isfile(fpath) and (os.access(fpath, os.X_OK) or fpath.endswith(".exe"))
    for path in pathlist:
      exe_file = os.path.join(path, program)
      if is_exe(exe_file):
        return exe_file
    if raiseError:
        raise Exception("Cannot find " + str(program) + " in any of these paths: " + str(pathlist) + ". Either the program is not installed, PATH is not set correctly, or this is a bug.")
    else:
        return None

# copied from https://github.com/t-oster/VisiCut/blob/0abe785a30d5d5085dd3b5953b38239b1ff83358/tools/inkscape_extension/visicut_export.py
# Strip SVG to only contain selected elements, convert objects to paths, unlink clones
# Inkscape version: takes care of special cases where the selected objects depend on non-selected ones.
# Examples are linked clones, flowtext limited to a shape and linked flowtext boxes (overflow into the next box).
#
# Inkscape is called with certain "actions" to do the required cleanup
# The idea is similar to http://bazaar.launchpad.net/~nikitakit/inkscape/svg2sif/view/head:/share/extensions/synfig_prepare.py#L181 , but more primitive - there is no need for more complicated preprocessing here
def stripSVG_inkscape(src, dest, elements):    
    # create temporary file for opening with inkscape.
    # delete this file later so that it will disappear from the "recently opened" list.
    tmpfile = tempfile.NamedTemporaryFile(delete=False, prefix='temp-visicut-', suffix='.svg')
    tmpfile.close()
    tmpfile = tmpfile.name
    shutil.copyfile(src, tmpfile)


    # Updated for Inkscape 1.2, released 16 May 2022
    # inkscape --export-overwrite --actions=action1;action2...
    # (see inkscape --help, inkscape --action-list)
    # (for debugging, you can look at the intermediate state by running inkscape --with-gui --actions=... my_filename.svg)
    # Note that it is (almost?) impossible to find a sequence that works in all cases.
    # Cases to consider:
    # - selecting whole groups
    # - selecting objects within a group
    # - selecting across groups/layers (e.g., enter group, select something, then Shift-click to select things from other layers)
    # Difficulties with Inkscape:
    # - "invert selection" does not behave as expected in all these cases,
    #   for example if a group is selected then inverting can select the elements within.
    # - Inkscape has a wonderful --export-id commandline switch, but it only works correctly with one ID

    # Solution:
    actions = []
    # - select objects
    actions += ["select-by-id:" + ",".join(elements)]
    # - convert to path
    actions +=  ["clone-unlink", "object-to-path"]
    # - create group of selection
    actions += ["selection-group"]
    # - set group ID to a known value. Use a pseudo-random value to avoid collisions
    target_group_id = "TARGET-GROUP-" + "".join(random.sample(string.ascii_lowercase, 20))
    actions += ["object-set-attribute:id," + target_group_id]
    # - set export options: use only the target group ID, nothing else
    actions += ["export-id-only:true", "export-id:" + target_group_id]
    # - export
    actions += ["export-do"]


    command = [inkscape_command(), tmpfile, "--export-overwrite", "--actions=" + ";".join(actions)]
    # to print the resulting commandline:
    # print(" ".join(["'" + c + "'" for c in command]), file=sys.stderr)
    
    
    DEBUG = False
    if DEBUG:
        # Inkscape sometimes silently ignores wrong verbs, so we need to double-check that everything's right
        for action in actions:
            aciton_list = [line.split(":")[0] for line in subprocess.check_output([inkscape_command(), "--action-list"], stderr=DEVNULL).split("\n")]
            if action not in action_list:
                sys.stderr.write("Inkscape does not have the action '{}'. Please report this as a VisiCut bug.".format(action))
        
    inkscape_output = "(not yet run)"
    try:
        #sys.stderr.write(" ".join(command))
        # run inkscape, buffer output
        inkscape = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        inkscape_output = inkscape.communicate()[0]
        if inkscape.returncode != 0:
            sys.stderr.write("Error: cleaning the document with inkscape failed. Something might still be shown in visicut, but it could be incorrect.\nInkscape's output was:\n" + str(inkscape_output))
    except:
        sys.stderr.write("Error: cleaning the document with inkscape failed. Something might still be shown in visicut, but it could be incorrect. Exception information: \n" + str(sys.exc_info()[0]) + "Inkscape's output was:\n" + str(inkscape_output))

    # move output to the intended destination filename
    os.rename(tmpfile, dest)


def mm_to_pt(x_mm: float) -> float:
    """
    convert value from millimeters to EPS points (pt).
    """
    return x_mm * 72 / 25.4

def make_cropmark_header(cropmark_settings: Optional[dict]) -> str:
    """
    Generate %%RolandCropMark EPS command.
    
    :param cropmark_settings: see parse_cropmark_settings()
    """
    
    if cropmark_settings is None:
        return ""
    
    """
    Calculate values for CutStudio:
    
    base_x_mm Setting "BaseX" in CutStudio. Meaning unclear. Probably: Radius of cropmark.
    base_y_mm: Setting "BaseY" in CutStudio. Meaning unclear. Probably: Radius of cropmark.
    width_mm: Setting "W" in CutStudio. X distance between center of cropmarks.
    height_mm: Setting "H" in CutStudio. Y distance between center of cropmarks.
    """
    base_x_mm = 5 # default value from CutStudio
    base_y_mm = 5 # default value from CutStudio
    width_mm = cropmark_settings["W"]
    height_mm = cropmark_settings["H"]
    return f"%%RolandCropMark: {mm_to_pt(base_x_mm)} {mm_to_pt(base_y_mm)} {mm_to_pt(width_mm)} {mm_to_pt(height_mm)} 56.692913 56.692913 4\n"


# Template for EPS file in CutStudio format
# for debugging purposes you can open the resulting EPS file in Inkscape,
#  select all, ungroup multiple times
# --> now you can view the exported lines in inkscape
CUTSTUDIO_EPS_TEMPLATE="""
%!PS-Adobe-3.0 EPSF-3.0
%%LanguageLevel: 2
%%BoundingBox: -10000 -10000 10000 10000
%<CROPMARK_INSERTED_HERE>
%%EndComments
%%BeginSetup
%%EndSetup
%%BeginProlog
% This code (until EndProlog) is from an inkscape-exported EPS, copyright unknown, see cairo-library
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
/cairo_data_source {
  CairoDataIndex CairoData length lt
    { CairoData CairoDataIndex get /CairoDataIndex CairoDataIndex 1 add def }
    { () } ifelse
} def
/cairo_flush_ascii85_file { cairo_ascii85_file status { cairo_ascii85_file flushfile } if } def
/cairo_image { image cairo_flush_ascii85_file } def
/cairo_imagemask { imagemask cairo_flush_ascii85_file } def
%%EndProlog
%%Page: 1 1
%%BeginPageSetup
%%PageBoundingBox: -10000 -10000 10000 10000
%%EndPageSetup
% This is a severely crippled fucked-up pseudo-postscript for importing in Roland CutStudio
% For debugging purpose you can also try to open it in Inkscape

% Inkscape header, not used by cutstudio
% Start


q q
0 g
1.41732 w
0 J
0 j
[] 0.0 d
4 M q 
% Cutstudio Start
%<CUTTING_LINES_INSERTED_HERE>
% Cutstudio End

%this is necessary for CutStudio so that the last line isnt skipped:
0 0 m

% Inkscape footer, not used by cutstudio
S Q

Q Q
showpage
%%Trailer
end
%%EOF

"""

def EPS2CutstudioEPS(src: str, dest: str, mirror: bool = False, cropmark_settings : Optional[dict] = None):
    """
    Convert original EPS (from Inkscape) to something that CutStudio understands.

    Mainly, we ungroup all groups and apply all transformations.
    To implement this we build a crude EPS parser.

    :param mirror: Mirror horizontally

    :param cropmark_settings:
        'None' for normal cutting.
        To enable cropmark scanning, set it to a dict specifying the page size (pageW, pageH)
        and the cropmark location settings (dx, dy, W, H) as defined in make_cropmark_header()
    """
    def outputFromStack(stack, n, transformCoordinates=True):
        arr=stack[-(n+1):-1]
        if transformCoordinates:
            arrTransformed=[]
            for i in range(n//2):
                arrTransformed+=transform(arr[2*i], arr[2*i+1])
            return output(arrTransformed+[stack[-1]])
        else:
            return output(arr+[stack[-1]])
    def transform(x, y):
        #debug("trafo from: {} {}".format(x, y))
        p=numpy.array([[float(x),float(y),1]]).transpose()
        multiply = lambda a, b: numpy.matmul(a, b)
        # concatenate transformations by multiplying: new = transformation x previousTransformtaion
        m=reduce(multiply, scalingStack[::-1])
        m=m.transpose()
        #debug("with {}".format(m))
        pnew = numpy.matmul(m, p)
        x=float(pnew.item(0))
        y=float(pnew.item(1))
        #debug("to: {} {}".format(x, y))
        return [x, y]
    def outputMoveto(x, y):
        [xx, yy]=transform(x, y)
        return output([str(xx), str(yy), "m"])
    def outputLineto(x, y):
        [xx, yy]=transform(x, y)
        return output([str(xx), str(yy), "l"])
    def output(array):
        array=list(map(str, array))
        output=" ".join(array)
        #debug("OUTPUT: "+output)
        return output + "\n"
    stack=[]
    scalingStack=[numpy.identity(3)]     
    lastMoveCoordinates=None
    
    # Set up initial transformation
    if mirror and cropmark_settings:
        raise Exception("Mirror horizontal is not supported when cropmarks are used")
    if mirror:
        # Horizontal mirroring is enabled by user
        scalingStack.append(numpy.diag([-1, 1, 1]))
    if cropmark_settings:
        # Translation for cropmarks (cropmark is always at fixed position, cut lines must be moved appropriately)
        # 5 is the currently hardcoded value of BaseX and BaseY
        translate_x = mm_to_pt(5 - cropmark_settings["dx"])
        translate_y = mm_to_pt(5 - cropmark_settings["dy"])
        # FIXME: why is .transpose() needed here?
        scalingStack.append(numpy.array([[1, 0, translate_x], [0, 1, translate_y], [0, 0, 1]]).transpose())
    
    outputStr = ""
    
    # Actual EPS content
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
                assert lastMoveCoordinates,  "closed path before first moveto"
                outputStr += outputLineto(float(lastMoveCoordinates[0]), float(lastMoveCoordinates[1]))
            elif item == "c": # bezier curveto
                outputStr += outputFromStack(stack, 6)
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
                newTrafo=numpy.array([[float(stack[-7]), float(stack[-6]), 0], [float(stack[-5]), float(stack[-4]), 0], [float(stack[-3]), float(stack[-2]), 1]])
                #debug("applying trafo "+str(newTrafo))
                scalingStack[-1] = numpy.matmul(scalingStack[-1], newTrafo)
            elif item=="q": # save graphics state to stack
                scalingStack.append(numpy.identity(3))
            elif item=="Q": # pop graphics state from stack
                scalingStack.pop()
            elif item in ["m", "l"]:
                if item=="m": # moveto
                    lastMoveCoordinates=stack[-3:-1]
                elif item=="l": # lineto
                    pass
                outputStr += outputFromStack(stack, 2)
                stack=[]
            else:
                pass # do nothing
        
    # Postscript Header and footer, incl. magic comment for cropmark locations
    epsContent = CUTSTUDIO_EPS_TEMPLATE
    epsContent = epsContent.replace("%<CROPMARK_INSERTED_HERE>\n", make_cropmark_header(cropmark_settings))
    epsContent = epsContent.replace("%<CUTTING_LINES_INSERTED_HERE>\n", outputStr)
    outputFile.write(epsContent)
    outputFile.close()
    inputFile.close()

def parse_cropmark_settings(svg_contents: str) -> Optional[dict]:
    """
    Parse SVG file and determine cropmark marker settings.
    Settings are stored in a string like
    'INKSCAPE_CUTSTUDIO_CROPMARK_SETTINGS={"version":1, "pageW":210, "pageH":297, "dx":20, "dy":25, "W":170, "H":120}'
    that is part of a text element.
    
    
    Return settings as dictionary, if present. Else, return None.
    
    
    Settings entries:
    
    version: currently fixed to 1, may be used to detect incompatible old templates
    
    pageW, pageH: page size in mm
    
    dx, dy: distance in X/Y between bottom left corner of page and bottom left cropmark
    
    W, H: distance in X/Y between center of cropmarks
    
    """
    match = re.search(r'INKSCAPE_CUTSTUDIO_CROPMARK_SETTINGS=(\{["a-zA-Z0-9,\.: ]+\})', svg_contents.replace("&quot;", '"'))
    if not match:
        return None
    settings = json.loads(match.group(1))
    if settings.get("version") != 1:
        raise Exception("invalid cropmark settings version. Please use the newest template file.")
    return settings

assert parse_cropmark_settings('INKSCAPE_CUTSTUDIO_CROPMARK_SETTINGS={"version":1, "pageW":210, "pageH":297, "dx":20, "dy":25, "W":170, "H":120}'.replace('"', '&quot;')) == {"version": 1, "pageW": 210, "pageH": 297, "dx": 20, "dy": 25, "W": 170, "H": 120};

def call_inkscape(args: List[str]):
    """
    Call inkscape with the given arguments
    """
    # work around Inkscape 1.3 failing to start when it "calls itself" (Inkscape -> Extension -> Inkscape):
    # https://gitlab.com/inkscape/inkscape/-/issues/4163
    # https://gitlab.com/inkscape/extensions/-/merge_requests/534
    # TODO: Rewrite most parts of this extension using the inkex python module. This removes the need for such workarounds.
    os.environ["SELF_CALL"] = "true"
    
    cmd = [inkscape_command()] + args
    assert 0 == subprocess.call(cmd, stderr=subprocess.DEVNULL), 'Calling Inkscape failed: command returned error: ' + '"' + '" "'.join(cmd) + '"'

def inkscape_command() -> str:
    """
    Get path to Inkscape binary
    """
    if "INKSCAPE_COMMAND" in os.environ:
        INKSCAPEBIN = os.environ["INKSCAPE_COMMAND"]
        sys.stderr.write("hallo")
    elif os.name=="nt": # windows
        INKSCAPEBIN = which("inkscape.exe", True, subdir="Inkscape")
    else:
        INKSCAPEBIN=which("inkscape", True)

    assert os.path.isfile(INKSCAPEBIN),  "cannot find inkscape binary " + INKSCAPEBIN
    return INKSCAPEBIN

def remove_unselected_elements_from_SVG(filename: str, selectedElements: List[str]):
    """
    SVG --> SVG with only selected elements
    """
    if len(selectedElements)==0:
        shutil.copyfile(filename, filename+".filtered.svg")
    else:
        # only take selected elements
        stripSVG_inkscape(src=filename, dest=filename+".filtered.svg", elements=selectedElements)
    return filename + ".filtered.svg"

def svg_to_inkscape_eps(svg_file_in: str, eps_file_out: str, export_area_page: bool):
    """
    SVG --> Inkscape EPS
    
    :param svg_file_in: File path of SVG file input
    :param eps_file_out: File path of EPS file output
    :param export_area_page: True: preserve position relative to page / False: crop to drawing area
    """
    cmd = ["-T", "--export-ignore-filters"]
    if export_area_page:
        cmd += ["--export-area-page"]
    else:
        cmd += ["--export-area-drawing"]
    cmd += ["--export-filename="+eps_file_out, svg_file_in]
    call_inkscape(cmd)
    assert os.path.exists(eps_file_out), 'EPS conversion failed: command did not create result file: ' + '"' + '" "'.join(cmd) + '"' 

def open_in_cutstudio(cutstudio_eps_file: str) -> None:
    """
    Open EPS file in CutStudio
    """
    if os.name=="nt":
        # on Windows
        DETACHED_PROCESS = 8 # start as "daemon"
        Popen([which("CutStudio\CutStudio.exe", True), "/import", cutstudio_eps_file], creationflags=DETACHED_PROCESS, close_fds=True)
    else:
        # On Linux, try with "wine"
        CUTSTUDIO_C_DRIVE = str(Path.home()) + "/.wine/drive_c/"
        CUTSTUDIO_PATH_LINUX_WINE = CUTSTUDIO_C_DRIVE + "Program Files (x86)/CutStudio/CutStudio.exe"
        CUTSTUDIO_COMMANDLINE = ["wine", CUTSTUDIO_PATH_LINUX_WINE, "/import", r'C:\cutstudio.eps']
        try:
            if not which("wine", False):
                    raise Exception("Cannot find 'wine'")
            if not os.path.exists(CUTSTUDIO_PATH_LINUX_WINE):
                raise Exception("Cannot find CutStudio in " + CUTSTUDIO_PATH_LINUX_WINE)
            shutil.copyfile(cutstudio_eps_file, CUTSTUDIO_C_DRIVE + "cutstudio.eps")
            subprocess.check_call(CUTSTUDIO_COMMANDLINE, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
        except Exception as exc:
            message("Could not open CutStudio.\nInstead, your file was saved to:\n" + cutstudio_eps_file + "\n" + \
                "Please open that with CutStudio manually. \n\n" + \
                "Tip: On Linux, you can use 'wine' to install CutStudio 3.10. Then, the file will be directly opened with CutStudio. \n" + \
                " Diagnostic information: \n" + str(exc))

def read_file(path: Union[str, Path]) -> str:
    """
    Read text file to string
    """
    with open(path) as f:
        return f.read()

def inkscape_to_cutstudio() -> None:
    """
    Take Inkscape SVG, process and send to CutStudio.
    """
    
    # parse commandline: selftest mode
    selftest = ("--selftest" in sys.argv)
    
    # parse commandline: selected elements and filename
    selectedElements=[]
    for arg in sys.argv[1:]:
        if arg[0] == "-":
            if len(arg) >= 5 and arg[0:5] == "--id=":
                selectedElements +=[arg[5:]]
        else:
            filename = arg
    if selftest:
        filename = "./test-input.svg"
        
    # parse commandline: mirror horizontal
    mirror = ("--mirror=true" in sys.argv)
    
    
    # Determine cropmark settings.
    # If the SVG file is based on the cropmark template generated by this plugin, then it contains a "magic text" from which the cropmark information is determined.
    # Else, cropmark_settings is None.
    cropmark_settings=parse_cropmark_settings(read_file(filename))
    
    # SVG --> SVG with only selected elements
    svg_only_selection = remove_unselected_elements_from_SVG(filename, selectedElements)
    
    # SVG --> Inkscape EPS
    inkscape_eps = filename+".inkscape.ps"
    # If cropmark is active, then preserve the position relative to the page. Else, fit to drawing ("move to bottom-left" in CutStudio).
    export_area_page = (cropmark_settings is not None)
    svg_to_inkscape_eps(svg_file_in = filename+".filtered.svg", eps_file_out=inkscape_eps, export_area_page=export_area_page)
    

    # determine destination filename
    if selftest:
        # used for unit-testing: fixed location of output file
        destination = "./test-output-actual.cutstudio.eps"
    else:
        # normally
        destination = filename + ".cutstudio.eps"
    
    # Inkscape EPS --> CutStudio EPS
    EPS2CutstudioEPS(inkscape_eps, destination, mirror=mirror, cropmark_settings=cropmark_settings)

    # Show in CutStudio
    open_in_cutstudio(destination)

    if selftest:
        # unittest: compare with known reference output
        TEST_REFERENCE_FILE = "./test-output-reference.cutstudio.eps"
        assert filecmp.cmp(destination, TEST_REFERENCE_FILE), "Test output changed. Please compare " + destination + " and " + TEST_REFERENCE_FILE
        print("Selftest successful :-)")



def main() -> None:
    """
    Main function.
    
    Handle the main operating modes of the plugin:
    - Cropmark template
    - Open in Cutstudio
    """
    
    if "--cropmark-template=true" in sys.argv:
        # Generate template for cropmarks
        # Currently, we return a hardcoded result, removing all existing contant.
        # User settings are currently hard coded as:
        # Page size A4 with W=170 L=210 mm, lower-left cropmark is offset from lower-left-corner by dX=20 dY=25 mm
        TEMPLATE_FILE = Path().absolute() / "roland_cutstudio_cropmark_template.svg"
        print(read_file(TEMPLATE_FILE))
        return

    # Standard case: Inkscape to cutstudio
    inkscape_to_cutstudio()
    
if __name__ == "__main__":
    main()
