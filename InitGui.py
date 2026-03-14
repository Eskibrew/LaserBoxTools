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

from PySide import QtCore
import FreeCAD as App
#from FreeCAD import Gui
import os
import laser_boxes_locator

laser_boxes_path = os.path.dirname(laser_boxes_locator.__file__)
lb_icons_path = os.path.join(laser_boxes_path, 'Resources', 'icons')
main_laser_boxes_icon = os.path.join(lb_icons_path, 'LBLogo.svg')

class LaserBoxesWorkbench (Workbench):
    global main_laser_boxes_icon
    global lb_icons_path

    MenuText = 'Laser Boxes ' + 'V0.1.0'
    ToolTip = 'Tools for making laser cut boxes'
    Icon = main_laser_boxes_icon
    
#     """
# /* XPM */
# static char * icon_xpm[] = {
# "21 21 9 1",
# " 	c None",
# ".	c #000000",
# "+	c #202220",
# "@	c #FF0801",
# "#	c #444643",
# "$	c #FF6664",
# "%	c #9C9E9B",
# "&	c #FFA0A1",
# "*	c #FFFFFF",
# "                     ",
# "                     ",
# "          .          ",
# "          ..         ",
# "         .#.         ",
# "        .#*#.        ",
# "        .%**.        ",
# "       +#***#.       ",
# "       .*****+       ",
# "      .%*****%.      ",
# "     .+*******+.     ",
# "     .%**&@$**%.     ",
# "    .#**$@@@@**#.    ",
# "    .%**@@@@@&**.    ",
# "   .%***@@@@@***%.   ",
# "   .****&@@@$****.   ",
# "  .%******&&*****%.  ",
# " .+***************#. ",
# " .++##+#+####+###++. ",
# " ................... ",
# "                     "};
# """ 

    def Initialize(self):
        "This function is executed when the workbench is first activated"
        from src import lasermakebox, lasertabs, laserslots, laserlivinghinge

        self.list = ["LBBasicBox", "LBTabs", "LBSlots", "LBLivingHinge"]
        self.appendToolbar("Laser Boxes", self.list)
        self.appendMenu("Laser Boxes", self.list)
        FreeCADGui.addIconPath(lb_icons_path)
 
    def Activated(self):
        "This function is executed when the workbench is activated"
        return
 
    def Deactivated(self):
        "This function is executed when the workbench is deactivated"
        return
 
    def ContextMenu(self, recipient):
        "This is executed whenever the user right-clicks on screen"
        self.appendContextMenu("Laser Boxes", self.list) # add commands to the context menu
 
    def GetClassName(self):
        "this function is mandatory if this is a full python workbench"
        return "Gui::PythonWorkbench"
 
Gui.addWorkbench(LaserBoxesWorkbench())