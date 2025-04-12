#!/usr/bin/env python3
# coding=utf-8
#
# Authors:
#   Nicolas Dufour - Association Inkscape-fr
#   Aurelio A. Heckert <aurium(a)gmail.com>
#
# Copyright (C) 2008 Authors
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
"""
this extension automates the editing of cropmarks for the inkscape roland cutstudio extnesion
based on Inkscape's printing marks extension
"""

import math
import re
import inkex
from inkex import Circle, Rectangle, TextElement
from inkex.paths import Path
from lxml import etree

class PrintingMarks(inkex.EffectExtension):

    def add_arguments(self, pars):
        pars.add_argument("--preset", help="Machine type (or 'custom' to use custom margins)", default="gx_24_gs_24")

        pars.add_argument("--page_size", help="Page size (or 'custom' to use custom new_width and new_height, or 'keep' to keep old page size)", default="A1")

        pars.add_argument("--unit", default="mm", help="Draw measurement")
        pars.add_argument("--mark_type", default="Four", help="Type of marks")
        pars.add_argument("--new_width", type=float, default=210.0, help="Width")
        pars.add_argument("--new_height", type=float, default=297.0, help="Height")
        pars.add_argument("--area_inset", type=float, default=0.0, help="Cut Area Inset")
        pars.add_argument("--margin_top", type=float, default=40.0, help="Bleed Top Size")
        pars.add_argument("--margin_bottom", type=float, default=20.0, help="Bleed Bottom Size")
        pars.add_argument("--margin_left", type=float, default=20.0, help="Bleed Left Size")
        pars.add_argument("--margin_right", type=float, default=20.0, help="Bleed Right Size")
        pars.add_argument("--tab", help="The selected UI-tab when OK was pressed")

    def apply_presets(self):
        """
        Applies page size and margin presets based on user-selected options.
        Overrides only if the user has not selected 'custom' or 'keep' (for page size).
        """
        # Preset margins for machines
        machine_margins = {
            "gx_24_gs_24": {"top": 60.0, "bottom":  20.0, "left": 15.0, "right": 15.0},
            "gr_g": {"top": 30.0, "bottom": 45.0, "left": 10.0, "right": 10.0},
            "sv_series": {"top": 6.0, "bottom": 30.0, "left": 23.0, "right": 23.0},
            "sv_8": {"top": 6.0, "bottom": 30.0, "left": 23.0, "right": 23.0},
        }

        # Page size dimensions in mm
        page_sizes = {
            "A1": {"width": 594.0, "height": 841.0},
            "A2": {"width": 420.0, "height": 594.0},
            "A3": {"width": 297.0, "height": 420.0},
            "A4": {"width": 210.0, "height": 297.0},
        }

        # Handle page size overwrites unless "custom" is selected
        if self.options.page_size != "custom":
            if self.options.page_size in page_sizes:
                page = page_sizes[self.options.page_size]
                self.options.new_width = page["width"]
                self.options.new_height = page["height"]

        # Handle margin overwrites unless "manual" is selected
        if self.options.preset != "custom":
            if self.options.preset in machine_margins:
                margins = machine_margins[self.options.preset]
                self.options.margin_top = margins["top"]
                self.options.margin_bottom = margins["bottom"]
                self.options.margin_left = margins["left"]
                self.options.margin_right = margins["right"]

    def apply_resize_page(self, width, height, unit="mm"):
        """
        Resize the SVG page to the given width and height.

        Args:
            self: The extension object (used to access the SVG root).
            width (float): Desired width of the page.
            height (float): Desired height of the page.
            unit (str): Unit for the dimensions (e.g., "mm", "px", "in"). Default is "mm".
        """
        # Access the SVG root element
        root = self.document.getroot()

        # Set the new page size
        root.set("width", f"{width}{unit}")
        root.set("height", f"{height}{unit}")

        # Update the viewBox to match the new dimensions
        root.set("viewBox", f"0 0 {width} {height}")

    def draw_reg_circile(self, x, y, name, parent):
        """Draw a circle with 10mm diameter and black fill, no stroke, at specified position."""
        style = {
            "fill": "#000000",  # Black fill
            "stroke": "none"    # No stroke
        }
        circle_attribs = {
            "style": str(inkex.Style(style)),
            inkex.addNS("label", "inkscape"): name,
            "id": re.sub(r'\W+', '_', name),  # Replace non-alphanumeric characters with underscores
            "cx": str(x),       # X position
            "cy": str(y),       # Y position
            "r": "5"            # Radius is half of the 10mm diameter
        }
        parent.add(inkex.elements.Circle(**circle_attribs))

    def draw_hairline_rectangle(self, parent, x, y, width, height):
        """
        Draws a rectangle with a hairline border in gray, with a fixed ID and name.
        Also adds a text label below the rectangle.

        Args:
            parent (inkex.BaseElement): The parent SVG element to which the rectangle will be added.
            x (float): The x-coordinate of the rectangle's top-left corner.
            y (float): The y-coordinate of the rectangle's top-left corner.
            width (float): The width of the rectangle.
            height (float): The height of the rectangle.
        """
        # Define the style for the rectangle
        style = {
            "stroke": "#808080",  # Gray color
            "stroke-width": "0.1px",  # Hairline border
            "fill": "none",  # No fill
        }

        # Define rectangle attributes with a fixed ID and label
        rect_attribs = {
            "x": str(x),
            "y": str(y),
            "width": str(width),
            "height": str(height),
            "style": str(inkex.Style(style)),
            "id": "cutting_area",  # Fixed ID
            inkex.addNS("label", "inkscape"): "Cutting Area",  # Fixed name for the rectangle
        }

        # Add the rectangle to the parent
        rect = inkex.elements.Rectangle(**rect_attribs)
        parent.add(rect)

        text_style = {
            "fill": "#808080",  # Gray color
            "font-size": "5px",  # Font size in user units (px)
            "text-anchor": "middle",  # Center alignment
        }

        # Define the text position (centered below the rectangle)
        text_x = x + (width / 2)  # Center of the rectangle
        text_y = y + height + 5   # 5mm below the bottom of the rectangle

        # Create the text element
        text_attribs = {
            "x": str(text_x),
            "y": str(text_y),
            "style": str(inkex.Style(text_style)),
            "id": "cutting_area_label",
            inkex.addNS("label", "inkscape"): "Cutting Area Label",
        }

        text = inkex.elements.TextElement(**text_attribs)
        text.text = "Cutting Area"
        parent.add(text)

    def add_open_path(self, vertices, style, svg_layer):
        """
        Adds an open path to the given SVG layer.

        :param vertices: List of (x, y) tuples representing the path vertices.
        :param style: SVG style string for the path (e.g., "stroke:red; fill:none; stroke-width:2").
        :param svg_layer: The SVG layer to which the path will be added.
        :return: The created PathElement.
        """
        if not vertices:
            raise ValueError("No vertices provided")

        # Create path data string
        path_data = f"M {vertices[0][0]},{vertices[0][1]} "  # Move to the first point
        path_data += " ".join(f"L {x},{y}" for x, y in vertices[1:])  # Line to subsequent points

        # Create and style the path element
        path_element = svg_layer.add(inkex.PathElement())
        path_element.set('d', path_data)  # Set the 'd' attribute with the path data
        path_element.style = inkex.Style.parse_str(style)

        return path_element

    def add_helper_layer(self, x, y, width, height):
        """
        Adds a helper layer and draws a hairline rectangle on it.

        Args:
            x (float): The x-coordinate of the rectangle's top-left corner.
            y (float): The y-coordinate of the rectangle's top-left corner.
            width (float): The width of the rectangle.
            height (float): The height of the rectangle.
        """
        svg = self.document.getroot()
        
        layer_id = "helper"
        layer_name = "Helper Layer - do not print or cut"
        
        # Create a new layer
        layer = svg.add(inkex.Layer.new(layer_name))
        layer.set("id", layer_id)
        layer.set("sodipodi:insensitive", "true")

        # Call the draw_hairline_rectangle function to add the rectangle to the layer
        self.draw_hairline_rectangle(layer, x, y, width, height)

    def add_cropmark_settings_text(
        self, pageW, pageH, dx, dy, W, H, x, y, parent
        ):
            """
            Adds a text object to the given parent with crop mark settings.

            Args:
                parent (inkex.BaseElement): The parent SVG element to add the text to.
                pageW (float): Page width in user units.
                pageH (float): Page height in user units.
                dx (float): Horizontal offset in user units.
                dy (float): Vertical offset in user units.
                W (float): Width in user units.
                H (float): Height in user units.
                x (float): X-coordinate for the text.
                y (float): Y-coordinate for the text.
                font_size (str): Font size for the text. Default is "9pt".
            """
            # Convert numeric values to integers to remove decimal points
            pageW = float(pageW)
            pageH = float(pageH)
            dx = float(dx)
            dy = float(dy)
            W = float(W)
            H = float(H)

            text_style = {
                "fill": "#000000",  
                "font-size": "3px", 
                "text-anchor": "middle",
            }

            txt_attribs = {
                "x": str(x),
                "y": str(y),
                "style": str(inkex.Style(text_style)),
                "id": "cropmark_settings",
                inkex.addNS("label", "inkscape"): "Cropmark Settings",
            }
            txt = parent.add(inkex.TextElement(**txt_attribs))
            

            # Construct the cropmark settings string without the extra {{
            txt.text = (
                f'INKSCAPE_CUTSTUDIO_CROPMARK_SETTINGS={{"version":1, '
                f'"pageW":{pageW}, "pageH":{pageH}, '
                f'"dx":{dx}, "dy":{dy}, '
                f'"W":{W}, "H":{H}}}'
            )

    def draw_effect(self, bbox, name=""):
        # Get SVG document dimensions
        # self.width must be replaced by bbox.right. same to others.
        svg = self.document.getroot()
        
        # Construct layer id and layer name
        layer_id = "cropmarks"
        layer_name = "Cropmarks - do not edit"
        if name != "":
            layer_id += "-" + name
            layer_name += " " + name

        # Create a new layer
        layer = svg.add(inkex.Layer.new(layer_name))
        layer.set("id", layer_id)
        layer.set("sodipodi:insensitive", "true")
        
        # Convert parameters to user unit
        offset = self.svg.viewport_to_unit(
            str(self.options.area_inset) + self.options.unit
        )
        margin_top = self.svg.viewport_to_unit(str(self.options.margin_top) + self.options.unit)
        margin_bottom = self.svg.viewport_to_unit(str(self.options.margin_bottom) + self.options.unit)
        margin_left = self.svg.viewport_to_unit(str(self.options.margin_left) + self.options.unit) 
        margin_right = self.svg.viewport_to_unit(str(self.options.margin_right) + self.options.unit)

        # External edges of the cropmarks
        border_left = bbox.left + margin_left
        border_right = bbox.right - margin_right
        border_top = bbox.top + margin_top
        border_bottom = bbox.bottom - margin_bottom

        if self.options.mark_type == "three":
            # Center lines for cropmarks
            offset_left = bbox.left + margin_left + 5
            offset_right = bbox.right - margin_right - 5 
            offset_top = bbox.top + margin_top + 5
            offset_bottom = bbox.bottom - margin_bottom - 5
            
            # CutStudio uses cardinal coordinates for positioning the cropmarks
            dx = offset_left
            dy = offset_left
            # Spacing between the cropmarks
            width = offset_right - offset_left, 5
            height = offset_bottom - offset_top, 5

            # Area internal to the cropmarks 
            # Positioning starting x and y at the edge of the cropmark by adding the radius of the cropmark
            cutting_area_x = offset_left + 5
            cutting_area_y = offset_top + 5

            # Subtracting 2 times the radius of the cropmarks
            cutting_area_width = width - 10
            cutting_area_heignt = height - 10

            # Get middle positions
            middle_vertical = bbox.top + (bbox.height / 2)
            middle_horizontal = bbox.left + (bbox.width / 2)


            # Cropmark Information
            self.add_cropmark_settings_text(bbox.right, bbox.bottom, dx, dy, width, height, str(middle_horizontal), str(bbox.bottom + 20), layer)
            self.draw_reg_circile(offset_left, offset_top, "Top Left Cropmark", layer)
            self.draw_reg_circile(offset_left, offset_bottom, "Bottom Left Cropmark", layer)
            self.draw_reg_circile(offset_right, offset_bottom, "Bottom Right Cropmark", layer)

        if self.options.mark_type == "four":

            # Center lines for cropmarks (with 4 crop marks the crop marks are pushed inwards by the manual marks)
            mark_size = 5
            offset_left = bbox.left + margin_left + (5 + mark_size)
            offset_right = bbox.right - margin_right - (5 + mark_size)
            offset_top = bbox.top + margin_top + (5 + mark_size)
            offset_bottom = bbox.bottom - margin_bottom - (5 + mark_size)
            
            # CutStudio uses cardinal coordinates for positioning the cropmarks
            dx = offset_left
            dy = offset_left
            # Spacing between the cropmarks
            width = offset_right - offset_left
            height = offset_bottom - offset_top

            # Area internal to the cropmarks 
            # Positioning starting x and y at the edge of the cropmark by adding the radius of the cropmark
            cutting_area_x = offset_left + 5
            cutting_area_y = offset_top + 5

            # Subtracting 2 times the radius of the cropmarks
            cutting_area_width = width - 10
            cutting_area_heignt = height - 10

            # Get middle positions
            middle_vertical = bbox.top + (bbox.height / 2)
            middle_horizontal = bbox.left + (bbox.width / 2)

            # Cropmark Information
            self.add_cropmark_settings_text(bbox.right, bbox.bottom, dx, dy, width, height, str(middle_horizontal), str(bbox.bottom + 20), layer)
            self.draw_reg_circile(offset_left, offset_top, "Top Left Cropmark", layer)
            self.draw_reg_circile(offset_left, offset_bottom, "Bottom Left Cropmark", layer)
            self.draw_reg_circile(offset_right, offset_bottom, "Bottom Right Cropmark", layer)
            self.draw_reg_circile(offset_right, offset_top, "Top Right Cropmark", layer)

            # Drawing manual alignment marks
            
            top_right_mark = [
                (border_right - mark_size, border_top),  # Start at top-right inner edge
                (border_right - mark_size, border_top + mark_size),             # Horizontal line outward
                (border_right, border_top + mark_size)  # Vertical line downward
            ]

            top_left_mark = [
                (border_left + mark_size, border_top),  # Start at top-left inner edge
                (border_left + mark_size, border_top + mark_size),             # Horizontal line outward
                (border_left, border_top + mark_size)  # Vertical line downward
            ]

            bottom_right_mark = [
                (border_right - mark_size, border_bottom),  # Start at bottom-right inner edge
                (border_right - mark_size , border_bottom - mark_size),             # Horizontal line outward
                (border_right, border_bottom - mark_size)  # Vertical line upward
            ]

            bottom_left_mark = [
                (border_left + mark_size, border_bottom),  # Start at bottom-left inner edge
                (border_left + mark_size, border_bottom - mark_size),             # Horizontal line outward
                (border_left, border_bottom - mark_size)  # Vertical line upward
            ]

            bottom_left_dia_mark = [
                (border_left, border_bottom),
                (border_left + mark_size, border_bottom - mark_size)
            ]
            line_mark_style = "fill:none;stroke:#000000;stroke-width:0.18;stroke-linecap:round;stroke-linejoin:round;stroke-miterlimit:10;stroke-dasharray:none;stroke-opacity:1"
            self.add_open_path(top_right_mark, line_mark_style, layer)
            self.add_open_path(top_left_mark, line_mark_style, layer)
            self.add_open_path(bottom_right_mark, line_mark_style, layer)
            self.add_open_path(bottom_left_mark, line_mark_style, layer)
            self.add_open_path(bottom_left_dia_mark, line_mark_style, layer)

        # Draw helper layer
        if True:
            self.add_helper_layer(cutting_area_x, cutting_area_y, cutting_area_width, cutting_area_heignt)


    def remove_layers(self, *layer_ids):
        """
        Removes layers with specified IDs from the SVG document.

        Args:
            *layer_ids: Arbitrary number of layer IDs to be removed. A maximum of 10 layers is allowed.

        Raises:
            ValueError: If more than 10 layer IDs are provided.
        """
        # Check if the number of layer IDs exceeds the limit
        if len(layer_ids) > 10:
            raise ValueError("Cannot remove more than 10 layers at once.")

        # Iterate over the provided layer IDs
        for layer_id in layer_ids:
            # Find the layer by its ID
            layer = self.svg.find(f".//*[@id='{layer_id}']")
            if layer is not None:
                # Remove the layer from the SVG document
                self.document.getroot().remove(layer)

    def effect(self):
        # chooses if to take values from presests or user provided
        self.apply_presets()

        pages = self.svg.namedview.get_pages()

        self.remove_layers("cropmarks", "helper")

        # Handle single-page document
        if len(pages) < 2:
            if self.options.page_size != "keep":
                self.apply_resize_page(
                self.svg.viewport_to_unit(str(self.options.new_width) + self.options.unit), 
                self.svg.viewport_to_unit(str(self.options.new_height) + self.options.unit),
                self.options.unit
                )
            self.draw_effect(self.svg.get_page_bbox(), "")
        else:
            raise ValueError("Multiple pages are not supported")



if __name__ == "__main__":
    PrintingMarks().run()