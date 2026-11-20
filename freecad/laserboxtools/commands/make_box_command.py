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

"""LBMakeBox Command"""

from typing import ClassVar

import FreeCAD as App
translate = App.Qt.translate

from ..resources import Resources


class LBMakeBoxCommand:
    """LBMakeBox command creates a laser cut box with or without tabs"""

    # Good practice (optional): set a constant for your command name, it is used in several places.
    Name: ClassVar[str] = "LBMakeBox"

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
                "box.svg"
            ),
            "MenuText": translate(
                "Laser Box Tools",
                "Make a box",
            ),
            "ToolTip": translate(
                "Laser Box Tools",
                "Make a box, with or without tabs",
            ),
        }

    def Activated(self) -> None:
        # Called when the user triggers the command (clicks the toolbar button,
        # selects the menu item, or runs FreeCADGui.runCommand()).
        # Place the main logic of your command here.
        App.Console.PrintMessage("LBMakeBox Command activated\n")

        from ..features import MakeBox
        # Create a new document if no document is open
        doc = App.ActiveDocument or App.newDocument()
        MakeBox.create("TheBox", doc)
        return

    def IsActive(self) -> bool:
        # Called frequently by FreeCAD to determine if the command should be
        # enabled (True) or greyed out/disabled (False).
        # Use this to check for conditions like: active document exists,
        # objects are selected, workbench is in correct state, etc.
        return True

    @classmethod
    def Install(cls) -> None:
        # Optional utility method to register the command
        if App.GuiUp:
            App.Gui.addCommand(cls.Name, cls())
