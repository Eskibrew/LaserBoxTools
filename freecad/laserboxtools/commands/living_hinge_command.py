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

## Problems
###1) Prevent slots on a curved surface (or make them work)

from typing import ClassVar

import FreeCAD as App
import Part
translate = App.Qt.translate

from ..resources import Resources
from ..features.living_hinge_feature_object import LBGenerateLivingHinge
from ..features.living_hinge_feature_vp import LBLivingHingeViewProviderTree, LBLivingHingeViewProviderFlat
from ..gui.living_hinge_task_panels import LBLivingHingeTaskPanel
from ..src import laser_helper as laserhelper


class LBLivingHingeCommand:
    """LBSlots command add living hinge to a face"""

    # Good practice (optional): set a constant for your command name, it is used in several places.
    Name: ClassVar[str] = "LBLivingHinge"

    def __init__(self) -> None:
        # Optional: initialize instance variables that persist for the command's lifetime
        pass

    def GetResources(self) -> dict[str, str]:
        # Returns a dictionary that defines how the command appears in the UI.
        # - Pixmap: path to the icon file (relative to FreeCAD's icon search paths or absolute path)
        # - MenuText: text shown in menus (use translate for translation support)
        # - ToolTip: text shown when hovering over the button/menu item
        # - Accel: optional keyboard shortcut (e.g., "Ctrl+A")
        return {
            "Pixmap": Resources.icon(
                "livinghinge.svg"
            ),
            "MenuText": translate(
                "Laser Box Tools",
                "Add living hinge to face",
            ),
            "ToolTip": translate(
                "Laser Box Tools",
                "Add living hinge to face",
            ),
        }

    def Activated(self) -> None:
        # Called when the user triggers the command (clicks the toolbar button,
        # selects the menu item, or runs FreeCADGui.runCommand()).
        # Place the main logic of your command here.
        #App.Console.PrintMessage("LBLivingHinge Command activated\n")

        doc = App.ActiveDocument
        view = App.Gui.ActiveDocument.ActiveView
        activeBody = None
        selobj = App.Gui.Selection.getSelectionEx()[0].Object
        
        if hasattr(view,'getActiveObject'):
            activeBody = view.getActiveObject('pdbody')
        
        if not laserhelper.lbIsOperationLegal(activeBody, selobj):
            return
        
        doc.openTransaction("LivingHinge")
        
        if activeBody is None or not laserhelper.lbIsPartDesign(selobj):
            a = doc.addObject("Part::FeaturePython","LivingHinge")
            cls = LBGenerateLivingHinge(a)
            LBLivingHingeViewProviderTree(a.ViewObject)
            a.AutoUpdate = True
            cls.execute(a)
        else:
            a = doc.addObject("PartDesign::FeaturePython","LivingHinge")
            cls = LBGenerateLivingHinge(a)
            LBLivingHingeViewProviderFlat(a.ViewObject)
            a.AutoUpdate = True
            activeBody.addObject(a)
            cls.execute(a)
        
        panel = LBLivingHingeTaskPanel(False)
        panel.obj = a
        panel.update()
        App.Gui.Control.showDialog(panel)
        return

    def IsActive(self) -> bool:
        # Called frequently by FreeCAD to determine if the command should be
        # enabled (True) or greyed out/disabled (False).
        # If a face is selected, the command is active.
        if len(App.Gui.Selection.getSelection()) < 1 or len(App.Gui.Selection.getSelectionEx()[0].SubElementNames) < 1:
            return False
        selobj = App.Gui.Selection.getSelection()[0]
        if selobj.isDerivedFrom("Sketcher::SketchObject"):
            return False
        for selFace in App.Gui.Selection.getSelectionEx()[0].SubObjects:
            if type(selFace) == Part.Vertex :
                return False
            if type(selFace) == Part.Edge :
                return False
        return True

    @classmethod
    def Install(cls) -> None:
        # Optional utility method to register the command
        if App.GuiUp:
            App.Gui.addCommand(cls.Name, cls())
