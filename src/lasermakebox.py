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

from FreeCAD import Gui
import FreeCAD
import FreeCADGui
import Part
import Sketcher
import os
from PySide import QtCore, QtGui

from src.lasertabs import LBCreateTabsFeature
from src.laserslots import LBCreateSlotsFeature

__dir__ = os.path.dirname(__file__)
icons = os.path.join(__dir__, '../Resources/icons')
path_to_ui = os.path.join(__dir__, '../dialogs/basicbox.ui')


def laser_face_names_two_largest_joint_faces_per_axis(shape, thickness, axis, tol=None):
    """Pick two opposing narrow joint faces (normals ±axis) on each side of the shape midpoint.

    axis: ``'X'`` (left/right) or ``'Y'`` (front/back on a horizontal plate). After booleans, many
    small faces can qualify; we keep the largest-area face per side of the bounding-box center.
    """
    if axis not in ('X', 'Y'):
        raise ValueError("axis must be 'X' or 'Y'")

    candidates = laser_face_names_for_tab_slot_faces_filtered_by_axes(shape, thickness, (axis,), tol)

    if not candidates:
        return []

    if len(candidates) <= 2:
        return candidates

    bb = shape.BoundBox
    mid = bb.Center.x if axis == 'X' else bb.Center.y
    neg_side = []
    pos_side = []

    for name in candidates:
        face = shape.getElement(name)

        try:
            area = float(face.Area)
        except Exception:
            area = 0.0

        c = face.CenterOfMass.x if axis == 'X' else face.CenterOfMass.y

        if c < mid:
            neg_side.append((area, name))
        else:
            pos_side.append((area, name))

    neg_side.sort(key=lambda t: -t[0])
    pos_side.sort(key=lambda t: -t[0])
    out = []

    if neg_side:
        out.append(neg_side[0][1])

    if pos_side:
        out.append(pos_side[0][1])

    if len(out) >= 2:
        return out[:2]

    ranked = []

    for name in candidates:
        face = shape.getElement(name)

        try:
            ranked.append((float(face.Area), name))
        except Exception:
            ranked.append((0.0, name))

    ranked.sort(key=lambda t: -t[0])

    if len(ranked) >= 2:
        return [ranked[0][1], ranked[1][1]]

    return [ranked[0][1]] if ranked else []


def laser_face_names_for_front_back_slots_on_tabbed_shape(shape, thickness, tol=None):
    """Pick the two left/right joint faces (world ±X) on a tabbed front/back panel.

    After tabs, ``filtered_by_axes(..., ('X',))`` can match dozens of small tab faces. The real
    left/right slots belong on the two large vertical strips: we take the largest-area qualifying
    face on each side of the solid's X midpoint.
    """
    return laser_face_names_two_largest_joint_faces_per_axis(shape, thickness, 'X', tol)


def laser_get_origin_plane(body, plane_role):
    """Get the plane object from body.Origin by Role (e.g. 'XY_Plane', 'YZ_Plane', 'XZ_Plane')."""
    # Method 1: Search OriginFeatures by Role (most reliable)
    if hasattr(body.Origin, 'OriginFeatures'):
        for obj in body.Origin.OriginFeatures:
            if hasattr(obj, 'Role') and obj.Role == plane_role:
                return obj
    # Method 2: Direct attribute (e.g. body.Origin.XY_Plane)
    plane_obj = getattr(body.Origin, plane_role, None)

    if plane_obj is not None:
        return plane_obj

    # Method 3: getSubObject with path (e.g. Origin.XY_Plane)
    plane_obj = body.getSubObject('Origin.' + plane_role)
    return plane_obj


def laser_make_box_piece(x, y, thickness, offset, plane_role, name): 
    body = FreeCAD.ActiveDocument.addObject('PartDesign::Body', name)
    sketch = body.newObject('Sketcher::SketchObject','Sketch')

    # Get the correct plane from the body's Origin by Role
    plane_obj = laser_get_origin_plane(body, plane_role)

    if plane_obj is None:
        raise ValueError("Could not find plane '{}' in body Origin".format(plane_role))

    sketch.AttachmentSupport = [(plane_obj, '')]
    sketch.MapMode = 'FlatFace'

    # Offset along the plane's normal (local Z)
    sketch.AttachmentOffset = FreeCAD.Placement(FreeCAD.Vector(0.000, 0.000, offset), FreeCAD.Rotation(FreeCAD.Vector(0.000, 0.000, 1.000), 0.000))

    geoList = []
    geoList.append(Part.LineSegment(FreeCAD.Vector(-x / 2, y / 2, 0), FreeCAD.Vector(x / 2, y / 2, 0)))
    geoList.append(Part.LineSegment(FreeCAD.Vector(x / 2, y / 2, 0), FreeCAD.Vector(x / 2, -y / 2, 0)))
    geoList.append(Part.LineSegment(FreeCAD.Vector(x / 2, -y / 2, 0), FreeCAD.Vector(-x / 2, -y / 2, 0)))
    geoList.append(Part.LineSegment(FreeCAD.Vector(-x / 2, -y / 2, 0), FreeCAD.Vector(-x / 2, y / 2, 0)))
    sketch.addGeometry(geoList, False)

    conList = []
    conList.append(Sketcher.Constraint('Coincident',0,2,1,1))
    conList.append(Sketcher.Constraint('Coincident',1,2,2,1))
    conList.append(Sketcher.Constraint('Coincident',2,2,3,1))
    conList.append(Sketcher.Constraint('Coincident',3,2,0,1))
    conList.append(Sketcher.Constraint('Horizontal',0))
    conList.append(Sketcher.Constraint('Horizontal',2))
    conList.append(Sketcher.Constraint('Vertical',1))
    conList.append(Sketcher.Constraint('Vertical',3))
    sketch.addConstraint(conList)

    pad = body.newObject('PartDesign::Pad','Pad')
    pad.Profile = sketch
    pad.Length = thickness
    pad.ReferenceAxis = (sketch,['N_Axis'])
    sketch.Visibility = False
    return body


def laser_make_box_piece_simple(name, length, width, height, position):
    """Create a Part::Feature box with given dimensions and position (corner at minimum coords)."""
    box_shape = Part.makeBox(length, width, height, position)
    obj = FreeCAD.ActiveDocument.addObject("Part::Feature", name)
    obj.Shape = box_shape
    return obj


def laser_face_names_for_tab_slot_faces(shape, thickness, tol=None):
    """Face names where the shortest edge on the face matches stock thickness (narrow edge / joint faces).

    Works for Part.makeBox solids and PartDesign pads (after the body has been recomputed).
    """
    if tol is None:
        tol = max(0.05, abs(thickness) * 0.02)

    names = []

    if shape is None or shape.isNull():
        return names

    for i, face in enumerate(shape.Faces, start=1):
        if not face.Edges:
            continue

        min_len = min(abs(e.Length) for e in face.Edges)

        if abs(min_len - thickness) <= tol:
            names.append('Face{}'.format(i))

    return names


def laser_face_normal_world(face):
    """Unit normal for a face (world coordinates).

    Avoids Surface.parameter(CenterOfMass): on some kernels it can hang or be very slow.
    Box/planar joint faces work with normalAt in the face parameter domain.
    """
    try:
        n = face.normalAt(0, 0)
    except Exception:
        try:
            n = face.normalAt(0.5, 0.5)
        except Exception:
            return FreeCAD.Vector(1, 0, 0)
    if n.Length < 1e-10:
        return FreeCAD.Vector(1, 0, 0)
    return n.normalize()


def laser_face_names_for_tab_slot_faces_filtered_by_axes(shape, thickness, world_axes, tol=None):
    """Like laser_face_names_for_tab_slot_faces, but only faces whose normal is parallel to a world axis.

    world_axes: iterable of 'X', 'Y', and/or 'Z' (e.g. ('Z',) for top+bottom edges, ('X',) for left+right).
    """
    if not world_axes:
        return laser_face_names_for_tab_slot_faces(shape, thickness, tol)

    axis_vecs = {
        'X': FreeCAD.Vector(1, 0, 0),
        'Y': FreeCAD.Vector(0, 1, 0),
        'Z': FreeCAD.Vector(0, 0, 1),
    }

    wanted = [axis_vecs[a] for a in world_axes if a in axis_vecs]

    if not wanted:
        return laser_face_names_for_tab_slot_faces(shape, thickness, tol)

    candidates = laser_face_names_for_tab_slot_faces(shape, thickness, tol)

    if not candidates:
        return []

    names = []
    parallel_tol = 0.06  # |n·axis| ≈ 1 for planar joint faces

    for name in candidates:
        face = shape.getElement(name)
        n = laser_face_normal_world(face)

        for w in wanted:
            if abs(abs(n.dot(w)) - 1.0) < parallel_tol:
                names.append(name)
                break

    return names


def laser_recompute_partdesign_body_for_tip(doc, body):
    """Ensure the PartDesign body Tip has a valid shape for face picking.

    Uses a **scoped** recompute (this body only) when the FreeCAD version supports it. A full
    ``doc.recompute()`` recomputes every object in the document; during Basic Box with tabs/slots,
    that was called once per panel and dominated runtime as the model grew.
    """
    if doc is None or body is None:
        return

    r = getattr(doc, "recompute", None)

    if r is None:
        return

    try:
        r([body])
    except TypeError:
        r()


def laser_link_target_and_shape_for_face_pick(part_obj):
    """Resolve link target and Shape for Face1.. enumeration and Tabs/Slots baseObject.

    PartDesign::FeaturePython links must target a sibling feature (e.g. Body.Tip / Pad), not the
    Body container — otherwise PartDesign reports 'Out of scope' and face references fail.

    For Part::Feature, returns the part itself. Does not run doc.recompute() for plain Part
    features (avoids AutoUpdate loops with FeaturePython view providers).
    """
    if part_obj is None:
        return None, None

    if part_obj.isDerivedFrom('PartDesign::Body'):
        doc = part_obj.Document

        if doc is not None:
            laser_recompute_partdesign_body_for_tip(doc, part_obj)

        tip = getattr(part_obj, 'Tip', None)

        if tip is not None:
            return tip, tip.Shape

        return part_obj, part_obj.Shape

    return part_obj, part_obj.Shape


def laser_add_piece_to_basic_box_group(group, piece_obj, feature_added):
    """Put a box panel under Basic Box Group.

    Part + Tabs/Slots: the parametric feature is added to the group (nested tree); skip the base solid.
    PartDesign: Tabs/Slots are inside the Body timeline, not the group — always add the Body so the group is not empty.
    """
    if piece_obj is None:
        return

    if not feature_added or piece_obj.isDerivedFrom('PartDesign::Body'):
        group.addObject(piece_obj)


def laser_add_tabs_feature_to_group(group, part_obj, thickness, tab_slot_count, tab_slot_width, tab_taper, gap_width, tab_mode, margin1, margin2, face_names=None):
    """Create a parametric Tabs feature (same as command LBTabs).

    PartDesign::Body: Tabs go inside the body (flat tree). Part::Feature: Tabs are added to the group
    and the tree view nests the base under Tabs (claimChildren).

    Returns True if Tabs were created (caller should not also add part_obj to the group when successful).
    """
    link_obj, shape = laser_link_target_and_shape_for_face_pick(part_obj)

    if face_names is None:
        face_names = laser_face_names_for_tab_slot_faces(shape, thickness)

    if not face_names:
        FreeCAD.Console.PrintWarning("LaserMakeBox: No tab faces found for '{}'; shortest edge should match material thickness. Skipping tabs.\n".format(part_obj.Label))
        return False

    doc = part_obj.Document
    plate_for_name = part_obj if part_obj.isDerivedFrom('PartDesign::Body') else None

    tabs = LBCreateTabsFeature(
        doc, link_obj, face_names,
        tab_slot_count, tab_slot_width, thickness, gap_width, tab_mode, tab_taper, margin1, margin2, refine=True,
        plate_for_name=plate_for_name,
    )

    if tabs is not None:
        # PartDesign::Body: Tabs are already in the body (flat timeline). Part: nest under group only.
        if not part_obj.isDerivedFrom('PartDesign::Body'):
            group.addObject(tabs)
        return True

    return False


def laser_add_slots_feature_to_group(group, part_obj, thickness, tab_slot_count, tab_slot_width, gap_width, slot_mode, margin1, margin2, face_names=None):
    """Create a parametric Slots feature (same as command LBSlots) and add it to the group when using Part.

    Returns True if a Slots object was created and added (caller should not also add part_obj to the group).
    """
    link_obj, shape = laser_link_target_and_shape_for_face_pick(part_obj)
    if face_names is None:
        face_names = laser_face_names_for_tab_slot_faces(shape, thickness)

    if not face_names:
        FreeCAD.Console.PrintWarning("LaserMakeBox: No slot faces found for '{}'; shortest edge should match material thickness. Skipping slots.\n".format(part_obj.Label))
        return False

    doc = part_obj.Document
    plate_for_name = part_obj if part_obj.isDerivedFrom('PartDesign::Body') else None

    slots = LBCreateSlotsFeature(
        doc, link_obj, face_names,
        tab_slot_count, tab_slot_width, thickness, gap_width, slot_mode, margin1, margin2, 0.0, refine=True,
        plate_for_name=plate_for_name,
    )

    if slots is not None:
        if not part_obj.isDerivedFrom('PartDesign::Body'):
            group.addObject(slots)

        return True

    return False


def laser_add_front_back_tabs_then_slots_to_group(group, plate_obj, thickness, tab_slot_count, tab_slot_width, tab_taper, gap_width, tab_slot_mode, margin1, margin2):
    """Front/Back panels: Tabs on top and bottom edges (world ±Z), then Slots on left and right (world ±X).

    Slots are applied to the *tabbed* solid (second feature links to the Tabs object) so both appear on one part.
    For Part workflow, only the final Slots object is added to the group (nested tree). For PartDesign, Tabs
    and Slots are appended inside the plate Body (flat timeline).

    Do not call doc.recompute() between Tabs and Slots: a full-document recompute here can interact with
    ViewProvider updateData (AutoUpdate) and cause a recompute loop. tabs_f.Shape is valid immediately after
    LBCreateTabsFeature (execute already ran).
    """
    doc = plate_obj.Document
    link_obj, shape = laser_link_target_and_shape_for_face_pick(plate_obj)
    face_tabs = laser_face_names_for_tab_slot_faces_filtered_by_axes(shape, thickness, ('Z',))

    if not face_tabs:
        FreeCAD.Console.PrintWarning("LaserMakeBox: No tab faces (±Z) for '{}'; skipping front/back tab/slot chain.\n".format(plate_obj.Label))
        return False

    plate_for_name = plate_obj if plate_obj.isDerivedFrom('PartDesign::Body') else None

    tabs_f = LBCreateTabsFeature(
        doc, link_obj, face_tabs,
        tab_slot_count, tab_slot_width, thickness, gap_width, tab_slot_mode, tab_taper, margin1, margin2, refine=True,
        plate_for_name=plate_for_name,
    )

    if tabs_f is None:
        return False

    face_slots = laser_face_names_for_front_back_slots_on_tabbed_shape(tabs_f.Shape, thickness)

    if not face_slots:
        FreeCAD.Console.PrintWarning("LaserMakeBox: No slot faces (±X) after tabs for '{}' — tabs only.\n".format(plate_obj.Label))

        if not plate_obj.isDerivedFrom('PartDesign::Body'):
            group.addObject(tabs_f)

        return True

    slots_f = LBCreateSlotsFeature(
        doc, tabs_f, face_slots,
        tab_slot_count, tab_slot_width, thickness, gap_width, tab_slot_mode, margin1, margin2, 0.0, refine=True
    )

    if slots_f is None:
        if not plate_obj.isDerivedFrom('PartDesign::Body'):
            group.addObject(tabs_f)
        return True

    if not plate_obj.isDerivedFrom('PartDesign::Body'):
        group.addObject(slots_f)
    return True


def laser_add_top_bottom_dual_slots_to_group(group, plate_obj, thickness, tab_slot_count, tab_slot_width, gap_width, tab_slot_mode, margin1, margin2):
    """Top/Bottom plates: slots on front/back edges (world ±Y), then ±X with margin1 = margin2 = thickness.

    The second slot feature links to the first (same pattern as front/back tabs then slots). No full
    document recompute between steps.
    """
    doc = plate_obj.Document
    link_obj, shape = laser_link_target_and_shape_for_face_pick(plate_obj)
    face_fb = laser_face_names_two_largest_joint_faces_per_axis(shape, thickness, 'Y')

    if not face_fb:
        FreeCAD.Console.PrintWarning(
            "LaserMakeBox: No slot faces (±Y / front-back) for '{}'; skipping top/bottom slot chain.\n".format(plate_obj.Label)
        )
        return False

    plate_for_name = plate_obj if plate_obj.isDerivedFrom('PartDesign::Body') else None
    slots_first = LBCreateSlotsFeature(
        doc, link_obj, face_fb,
        tab_slot_count, tab_slot_width, thickness, gap_width, tab_slot_mode, margin1, margin2, 0.0, refine=True,
        plate_for_name=plate_for_name,
    )

    if slots_first is None:
        return False

    face_lr = laser_face_names_two_largest_joint_faces_per_axis(slots_first.Shape, thickness, 'X')

    if not face_lr:
        FreeCAD.Console.PrintWarning(
            "LaserMakeBox: No slot faces (±X / left-right) after first slots for '{}' — first slot pass only.\n".format(plate_obj.Label)
        )
        if not plate_obj.isDerivedFrom('PartDesign::Body'):
            group.addObject(slots_first)
        return True

    mt = float(thickness)
    slots_second = LBCreateSlotsFeature(
        doc, slots_first, face_lr,
        tab_slot_count, tab_slot_width, thickness, gap_width, tab_slot_mode, mt, mt, 0.0, refine=True,
        plate_for_name=plate_for_name,
    )

    if slots_second is None:
        if not plate_obj.isDerivedFrom('PartDesign::Body'):
            group.addObject(slots_first)
        return True

    if not plate_obj.isDerivedFrom('PartDesign::Body'):
        group.addObject(slots_second)
    return True


def laser_make_box_pieces_simple(length, width, height, thickness, top, bottom, left, right, front, back, use_tabs_and_slots, tab_slot_count, tab_slot_width, tab_taper, gap_width, tab_slot_mode, margin1, margin2):
    """Create box using Part workbench (Part::Feature objects, no sketches)."""
    group = FreeCAD.ActiveDocument.addObject("App::DocumentObjectGroup", "Basic Box Group")

    # Bottom: length x width, at z = -height/2
    if bottom:
        bottom = laser_make_box_piece_simple(
            "Bottom",
            length, width, thickness,
            FreeCAD.Vector(-length / 2, -width / 2, -height / 2)
        )
        feature_added = False
        if use_tabs_and_slots:
            feature_added = laser_add_top_bottom_dual_slots_to_group(
                group, bottom, thickness,
                tab_slot_count, tab_slot_width, gap_width, tab_slot_mode, margin1, margin2
            )
        laser_add_piece_to_basic_box_group(group, bottom, feature_added)

    # Top: length x width, at z = height/2 - thickness
    if top:
        top = laser_make_box_piece_simple(
            "Top",
            length, width, thickness,
            FreeCAD.Vector(-length / 2, -width / 2, height / 2 - thickness)
        )
        feature_added = False
        if use_tabs_and_slots:
            feature_added = laser_add_top_bottom_dual_slots_to_group(
                group, top, thickness,
                tab_slot_count, tab_slot_width, gap_width, tab_slot_mode, margin1, margin2
            )
        laser_add_piece_to_basic_box_group(group, top, feature_added)

    # Left: thickness x (width - 2*thickness) x (height - 2*thickness), at x = -length/2
    if left:
        left = laser_make_box_piece_simple(
            "Left",
            thickness, width - 2 * thickness, height - 2 * thickness,
            FreeCAD.Vector(-length / 2, -width / 2 + thickness, -height / 2 + thickness)
        )

        feature_added = False
        if use_tabs_and_slots:
            feature_added = laser_add_tabs_feature_to_group(
                group, left, thickness,
                tab_slot_count, tab_slot_width, tab_taper, gap_width, tab_slot_mode, margin1, margin2
            )
        laser_add_piece_to_basic_box_group(group, left, feature_added)

    # Right: at x = length/2 - thickness
    if right:
        right = laser_make_box_piece_simple(
            "Right",
            thickness, width - 2 * thickness, height - 2 * thickness,
            FreeCAD.Vector(length / 2 - thickness, -width / 2 + thickness, -height / 2 + thickness)
        )
        feature_added = False
        if use_tabs_and_slots:
            feature_added = laser_add_tabs_feature_to_group(
                group, right, thickness,
                tab_slot_count, tab_slot_width, tab_taper, gap_width, tab_slot_mode, margin1, margin2
            )
        laser_add_piece_to_basic_box_group(group, right, feature_added)

    # Front: tabs on top/bottom (±Z), slots on left/right (±X); slots run on the tabbed solid
    if front:
        front = laser_make_box_piece_simple(
            "Front",
            length, thickness, height - 2 * thickness,
            FreeCAD.Vector(-length / 2, width / 2 - thickness, -height / 2 + thickness)
        )
        feature_added = False
        if use_tabs_and_slots:
            feature_added = laser_add_front_back_tabs_then_slots_to_group(
                group, front, thickness,
                tab_slot_count, tab_slot_width, tab_taper, gap_width, tab_slot_mode, margin1, margin2
            )
        laser_add_piece_to_basic_box_group(group, front, feature_added)

    # Back: same edge roles as Front (world ±Z tabs, ±X slots)
    if back:
        back = laser_make_box_piece_simple(
            "Back",
            length, thickness, height - 2 * thickness,
            FreeCAD.Vector(-length / 2, -width / 2, -height / 2 + thickness)
        )
        feature_added = False
        if use_tabs_and_slots:
            feature_added = laser_add_front_back_tabs_then_slots_to_group(
                group, back, thickness,
                tab_slot_count, tab_slot_width, tab_taper, gap_width, tab_slot_mode, margin1, margin2
            )
        laser_add_piece_to_basic_box_group(group, back, feature_added)

    FreeCAD.ActiveDocument.recompute()
    return group


def laser_make_box_pieces(length, width, height, thickness, top, bottom, left, right, front, back, use_tabs_and_slots, tab_slot_count, tab_slot_width, tab_taper, gap_width, tab_slot_mode, margin1, margin2):
    """Create box using PartDesign workbench (bodies, sketches, pads)."""
    group = FreeCAD.ActiveDocument.addObject("App::DocumentObjectGroup", "Basic Box Group")

    if bottom:
        bottom = laser_make_box_piece(length, width, thickness, -height / 2, 'XY_Plane', 'BodyBottom')
        feature_added = False
        if use_tabs_and_slots:
            feature_added = laser_add_top_bottom_dual_slots_to_group(
                group, bottom, thickness,
                tab_slot_count, tab_slot_width, gap_width, tab_slot_mode, margin1, margin2
            )
        laser_add_piece_to_basic_box_group(group, bottom, feature_added)

    if top:
        top = laser_make_box_piece(length, width, thickness, (height / 2) - thickness, 'XY_Plane', 'BodyTop')
        feature_added = False
        if use_tabs_and_slots:
            feature_added = laser_add_top_bottom_dual_slots_to_group(
                group, top, thickness,
                tab_slot_count, tab_slot_width, gap_width, tab_slot_mode, margin1, margin2
            )
        laser_add_piece_to_basic_box_group(group, top, feature_added)

    if left:
        left = laser_make_box_piece(width - thickness * 2, height - thickness * 2, thickness, -length / 2, 'YZ_Plane', 'BodyLeft')
        feature_added = False
        if use_tabs_and_slots:
            feature_added = laser_add_tabs_feature_to_group(
                group, left, thickness,
                tab_slot_count, tab_slot_width, tab_taper, gap_width, tab_slot_mode, margin1, margin2
            )
        laser_add_piece_to_basic_box_group(group, left, feature_added)

    if right:
        right = laser_make_box_piece(width - thickness * 2, height - thickness * 2, thickness, (length / 2) - thickness, 'YZ_Plane', 'BodyRight')
        feature_added = False
        if use_tabs_and_slots:
            feature_added = laser_add_tabs_feature_to_group(
                group, right, thickness,
                tab_slot_count, tab_slot_width, tab_taper, gap_width, tab_slot_mode, margin1, margin2
            )
        laser_add_piece_to_basic_box_group(group, right, feature_added)

    if front:
        front = laser_make_box_piece(length, height - thickness * 2, thickness, (width / 2) - thickness, 'XZ_Plane', 'BodyFront')
        feature_added = False
        if use_tabs_and_slots:
            feature_added = laser_add_front_back_tabs_then_slots_to_group(
                group, front, thickness,
                tab_slot_count, tab_slot_width, tab_taper, gap_width, tab_slot_mode, margin1, margin2
            )
        laser_add_piece_to_basic_box_group(group, front, feature_added)

    if back:
        back = laser_make_box_piece(length, height - thickness * 2, thickness, -width / 2, 'XZ_Plane', 'BodyBack')
        feature_added = False
        if use_tabs_and_slots:
            feature_added = laser_add_front_back_tabs_then_slots_to_group(
                group, back, thickness,
                tab_slot_count, tab_slot_width, tab_taper, gap_width, tab_slot_mode, margin1, margin2
            )
        laser_add_piece_to_basic_box_group(group, back, feature_added)

    FreeCAD.ActiveDocument.recompute()
    return group

def error_message(msg):
    diag = QtGui.QMessageBox(QtGui.QMessageBox.Warning, 'Error', msg)
    diag.setWindowModality(QtCore.Qt.ApplicationModal)
    diag.exec_()


class LaserMakeBoxTaskPanel:
    def __init__(self):
        # this will create a Qt widget from our ui file
        self.form = FreeCADGui.PySideUic.loadUi(path_to_ui)
        self.form.BoxLength.setValue(200)
        self.form.BoxWidth.setValue(100)
        self.form.BoxHeight.setValue(50)
        self.form.BoxThickness.setValue(3)
        self.form.rbPartDesign.setChecked(True)
        self.form.cbTop.setChecked(True)
        self.form.cbBottom.setChecked(True)
        self.form.cbLeft.setChecked(True)
        self.form.cbRight.setChecked(True)
        self.form.cbFront.setChecked(True)
        self.form.cbBack.setChecked(True)
        self.form.cbUseTabsAndSlots.setChecked(False)


    def accept(self):
        length = self.form.BoxLength.value()
        width = self.form.BoxWidth.value()
        height = self.form.BoxHeight.value()
        thickness = self.form.BoxThickness.value()

        if length == 0:
            error_message('length cannot be zero!')
            return

        if width == 0:
            error_message('width cannot be zero!')
            return

        if height == 0:
            error_message('height cannot be zero!')
            return

        if thickness == 0:
            error_message('thickness cannot be zero!')
            return

        if not self.form.cbTop.isChecked() and not self.form.cbBottom.isChecked() and not self.form.cbLeft.isChecked() and not self.form.cbRight.isChecked() and not self.form.cbFront.isChecked() and not self.form.cbBack.isChecked():
            error_message('At least one box part must be selected!')
            return

        if self.form.rbPart.isChecked():
            laser_make_box_pieces_simple(length, width, height, thickness,
                                        self.form.cbTop.isChecked(),
                                        self.form.cbBottom.isChecked(),
                                        self.form.cbLeft.isChecked(),
                                        self.form.cbRight.isChecked(),
                                        self.form.cbFront.isChecked(),
                                        self.form.cbBack.isChecked(),
                                        self.form.cbUseTabsAndSlots.isChecked(),
                                        self.form.TabSlotCount.value(),
                                        self.form.TabSlotWidth.value(),
                                        self.form.TabTaper.value(),
                                        self.form.GapWidth.value(),
                                        "From Middle",
                                        0,
                                        0
                                        )
        else:
            laser_make_box_pieces(length, width, height, thickness,
                                        self.form.cbTop.isChecked(),
                                        self.form.cbBottom.isChecked(),
                                        self.form.cbLeft.isChecked(),
                                        self.form.cbRight.isChecked(),
                                        self.form.cbFront.isChecked(),
                                        self.form.cbBack.isChecked(),
                                        self.form.cbUseTabsAndSlots.isChecked(),
                                        self.form.TabSlotCount.value(),
                                        self.form.TabSlotWidth.value(),
                                        self.form.TabTaper.value(),
                                        self.form.GapWidth.value(),
                                        "From Middle",
                                        0,
                                        0
                                        )
        FreeCADGui.Control.closeDialog()


class LaserMakeBox:

    def __init__(self):
        return

    def GetResources(self):
        return {'Pixmap': os.path.join(icons, 'box.svg'),
                'MenuText': "Make a basic box",
                'ToolTip': "Make a basic box, without tabs"}

    def IsActive(self):
        return FreeCAD.ActiveDocument is not None

    def Activated(self):
        panel = LaserMakeBoxTaskPanel()
        FreeCADGui.Control.showDialog(panel)
        #vp = ViewProviderGroupBox(groupBox.ViewObject)
        #vp.setEdit(ViewProviderGroupBox)
        return


Gui.addCommand('LBBasicBox', LaserMakeBox())
