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

def _install_living_hinge_view_provider(vobj, kind):
    from freecad.laserboxtools.features.living_hinge_feature_vp import (
        LBLivingHingeViewProviderFlat,
        LBLivingHingeViewProviderTree,
    )
    if kind == "Tree":
        LBLivingHingeViewProviderTree(vobj)
    else:
        LBLivingHingeViewProviderFlat(vobj)

class LBGenerateLivingHinge:
    def onDocumentRestored(self, obj):

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

        # We don't need to remove any properties

        # src.laserlivinghinge is a top-level module, so a relative import cannot see freecad/.
        from freecad.laserboxtools.features.living_hinge_feature_object import LBGenerateLivingHinge as LBGenerateLivingHingeNew

        LBGenerateLivingHingeNew(obj)
        _wrn("New proxy class used; properties migrated\n")

        if App.GuiUp and getattr(obj, "ViewObject", None) is not None:
            # PartDesign features were given the flat provider; Part features the tree provider.
            kind = "Flat" if obj.isDerivedFrom("PartDesign::Feature") else "Tree"
            _install_living_hinge_view_provider(obj.ViewObject, kind)

class LBLivingHingeViewProviderTree:
    def attach(self, vobj):
        _install_living_hinge_view_provider(vobj, "Tree")

class LBLivingHingeViewProviderFlat:
    def attach(self, vobj):
        _install_living_hinge_view_provider(vobj, "Flat")