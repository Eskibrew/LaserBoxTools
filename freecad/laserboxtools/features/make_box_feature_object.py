# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2022 EskiBrew                                           *
# *                                                                         *
# *   This file is part of LaserBoxTools module.                            *
# *   LaserBoxTools module is free software; you can redistribute it and/or *
# *   modify it under the terms of the GNU Lesser General Public            *
# *   License as published by the Free Software Foundation; either          *
# *   version 2.1 of the License, or (at your option) any later version.    *
# *                                                                         *
# *   This module is distributed in the hope that it will be useful,        *
# *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
# *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU     *
# *   Lesser General Public License for more details.                       *
# *                                                                         *
# *   You should have received a copy of the GNU Lesser General Public      *
# *   License along with this library; if not, write to the Free Software   *
# *   Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,            *
# *   MA  02110-1301  USA                                                   *
# *                                                                         *
# ***************************************************************************

from __future__ import annotations

import FreeCAD as App
#import os, Part, Sketcher

from ..gui.make_box_task_panels import LaserMakeBoxTaskPanel
from ..src import laser_helper as laserhelper


class MakeBox:
    """MakeBox feature object to create a laser cut box with or without tabs"""

    def __init__(self, obj: App.DocumentObject) -> None:
        obj.Proxy = self
        obj.addProperty("App::PropertyLength", "BoxLength", "Dimensions").BoxLength = 200.0
        obj.addProperty("App::PropertyLength", "BoxWidth", "Dimensions").BoxWidth = 100.0
        obj.addProperty("App::PropertyLength", "BoxHeight", "Dimensions").BoxHeight = 50.0
        obj.addProperty("App::PropertyLength", "BoxThickness", "Dimensions").BoxThickness = 3.0
        obj.addProperty("App::PropertyInteger", "TabSlotCount", "TabsAndSlots").TabSlotCount = 0
        obj.addProperty("App::PropertyBool", "Autofill", "TabsAndSlots", "Fill each edge with as many tabs and slots as will fit").Autofill = True
        obj.addProperty("App::PropertyLength", "TabSlotWidth", "TabsAndSlots").TabSlotWidth = 10.0
        obj.addProperty("App::PropertyLength", "GapWidth", "TabsAndSlots").GapWidth = 10.0
        obj.addProperty("App::PropertyLength", "TabTaper", "TabsAndSlots").TabTaper = 0.0
        obj.addProperty("App::PropertyLength", "Kerf", "TabsAndSlots", "Laser kerf (beam width): tabs widened and slots narrowed by kerf/2 per side").Kerf = 0.0
        laserhelper.lbApplyAutofillCountMode(obj, "TabSlotCount", 1, False)
        obj.ViewObject.Visibility = False

    def onDocumentRestored(self, obj: App.DocumentObject) -> None:
        """Re-apply the Data-pane lock after the saved properties are loaded."""
        laserhelper.lbApplyAutofillCountMode(obj, "TabSlotCount", 1, False)

    def onChanged(self, obj: App.DocumentObject, prop: str) -> None:
        """Gray Tab/Slot Count while Autofill is checked, and keep that count at 0.

        The task panel prepares its spin box before assigning Autofill. This
        still covers edits made from the property view.
        """
        if prop != "Autofill" or laserhelper.lbObjectIsRestoring(obj):
            return
        laserhelper.lbApplyAutofillCountMode(obj, "TabSlotCount", 1, True)

    def execute(self, obj: App.DocumentObject) -> None:
        """Do something when doing a recomputation, this method is mandatory"""
        ##import Part
        #App.Console.PrintMessage("Recompute Python Box feature\n")
        ##obj.Shape = Part.makeBox(obj.Length, obj.Width, obj.Height)

    @classmethod
    def create(cls, name: str | None = None, doc: App.Document | None = None) -> MakeBox:
        """Optional utility method to create instances of this feature"""
        #App.Console.PrintMessage("Create TheBox Feature Object\n")

        # Check valid document
        if not (doc := doc or App.ActiveDocument):
            raise ValueError("A FreeCAD document is required")

        # Create the c++ DocumentObject
        # see: https://wiki.freecad.org/App_FeaturePython
        obj = doc.addObject("App::FeaturePython", name or "TheBox")

        # Bind the Python Proxy
        proxy = cls(obj)

        # Manage Gui (ViewProvider) if available
        # Actually, I don't think the box needs a ViewProvider
        if App.GuiUp and hasattr(obj, "ViewObject"):
            from .make_box_feature_vp import MakeBoxViewProvider
            MakeBoxViewProvider(obj.ViewObject)

        # Show the task panel
        panel = LaserMakeBoxTaskPanel(obj)
        App.Gui.Control.showDialog(panel)

        obj.recompute()
        return proxy