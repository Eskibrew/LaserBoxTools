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

import FreeCAD as App
_wrn = App.Console.PrintWarning

#we have restructured the workbench to the new proxy class structure, so when opening files from older versions we need to migrate the properties to the new class

def _install_tabs_view_provider(vobj, kind):
    from freecad.laserboxtools.features.add_tabs_feature_vp import (
        LBTabsViewProviderFlat,
        LBTabsViewProviderTree,
    )
    if kind == "Tree":
        LBTabsViewProviderTree(vobj)
    else:
        LBTabsViewProviderFlat(vobj)

class LBGenerateTabs:
    def onDocumentRestored(self, obj):

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

        # We don't need to remove any properties

        # src.lasertabs is a top-level module, so a relative import cannot see freecad/.
        from freecad.laserboxtools.features.add_tabs_feature_object import LBGenerateTabs as LBGenerateTabsNew

        LBGenerateTabsNew(obj)
        _wrn("New proxy class used; properties migrated\n")

        if App.GuiUp and getattr(obj, "ViewObject", None) is not None:
            # PartDesign features were given the flat provider; Part features the tree provider.
            kind = "Flat" if obj.isDerivedFrom("PartDesign::Feature") else "Tree"
            _install_tabs_view_provider(obj.ViewObject, kind)

class LBTabsViewProviderTree:
    def attach(self, vobj):
        _install_tabs_view_provider(vobj, "Tree")

class LBTabsViewProviderFlat:
    def attach(self, vobj):
        _install_tabs_view_provider(vobj, "Flat")