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

from . import laser_helper as laserhelper
from ..features.add_tabs_feature_object import LBGenerateTabs
from ..features.add_tabs_feature_vp import LBTabsViewProviderFlat, LBTabsViewProviderTree


def LBCreateTabsFeature(doc, link_obj, face_names, tab_count, tab_width, tab_depth, gap_width, tab_mode, tab_taper, margin1, margin2, refine=True, plate_for_name=None, kerf=0.0):
    """Create a parametric Tabs feature linked to link_obj (no GUI selection).

    link_obj: object for baseObject / FaceN refs (PartDesign: Body.Tip, e.g. Pad — not the Body).
    plate_for_name: optional; used for unique Name/Label when link_obj is Tip but the plate is a Body.

    PartDesign::FeaturePython + flat view when link_obj lies in a PartDesign::Body; Part::FeaturePython
    + tree view for Part workbench.

    Returns the new Tabs object, or None if tabs were skipped (no faces or zero depth).
    """
    if tab_depth <= 0 or not face_names:
        return None

    #uniq = plate_for_name.Name if plate_for_name is not None else link_obj.Name
    #App.Console.PrintMessage("LBCreateTabsFeature: uniq = " + uniq + "\n")
    #name = doc.getUniqueObjectName("Tabs_" + uniq)
    name = doc.getUniqueObjectName("Tabs")
    #App.Console.PrintMessage("LBCreateTabsFeature: name = " + name + "\n")
    pd_body = laserhelper.lbPartDesignBodyContaining(link_obj)
    #App.Console.PrintMessage("LBCreateTabsFeature: pd_body = " + str(pd_body) + "\n")

    if pd_body is not None:
        a = doc.addObject("PartDesign::FeaturePython", name)
    else:
        a = doc.addObject("Part::FeaturePython", name)
    
    cls = LBGenerateTabs(a, base_link=(link_obj, tuple(face_names)))

    if pd_body is not None:
        LBTabsViewProviderFlat(a.ViewObject)
    else:
        LBTabsViewProviderTree(a.ViewObject)

    a.TabCount = tab_count
    a.TabWidth = float(tab_width)
    a.TabDepth = float(tab_depth)
    a.GapWidth = float(gap_width)
    a.TabMode = tab_mode
    a.TabTaper = float(tab_taper)
    a.Margin1 = float(margin1)
    a.Margin2 = float(margin2)
    a.SwapEnds = False
    a.Refine = refine
    a.TabHookDepth = 0.0
    a.TabHookLength = 0.0
    a.TabHookRadius = 0.0
    a.SwapHookDirection = False
    a.Kerf = float(kerf)
    #label_src = plate_for_name if plate_for_name is not None else link_obj
    #a.Label = "Tabs ({})".format(label_src.Label)
    a.Label = "Tabs"
    if pd_body is not None:
        pd_body.addObject(a)
    cls.execute(a)
    a.AutoUpdate = True
    return a