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

def _install_slots_view_provider(vobj, kind):
    from freecad.laserboxtools.features.add_slots_feature_vp import (
        LBSlotsViewProviderFlat,
        LBSlotsViewProviderTree,
    )
    if kind == "Tree":
        LBSlotsViewProviderTree(vobj)
    else:
        LBSlotsViewProviderFlat(vobj)

class LBGenerateSlots:
    def onDocumentRestored(self, obj):

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
            obj.addProperty("App::PropertyLength","Margin1","Parameters", "Margin 1").Margin1 = 0.0

        if not hasattr(obj, 'Margin2'):
            obj.addProperty("App::PropertyLength","Margin2","Parameters", "Margin 2").Margin2 = 0.0

        if not hasattr(obj, 'SlotHookLength'):
            obj.addProperty("App::PropertyLength","SlotHookLength","Parameters", "Slot Hook Depth").SlotHookLength = 0.0

        if not hasattr(obj, 'SwapHookDirection'):
            obj.addProperty("App::PropertyBool","SwapHookDirection","Parameters", "Swap Hook Direction").SwapHookDirection = False

        if not hasattr(obj, 'OffsetFromFace'):
            obj.addProperty("App::PropertyLength","OffsetFromFace","Parameters", "Slot Offset from face").OffsetFromFace = 0.0

        if not hasattr(obj, 'Kerf'):
            obj.addProperty("App::PropertyLength","Kerf","Parameters", "Laser kerf (full beam width). Slots are narrowed by kerf/2 on each side to compensate.").Kerf = 0.0

        # We don't need to remove any properties

        # src.laserslots is a top-level module, so a relative import cannot see freecad/.
        from freecad.laserboxtools.features.add_slots_feature_object import LBGenerateSlots as LBGenerateSlotsNew

        LBGenerateSlotsNew(obj)
        _wrn("New proxy class used; properties migrated\n")

        if App.GuiUp and getattr(obj, "ViewObject", None) is not None:
            # PartDesign features were given the flat provider; Part features the tree provider.
            kind = "Flat" if obj.isDerivedFrom("PartDesign::Feature") else "Tree"
            _install_slots_view_provider(obj.ViewObject, kind)

class LBSlotsViewProviderTree:
    def attach(self, vobj):
        _install_slots_view_provider(vobj, "Tree")

class LBSlotsViewProviderFlat:
    def attach(self, vobj):
        _install_slots_view_provider(vobj, "Flat")