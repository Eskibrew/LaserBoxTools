# SPDX-License-Identifier: LGPL-2.1-or-later

"""Laser Box Tools FreeCAD Workbench."""

import FreeCAD as App
import FreeCADGui as Gui

translate = App.Qt.translate

from .resources import Resources
from .commands import LBMakeBoxCommand
from .commands import LBTabsCommand
from .commands import LBSlotsCommand
from .commands import LBLivingHingeCommand

class LaserBoxToolsWorkbench(Gui.Workbench):

    MenuText: str = translate(
            "Laser Box Tools",
            "Laser Box Tools",
        )

    ToolTip: str = translate(
            "Laser Box Tools",
            "Tools for making laser cut boxes",
        )

    Icon: str = Resources.icon("LBLogo-wb.svg")


    def Initialize(self) -> None:
        App.Console.PrintMessage("Laser Box Tools Workbench initialized\n")
        # Adding menus and toolbars when the Workbench is active
        commands = [LBMakeBoxCommand.Name, LBTabsCommand.Name, LBSlotsCommand.Name, LBLivingHingeCommand.Name]
        self.appendToolbar("Laser Box Tools", commands)
        self.appendMenu("Laser Box Tools", commands)

    def Activated(self) -> None:
        App.Console.PrintMessage("Laser Box Tools Workbench activated\n")

    def Deactivated(self) -> None:
        App.Console.PrintMessage("Laser Box Tools Workbench deactivated\n")

    def ContextMenu(self, recipient: str) -> None:
        App.Console.PrintMessage("Laser Box Tools Workbench context menu\n")
        # Adding context menus when the Workbench is active
        self.appendContextMenu("", [LBMakeBoxCommand.Name, LBTabsCommand.Name, LBSlotsCommand.Name, LBLivingHingeCommand.Name])

    @classmethod
    def Install(cls) -> None:
        Gui.addWorkbench(cls)
