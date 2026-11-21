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

from . import laser_helper as laserhelper
from ..features.add_slots_feature_object import LBGenerateSlots
from ..features.add_slots_feature_vp import LBSlotsViewProviderFlat, LBSlotsViewProviderTree


def LBCreateSlotsFeature(doc, link_obj, face_names, slot_count, slot_width, slot_depth, gap_width, slot_mode, margin1, margin2, offset_from_face, refine=True, plate_for_name=None, kerf=0.0, autofill=False):
    """Create a parametric Slots feature linked to link_obj (no GUI selection).

    link_obj: object for baseObject (PartDesign: Body.Tip — not the Body). plate_for_name: optional
    for unique Name/Label when link_obj is Tip.

    PartDesign::FeaturePython + flat view when link_obj belongs to a PartDesign::Body; otherwise
    Part::FeaturePython + tree view (same split as LBSlots command).

    Returns the new Slots object, or None if slots were skipped (no faces or zero depth).
    """
    if slot_depth <= 0 or not face_names:
        return None

    #uniq = plate_for_name.Name if plate_for_name is not None else link_obj.Name
    #name = doc.getUniqueObjectName("Slots_" + uniq)
    name = doc.getUniqueObjectName("Slots")
    pd_body = laserhelper.lbPartDesignBodyContaining(link_obj)

    if pd_body is not None:
        a = doc.addObject("PartDesign::FeaturePython", name)
    else:
        a = doc.addObject("Part::FeaturePython", name)
    cls = LBGenerateSlots(a, base_link=(link_obj, tuple(face_names)))

    if pd_body is not None:
        LBSlotsViewProviderFlat(a.ViewObject)
    else:
        LBSlotsViewProviderTree(a.ViewObject)

    # Autofill is assigned first. Turning it on sets SlotCount to 0 and grays it
    # in the Data pane; turning it off sets SlotCount to 1. The requested count
    # is applied after that, so unlock the property before writing it.
    a.Autofill = bool(autofill)
    a.setEditorMode("SlotCount", 0)
    a.SlotCount = slot_count
    if a.Autofill:
        a.setEditorMode("SlotCount", 1)
    a.SlotLength = float(slot_width)
    a.SlotDepth = float(slot_depth)
    a.GapWidth = float(gap_width)
    a.SlotMode = slot_mode
    a.Margin1 = float(margin1)
    a.Margin2 = float(margin2)
    a.SwapEnds = False
    a.Refine = refine
    a.SlotHookLength = 0.0
    a.SwapHookDirection = False
    a.OffsetFromFace = float(offset_from_face)
    a.Kerf = float(kerf)
    #label_src = plate_for_name if plate_for_name is not None else link_obj
    #a.Label = "Slots ({})".format(label_src.Label)
    a.Label = "Slots"
    if pd_body is not None:
        pd_body.addObject(a)
    cls.execute(a)
    a.AutoUpdate = True
    return a