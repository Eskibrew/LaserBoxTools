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

from ..src import laser_helper as laserhelper


class LBGenerateSlots:
    def __init__(self, obj, base_link=None):
        '''"Generate Slots"

        base_link: optional (base_document_object, sub_element_names) to skip GUI selection
        (e.g. programmatic use from Make Box). If None, uses the current selection.
        '''
        obj.Proxy = self
        
        # Restored objects already have their properties. Calling this constructor
        # from the old src.lasertabs proxy only rebinds the proxy.
        if hasattr(obj, "baseObject"):
            laserhelper.lbApplyAutofillCountMode(obj, "SlotCount", 1, False)
            return

        if not hasattr(obj, 'baseObject'):
            obj.addProperty("App::PropertyLinkSub", "baseObject", "Parameters", "Base Object")

        if base_link is not None:
            bo, sub = base_link
            obj.baseObject = (bo, tuple(sub))
        else:
            selobj = App.Gui.Selection.getSelectionEx()[0]
            obj.baseObject = (selobj.Object, selobj.SubElementNames)

        if not hasattr(obj, 'AutoUpdate'):
            obj.addProperty("App::PropertyBool","AutoUpdate","ParametersExt", "Auto Update").AutoUpdate = False
        if not hasattr(obj, 'SlotCount'):
            obj.addProperty("App::PropertyInteger","SlotCount","Parameters", "Slot Count").SlotCount = 0
        if not hasattr(obj, 'SlotLength'):
            obj.addProperty("App::PropertyLength","SlotLength","Parameters", "Slot Length").SlotLength = 10.0
        if not hasattr(obj, 'SlotDepth'):
            obj.addProperty("App::PropertyLength","SlotDepth","Parameters", "Slot Depth").SlotDepth = 3.0
        if not hasattr(obj, 'GapWidth'):
            obj.addProperty("App::PropertyLength","GapWidth","Parameters", "Gap Width").GapWidth = 10.0
        if not hasattr(obj, 'Refine'):
            obj.addProperty("App::PropertyBool","Refine","ParametersExt", "Use Refine").Refine = True
        if not hasattr(obj, 'SlotMode'):
            obj.addProperty("App::PropertyEnumeration", "SlotMode", "Parameters", "Where to start slots").SlotMode = ["From One End", "From Both Ends", "From Middle"]
        if not hasattr(obj, 'SwapEnds'):
            obj.addProperty("App::PropertyBool","SwapEnds","Parameters", "Swap Ends").SwapEnds = False
        if not hasattr(obj, 'Margin1'):
            obj.addProperty("App::PropertyLength","Margin1","Parameters", "Slot Margin 1").Margin1 = 0.0
        if not hasattr(obj, 'Margin2'):
            obj.addProperty("App::PropertyLength","Margin2","Parameters", "Slot Margin 2").Margin2 = 0.0
        if not hasattr(obj, 'SlotHookLength'):
            obj.addProperty("App::PropertyLength","SlotHookLength","Parameters", "Slot Hook Depth").SlotHookLength = 0.0
        if not hasattr(obj, 'SwapHookDirection'):
            obj.addProperty("App::PropertyBool","SwapHookDirection","Parameters", "Swap Hook Direction").SwapHookDirection = False
        if not hasattr(obj, 'OffsetFromFace'):
            obj.addProperty("App::PropertyLength","OffsetFromFace","Parameters", "Slot Offset from face").OffsetFromFace = 0.0
        if not hasattr(obj, 'Kerf'):
            obj.addProperty("App::PropertyLength","Kerf","Parameters", "Laser kerf (full beam width). Slots are narrowed by kerf/2 on each side to compensate.").Kerf = 0.0
        if not hasattr(obj, 'Autofill'):
            obj.addProperty("App::PropertyBool","Autofill","Parameters", "Autofill").Autofill = True
        else:
            if obj.Autofill and obj.SlotCount == 0:
                obj.SlotCount = 0
        laserhelper.lbApplyAutofillCountMode(obj, "SlotCount", 1, False)

    def onDocumentRestored(self, obj: App.DocumentObject) -> None:
        """Re-apply the Data-pane lock after the saved properties are loaded."""
        laserhelper.lbApplyAutofillCountMode(obj, "SlotCount", 1, False)

    def onChanged(self, obj: App.DocumentObject, prop: str) -> None:
        """Gray Slot Count while Autofill is checked, and keep that count at 0.

        The task panel prepares its spin box before assigning Autofill. This
        still covers edits made from the property view.
        """
        if prop != "Autofill" or laserhelper.lbObjectIsRestoring(obj):
            return
        laserhelper.lbApplyAutofillCountMode(obj, "SlotCount", 1, True)

    def execute(self, obj: App.DocumentObject) -> None:
        '''"Print a short message when doing a recomputation, this method is mandatory" '''
        #App.Console.PrintMessage("Recompute Add Slots feature\n")

        # pass selected object shape
        Main_Object = obj.baseObject[0].Shape.copy()
        face = obj.baseObject[1]

        s = laserhelper.lbCreateSlots(slotCount = obj.SlotCount, slotLength = obj.SlotLength.Value, gapWidth = obj.GapWidth.Value,
                        slotDepth = obj.SlotDepth.Value, mode = obj.SlotMode, swapends = obj.SwapEnds,
                        margin1 = obj.Margin1.Value, margin2 = obj.Margin2.Value, offsetFromFace = obj.OffsetFromFace.Value,
                        slotHookLength = obj.SlotHookLength.Value, swapHookDirection = obj.SwapHookDirection,
                        subtraction = False, refine = obj.Refine, selFaceNames = face, selObject = Main_Object,
                        kerf = obj.Kerf.Value)
        obj.baseObject[0].ViewObject.Visibility = False
        obj.Shape = s
