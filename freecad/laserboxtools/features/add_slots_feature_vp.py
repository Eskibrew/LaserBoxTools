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

"""
see: https://wiki.freecad.org/Scripted_objects
"""

from __future__ import annotations
from ..resources import Resources

import FreeCAD as App

from ..src import laser_helper as laserhelper
from ..gui.add_slots_task_panels import LBSlotsTaskPanel

_LB_SLOTS_AUTOUPDATE_PROPS = (
    "Autofill", "SlotDepth", "SlotLength", "GapWidth", "SlotCount", "Refine", "SlotMode",
    "Margin1", "Margin2", "OffsetFromFace", "baseObject", "SwapEnds",
    "SlotHookLength", "SwapHookDirection", "Kerf",
)

class LBSlotsViewProviderTree:
    "A View provider that nests children objects under the created one, like Part"

    def __init__(self, vobj):
        vobj.Proxy = self
        self.Object = vobj.Object

    def attach(self, vobj):
        self.Object = vobj.Object
        return

    def setupContextMenu(self, viewObject, menu):
        action = menu.addAction(App.Qt.translate("QObject", "Edit %1").replace("%1", viewObject.Object.Label))
        action.triggered.connect(lambda: self.startDefaultEditMode(viewObject))
        return False

    def startDefaultEditMode(self, viewObject):
        document = viewObject.Document.Document
        if not document.HasPendingTransaction:
            text = App.Qt.translate("QObject", "Edit %1").replace("%1", viewObject.Object.Label)
            document.openTransaction(text)
        viewObject.Document.setEdit(viewObject.Object, 0)

    def updateData(self, fp, prop):
        '''If a property of the handled feature has changed we have the chance to handle this here'''
        laserhelper.lbAutoRecomputeOnProperty(fp, prop, _LB_SLOTS_AUTOUPDATE_PROPS)
        return

    def getDisplayModes(self, vobj):
        modes=[]
        return modes

    def setDisplayMode(self,mode):
        return mode

    def __getstate__(self):
        return None

    def __setstate__(self,state):
        if state is not None:
            doc = App.ActiveDocument
            self.Object = doc.getObject(state['ObjectName'])

    def claimChildren(self):
        objs = []
        if hasattr(self.Object,"baseObject"):
            objs.append(self.Object.baseObject[0])
        if hasattr(self.Object,"Sketch"):
            objs.append(self.Object.Sketch)
        return objs
    
    def getIcon(self):
        return Resources.icon("slots.svg")

    def setEdit(self, vobj, mode):
        if (mode != 0):
            return False #we only handle the detault mode

        laserhelper.lbActivateWorkbench()
        taskd = LBSlotsTaskPanel(True)
        taskd.obj = vobj.Object
        self.Object.AutoUpdate = False
        taskd.update()
        self.Object.AutoUpdate = True
        App.Gui.Control.showDialog(taskd)
        return True

    def unsetEdit(self, vobj, mode):
        if (mode != 0):
            return False #we only handle the detault mode
            
        App.Gui.Control.closeDialog()
        return False


class LBSlotsViewProviderFlat:
    "A View provider that places objects flat under base object, like PartDesign"

    def __init__(self, obj):
        obj.Proxy = self
        self.Object = obj.Object

    def attach(self, obj):
        self.Object = obj.Object
        return

    def updateData(self, fp, prop):
        '''If a property of the handled feature has changed we have the chance to handle this here'''
        laserhelper.lbAutoRecomputeOnProperty(fp, prop, _LB_SLOTS_AUTOUPDATE_PROPS)
        return

    def getDisplayModes(self,obj):
        modes=[]
        return modes

    def setDisplayMode(self,mode):
        return mode

    def __getstate__(self):
        return None

    def __setstate__(self,state):
        if state is not None:
            doc = App.ActiveDocument
            self.Object = doc.getObject(state['ObjectName'])

    def claimChildren(self):
        objs = []
        if hasattr(self.Object,"Sketch"):
            objs.append(self.Object.Sketch)
        return objs
    
    def getIcon(self):
        return Resources.icon("slots.svg")

    def setEdit(self,vobj,mode):
        if (mode != 0):
            return False #we only handle the detault mode

        laserhelper.lbActivateWorkbench()
        #laserhelper.laser_ensure_new_slot_properties_exist(vobj.Object)
        taskd = LBSlotsTaskPanel(True)
        taskd.obj = vobj.Object
        self.Object.AutoUpdate = False
        taskd.update()
        self.Object.AutoUpdate = True
        App.Gui.Control.showDialog(taskd)
        return True

    def unsetEdit(self,vobj,mode):
        if (mode != 0):
            return False #we only handle the detault mode
            
        App.Gui.Control.closeDialog()
        return False
