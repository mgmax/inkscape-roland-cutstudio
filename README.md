# inkscape-roland-cutstudio

[Inkscape][] plugin that converts SVG files to an EPS format that Roland's [CutStudio][] software can read.

<!--p align="center">
    <img alt="Illustration of Inkscape file and CutStudio output" src="images/no-cutstudio.png"/>
</p-->

[Inkscape]: https://www.inkscape.org/
[CutStudio]: https://www.rolanddga.com/products/software/roland-cutstudio-software

## Usage

### Using with CutStudio installed

1. Open Inkscape.
2. Select the objects you want to export to CutStudio. If no objects are selected, everything in the file will be exported.
3. Open the Extensions menu, then select Roland CutStudio -> Open in CutStudio. Selecting 'Open in CutStudio (mirror horizontal ◢|◣)' will horizontally mirror all objects.

### Using without CutStudio installed

Follow the steps above. Once the plugin has completed the export, you'll see a dialog box that indicates where the EPS file has been saved. This file can be imported into CutStudio with File -> Import.

<p align="center">
    <img alt="Dialog box shown when plugin is run and CutStudio is not installed" src="images/no-cutstudio.png" width="425"/>
</p>

## Installing

1. Obtain the files by either cloning this repository or [downloading the repository zip file][zip].
2. Unzip if required and copy all files starting with 'roland\_' to the appropriate Inkscape extensions folder:
    a. For per-user installation: open Inkscape Preferences -> System, look for 'User Extensions' and click the 'Open' button.
    b. To install system-wide: open the same preferences tab. The correct folder is listed further down under 'Inkscape extensions'.
3. Restart Inkscape.

[zip]: https://github.com/mgmax/inkscape-roland-cutstudio/archive/refs/heads/master.zip

### Installation notes

- On Windows, CutStudio must be installed in the default path - `C:\Program Files\CutStudio` or `C:\Program Files (x86)\CutStudio`.
- CutStudio can be installed on Linux using WINE, but will probably not work for actually controlling Roland cutters.

### Inkscape versions < 1.2

Inkscape 1.2 [replaced verbs with actions][1.2notes], changing the way this plugin works. If you're using a version of Inkscape earlier than 1.2 you can get older versions of this plugin from the [releases page][releases]. Note that the installation instructions may be different, so please check the readme in the downloaded ZIP file.

[1.2notes]: https://wiki.inkscape.org/wiki/index.php/Release_notes/1.2#Command_line
[releases]: https://github.com/mgmax/inkscape-roland-cutstudio/releases

## Known issues

- Clipping of paths doesn't work. This can be worked around by using boolean operations to produce the actual path you want to cut before running the plugin.
- If there are any objects with opacity less than 100%, Inkscape exports them as bitmaps and they will not appear in CutStudio. This also occurs if the alpha value of the stroke or fill color is less than 100%.
- Filters (e.g. blur) are also exported as bitmaps, so are not supported.

These issues won't be fixed as there's a workaround for the first issue and CutStudio has no way of handling bitmaps.

## Contributing

I am sorry that the code is so horrible. If anyone feels the desire to burn everything and rewrite it from scratch, please feel free to do so. If you're making changes to the code, please make sure that `python2.7 roland_cutstudio.py --selftest` and `python3 roland_cutstudio.py --selftest` work before you submit a pull request.

## Details

CutStudio has a very crude EPS parser that only works with files exported from certain versions of Corel Draw and Adobe Illustrator. Specifically, it only knows these commands:

- moveto: `1 2 m`
- lineto: `1 2 l`
- curveto: `1 2 3 4 5 6 c`

It's not known if groups are possible (this plugin ungroups all objects before export), and closing paths has to be done by repeating the first point.