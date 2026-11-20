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


class LBGenerateLivingHinge:
    def __init__(self, obj):
        '''"Generate Living Hinge" '''

        obj.Proxy = self

        # # Restored objects already have their properties. Calling this constructor
        # # from the old src.lasertabs proxy only rebinds the proxy.
        # if hasattr(obj, "baseObject"):
        #     return

        selection = App.Gui.Selection.getSelectionEx()
        selobj = selection[0] if selection else None
        # obj.baseObject = (selobj.Object, selobj.SubElementNames)

        # if not hasattr(obj, 'baseObject'):
        #     obj.addProperty("App::PropertyLinkSub", "baseObject", "Parameters", "Base Object")

        # if base_link is not None:
        #     bo, sub = base_link
        #     obj.baseObject = (bo, tuple(sub))
        # else:
        #     selobj = App.Gui.Selection.getSelectionEx()[0]
        #     obj.baseObject = (selobj.Object, selobj.SubElementNames)

        if not hasattr(obj, 'AutoUpdate'):
            obj.addProperty("App::PropertyBool","AutoUpdate","ParametersExt", "Auto Update").AutoUpdate = False
        if not hasattr(obj, 'ElementCount'):
            obj.addProperty("App::PropertyInteger","ElementCount","Parameters", "Element Count").ElementCount = 4
        if not hasattr(obj, 'ElementWidth'):
            obj.addProperty("App::PropertyLength","ElementWidth","Parameters", "Element Width").ElementWidth = 0.1
        if not hasattr(obj, 'ElementDepth'):
            obj.addProperty("App::PropertyLength","ElementDepth","Parameters", "Element Depth").ElementDepth = 0.0
        if not hasattr(obj, 'ElementSpacing'):
            obj.addProperty("App::PropertyLength","ElementSpacing","Parameters", "Element Spacing").ElementSpacing = 1.0
        if not hasattr(obj, 'baseObject'):
            obj.addProperty("App::PropertyLinkSub", "baseObject", "Parameters", "Base Object")
            if selobj is not None:
                obj.baseObject = (selobj.Object, selobj.SubElementNames)
        if not hasattr(obj, 'Refine'):
            obj.addProperty("App::PropertyBool","Refine","ParametersExt", "Use Refine (slower but cleaner result)").Refine = False
        if not hasattr(obj, 'ElementMode'):
            obj.addProperty("App::PropertyEnumeration", "ElementMode", "Parameters", "Where to start hinge elements").ElementMode = ["From One End", "From Both Ends", "From Middle"]
        if not hasattr(obj, 'SwapEnds'):
            obj.addProperty("App::PropertyBool","SwapEnds","Parameters", "Swap Ends").SwapEnds = False
        if not hasattr(obj, 'Margin1'):
            obj.addProperty("App::PropertyLength","Margin1","Parameters", "Margin1").Margin1 = 0.0
        if not hasattr(obj, 'Margin2'):
            obj.addProperty("App::PropertyLength","Margin2","Parameters", "Margin2").Margin2 = 0.0
        if not hasattr(obj, 'ElementType'):
            obj.addProperty("App::PropertyEnumeration", "ElementType", "Parameters", "What shape are the hinge elements").ElementType = ["Straight"]

    # def onChanged(self, obj: App.DocumentObject, prop: str) -> None:
    #     """Do something when a property has changed"""
    #     App.Console.PrintMessage("Change property: " + str(prop) + "\n")

    def execute(self, obj: App.DocumentObject) -> None:
        '''"Print a short message when doing a recomputation, this method is mandatory" '''
        #App.Console.PrintMessage("Recompute Living Hinge feature\n")
        
        # pass selected object shape
        Main_Object = obj.baseObject[0].Shape.copy()
        face = obj.baseObject[1]

        s = laserhelper.lbCreateLivingHinge(elementCount = obj.ElementCount, elementWidth = obj.ElementWidth.Value, elementDepth = obj.ElementDepth.Value, elementSpacing = obj.ElementSpacing.Value, elementMode = obj.ElementMode, elementType = obj.ElementType, swapends = obj.SwapEnds, margin1 = obj.Margin1.Value, margin2 = obj.Margin2.Value, subtraction = False, refine = obj.Refine, selFaceNames = face, selObject = Main_Object)
        obj.baseObject[0].ViewObject.Visibility = False
        obj.Shape = s
