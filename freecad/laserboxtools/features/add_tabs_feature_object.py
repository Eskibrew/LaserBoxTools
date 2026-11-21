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


class LBGenerateTabs:
    def __init__(self, obj, base_link=None):
        '''"Generate Tabs"

        base_link: optional (base_document_object, sub_element_names) to skip GUI selection
        (e.g. programmatic use from Make Box). If None, uses the current selection.
        '''
        obj.Proxy = self
        
        # Restored objects already have their properties. Calling this constructor
        # from the old src.lasertabs proxy only rebinds the proxy.
        if hasattr(obj, "baseObject"):
            laserhelper.lbApplyAutofillCountMode(obj, "TabCount", 1, False)
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
        if not hasattr(obj, 'TabCount'):
            obj.addProperty("App::PropertyInteger","TabCount","Parameters", "Tab Count").TabCount = 0
        if not hasattr(obj, 'TabWidth'):
            obj.addProperty("App::PropertyLength","TabWidth","Parameters", "Tab Width").TabWidth = 10.0
        if not hasattr(obj, 'TabDepth'):
            obj.addProperty("App::PropertyLength","TabDepth","Parameters", "Tab Depth").TabDepth = 3.0
        if not hasattr(obj, 'GapWidth'):
            obj.addProperty("App::PropertyLength","GapWidth","Parameters", "Gap Width").GapWidth = 10.0
        if not hasattr(obj, 'Refine'):
            obj.addProperty("App::PropertyBool","Refine","ParametersExt", "Use Refine").Refine = True
        if not hasattr(obj, 'TabMode'):
            obj.addProperty("App::PropertyEnumeration", "TabMode", "Parameters", "Where to start tabs").TabMode = ["From One End", "From Both Ends", "From Middle"]
        if not hasattr(obj, 'SwapEnds'):
            obj.addProperty("App::PropertyBool","SwapEnds","Parameters", "Swap Ends").SwapEnds = False
        if not hasattr(obj, 'TabTaper'):
            obj.addProperty("App::PropertyLength","TabTaper","Parameters", "Tab Taper Angle").TabTaper = 0.0
        if not hasattr(obj, 'Margin1'):
            obj.addProperty("App::PropertyLength","Margin1","Parameters", "Margin 1").Margin1 = 0.0
        if not hasattr(obj, 'Margin2'):
            obj.addProperty("App::PropertyLength","Margin2","Parameters", "Margin 2").Margin2 = 0.0
        if not hasattr(obj, 'TabHookDepth'):
            obj.addProperty("App::PropertyLength","TabHookDepth","Parameters", "Tab Hook Depth").TabHookDepth = 0.0
        if not hasattr(obj, 'TabHookLength'):
            obj.addProperty("App::PropertyLength","TabHookLength","Parameters", "Tab Hook Length").TabHookLength = 0.0
        if not hasattr(obj, 'TabHookRadius'):
            obj.addProperty("App::PropertyLength","TabHookRadius","Parameters", "Tab Hook Radius").TabHookRadius = 0.0
        if not hasattr(obj, 'SwapHookDirection'):
            obj.addProperty("App::PropertyBool","SwapHookDirection","Parameters", "Swap Hook Direction").SwapHookDirection = False
        if not hasattr(obj, 'Kerf'):
            obj.addProperty("App::PropertyLength","Kerf","Parameters", "Laser kerf (full beam width). Tabs are widened by kerf/2 on each side to compensate.").Kerf = 0.0
        if not hasattr(obj, 'Autofill'):
            #_msg("Adding Autofill property since it doesn't exist\n")
            obj.addProperty("App::PropertyBool","Autofill","Parameters", "Autofill").Autofill = True
        else:
            #_msg("Autofill property already exists\n")
            if obj.Autofill and obj.TabCount == 0:
                #_msg("Autofill is checked, setting TabCount to 0\n")
                obj.TabCount = 0
        laserhelper.lbApplyAutofillCountMode(obj, "TabCount", 1, False)

    def onDocumentRestored(self, obj: App.DocumentObject) -> None:
        """Re-apply the Data-pane lock after the saved properties are loaded."""
        laserhelper.lbApplyAutofillCountMode(obj, "TabCount", 1, False)

    def onChanged(self, obj: App.DocumentObject, prop: str) -> None:
        """Gray Tab Count while Autofill is checked, and keep that count at 0.

        The task panel prepares its spin box before assigning Autofill. This
        still covers edits made from the property view.
        """
        if prop != "Autofill" or laserhelper.lbObjectIsRestoring(obj):
            return
        laserhelper.lbApplyAutofillCountMode(obj, "TabCount", 1, True)

    def execute(self, obj: App.DocumentObject) -> None:
        '''"Print a short message when doing a recomputation, this method is mandatory" '''
        #App.Console.PrintMessage("Recompute Add Tabs feature\n")

        # pass selected object shape
        Main_Object = obj.baseObject[0].Shape.copy()
        face = obj.baseObject[1]

        s = laserhelper.lbCreateTabs(tabCount = obj.TabCount, tabWidth = obj.TabWidth.Value, gapWidth = obj.GapWidth.Value,
                        tabDepth = obj.TabDepth.Value, mode = obj.TabMode, swapends = obj.SwapEnds, tabTaper = obj.TabTaper.Value,
                        margin1 = obj.Margin1.Value, margin2 = obj.Margin2.Value,
                        tabHookDepth = obj.TabHookDepth.Value, tabHookLength = obj.TabHookLength.Value, tabHookRadius = obj.TabHookRadius.Value,
                        swapHookDirection = obj.SwapHookDirection,
                        subtraction = False, refine = obj.Refine, selFaceNames = face, selObject = Main_Object,
                        kerf = obj.Kerf.Value)
        obj.baseObject[0].ViewObject.Visibility = False
        obj.Shape = s
