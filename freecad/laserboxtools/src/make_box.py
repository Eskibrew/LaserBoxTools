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
import Part, Sketcher

from . import laser_helper as laserhelper
from .create_tabs import LBCreateTabsFeature
from .create_slots import LBCreateSlotsFeature


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
    body = App.ActiveDocument.addObject('PartDesign::Body', name)
    sketch = body.newObject('Sketcher::SketchObject','Sketch')

    # Get the correct plane from the body's Origin by Role
    plane_obj = laser_get_origin_plane(body, plane_role)

    if plane_obj is None:
        raise ValueError("Could not find plane '{}' in body Origin".format(plane_role))

    sketch.AttachmentSupport = [(plane_obj, '')]
    sketch.MapMode = 'FlatFace'

    # Offset along the plane's normal (local Z)
    sketch.AttachmentOffset = App.Placement(App.Vector(0.000, 0.000, offset), App.Rotation(App.Vector(0.000, 0.000, 1.000), 0.000))

    geoList = []
    geoList.append(Part.LineSegment(App.Vector(-x / 2, y / 2, 0), App.Vector(x / 2, y / 2, 0)))
    geoList.append(Part.LineSegment(App.Vector(x / 2, y / 2, 0), App.Vector(x / 2, -y / 2, 0)))
    geoList.append(Part.LineSegment(App.Vector(x / 2, -y / 2, 0), App.Vector(-x / 2, -y / 2, 0)))
    geoList.append(Part.LineSegment(App.Vector(-x / 2, -y / 2, 0), App.Vector(-x / 2, y / 2, 0)))
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
    obj = App.ActiveDocument.addObject("Part::Feature", name)
    obj.Shape = box_shape
    return obj


def laser_face_names_for_tab_slot_faces(shape, thickness, tol=None):
    """Face names where the shortest edge on the face matches stock thickness (narrow edge / joint faces).

    Works for Part.makeBox solids and PartDesign pads (after the body has been recomputed).

    This lists every joint face. Dropping an face because its mating panel is not being built is done
    afterwards by laser_face_names_whose_mate_is_included, once the real edges have been chosen.
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
            return App.Vector(1, 0, 0)
    if n.Length < 1e-10:
        return App.Vector(1, 0, 0)
    return n.normalize()


def laser_face_names_for_tab_slot_faces_filtered_by_axes(shape, thickness, world_axes, tol=None):
    """Like laser_face_names_for_tab_slot_faces, but only faces whose normal is parallel to a world axis.

    world_axes: iterable of 'X', 'Y', and/or 'Z' (e.g. ('Z',) for top+bottom edges, ('X',) for left+right).
    """
    if not world_axes:
        return laser_face_names_for_tab_slot_faces(shape, thickness, tol)

    axis_vecs = {
        'X': App.Vector(1, 0, 0),
        'Y': App.Vector(0, 1, 0),
        'Z': App.Vector(0, 0, 1),
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
    ``doc.recompute()`` recomputes every object in the document; during Make Box with tabs/slots,
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


def laser_mate_panel_for_face(shape, face):
    """Name of the box panel this joint face meets, or None if it does not sit on one side.

    The face is classed by which side of the solid's bounding box it lies on: +Z Top, -Z Bottom,
    -X Left, +X Right, +Y Front, -Y Back. Position is used instead of the face normal so a boolean
    that flips a face (tabs or slots) still drops the edge that meets the missing panel.
    """
    bb = shape.BoundBox
    c = face.CenterOfMass
    center = bb.Center
    best_name = None
    best_ratio = 0.0

    for length, delta, neg_name, pos_name in (
        (bb.XLength, c.x - center.x, 'left', 'right'),
        (bb.YLength, c.y - center.y, 'back', 'front'),
        (bb.ZLength, c.z - center.z, 'bottom', 'top'),
    ):
        half = max(abs(length) * 0.5, 1e-9)
        ratio = abs(delta) / half

        if ratio > best_ratio:
            best_ratio = ratio
            best_name = pos_name if delta > 0.0 else neg_name

    # A joint face lies on the boundary (ratio about 1). Anything nearer the middle is not one edge.
    if best_ratio < 0.5:
        return None

    return best_name


def laser_included_panels(top, bottom, left, right, front, back):
    """Map each box panel to whether it is being built.

    Capture this before the make-box loops rebind those names to the panel objects.
    """
    return {
        'top': bool(top),
        'bottom': bool(bottom),
        'left': bool(left),
        'right': bool(right),
        'front': bool(front),
        'back': bool(back),
    }


def laser_face_names_whose_mate_is_included(shape, face_names, included):
    """Drop joint faces that meet a panel which is not being built.

    included is a mapping from laser_included_panels, or None to keep every face.
    A face that does not sit clearly on one side of the solid is kept.

    Call this after the opposing joint faces have been chosen. Filtering the candidate list
    earlier lets a small slot or tab wall win "largest face on that side" once the real edge
    has been removed.
    """
    if not face_names or included is None:
        return face_names if face_names else []

    kept = []

    for name in face_names:
        mate = laser_mate_panel_for_face(shape, shape.getElement(name))

        if mate is None or included.get(mate, True):
            kept.append(name)

    return kept


def laser_add_piece_to_make_box_group(group, piece_obj, feature_added):
    """Put a box panel under Make Box Group.

    Part + Tabs/Slots: the parametric feature is added to the group (nested tree); skip the base solid.
    PartDesign: Tabs/Slots are inside the Body timeline, not the group — always add the Body so the group is not empty.
    """
    if piece_obj is None:
        return

    if not feature_added or piece_obj.isDerivedFrom('PartDesign::Body'):
        group.addObject(piece_obj)


def laser_add_tabs_feature_to_group(group, part_obj, thickness, tab_slot_count, tab_slot_width, tab_taper, gap_width, tab_mode, margin1, margin2, face_names=None, kerf=0.0, included=None):
    """Create a parametric Tabs feature (same as command LBTabs).

    PartDesign::Body: Tabs go inside the body (flat tree). Part::Feature: Tabs are added to the group
    and the tree view nests the base under Tabs (claimChildren).

    included: optional panel map from laser_included_panels. Faces that meet a panel set to False are left plain.

    Returns True if Tabs were created (caller should not also add part_obj to the group when successful).
    """
    link_obj, shape = laser_link_target_and_shape_for_face_pick(part_obj)

    if face_names is None:
        face_names = laser_face_names_for_tab_slot_faces(shape, thickness)

    detected = face_names
    face_names = laser_face_names_whose_mate_is_included(shape, face_names, included)

    if not face_names:
        if not detected:
            App.Console.PrintWarning("LaserMakeBox: No tab faces found for '{}'; shortest edge should match material thickness. Skipping tabs.\n".format(part_obj.Label))
        return False

    doc = part_obj.Document
    plate_for_name = part_obj if part_obj.isDerivedFrom('PartDesign::Body') else None

    tabs = LBCreateTabsFeature(
        doc, link_obj, face_names,
        tab_slot_count, tab_slot_width, thickness, gap_width, tab_mode, tab_taper, margin1, margin2, refine=True, kerf=kerf,
        plate_for_name=plate_for_name,
    )

    if tabs is not None:
        # PartDesign::Body: Tabs are already in the body (flat timeline). Part: nest under group only.
        if not part_obj.isDerivedFrom('PartDesign::Body'):
            group.addObject(tabs)
        return True

    return False


def laser_add_slots_feature_to_group(group, part_obj, thickness, tab_slot_count, tab_slot_width, gap_width, slot_mode, margin1, margin2, face_names=None, kerf=0.0, included=None):
    """Create a parametric Slots feature (same as command LBSlots) and add it to the group when using Part.

    included: optional panel map from laser_included_panels. Faces that meet a panel set to False are left plain.

    Returns True if a Slots object was created and added (caller should not also add part_obj to the group).
    """
    link_obj, shape = laser_link_target_and_shape_for_face_pick(part_obj)
    if face_names is None:
        face_names = laser_face_names_for_tab_slot_faces(shape, thickness)

    detected = face_names
    face_names = laser_face_names_whose_mate_is_included(shape, face_names, included)

    if not face_names:
        if not detected:
            App.Console.PrintWarning("LaserMakeBox: No slot faces found for '{}'; shortest edge should match material thickness. Skipping slots.\n".format(part_obj.Label))
        return False

    doc = part_obj.Document
    plate_for_name = part_obj if part_obj.isDerivedFrom('PartDesign::Body') else None

    slots = LBCreateSlotsFeature(
        doc, link_obj, face_names,
        tab_slot_count, tab_slot_width, thickness, gap_width, slot_mode, margin1, margin2, 0.0, refine=True, kerf=kerf,
        plate_for_name=plate_for_name,
    )

    if slots is not None:
        if not part_obj.isDerivedFrom('PartDesign::Body'):
            group.addObject(slots)

        return True

    return False


def laser_add_front_back_tabs_then_slots_to_group(group, plate_obj, thickness, tab_slot_count, tab_slot_width, tab_taper, gap_width, tab_slot_mode, margin1, margin2, kerf=0.0, included=None):
    """Front/Back panels: Tabs on top and bottom face (world ±Z), then Slots on left and right faces (world ±X).

    A face that meets a panel which is not being built is left plain. Slots still run when both top and
    bottom tabs are omitted; they are cut on the plain plate. When tabs are present, slots are applied to
    the tabbed solid (second feature links to the Tabs object) so both appear on one part.
    For Part workflow, only the final feature is added to the group (nested tree). For PartDesign, Tabs
    and Slots are appended inside the plate Body (flat timeline).

    Do not call doc.recompute() between Tabs and Slots: a full-document recompute here can interact with
    ViewProvider updateData (AutoUpdate) and cause a recompute loop. tabs_f.Shape is valid immediately after
    LBCreateTabsFeature (execute already ran).
    """
    doc = plate_obj.Document
    link_obj, shape = laser_link_target_and_shape_for_face_pick(plate_obj)
    raw_tabs = laser_face_names_for_tab_slot_faces_filtered_by_axes(shape, thickness, ('Z',))

    if not raw_tabs:
        App.Console.PrintWarning("LaserMakeBox: No tab faces (±Z) for '{}'; skipping front/back tab/slot chain.\n".format(plate_obj.Label))
        return False

    face_tabs = laser_face_names_whose_mate_is_included(shape, raw_tabs, included)
    plate_for_name = plate_obj if plate_obj.isDerivedFrom('PartDesign::Body') else None

    # Tabs reaching a corner lengthen the ±X faces, so size the slots on the nominal (untabbed) panel height
    # to keep them identical to the mating Left/Right tabs.
    slot_count, slot_width, slot_gap = tab_slot_count, tab_slot_width, gap_width
    if tab_slot_mode == "From Middle":
        slot_count, slot_width, slot_gap = laserhelper.lbMiddleResolveParams(
            shape.BoundBox.ZLength - margin1 - margin2, tab_slot_count, tab_slot_width, gap_width
        )

    tabs_f = None
    slot_base = link_obj
    slot_shape = shape

    if face_tabs:
        tabs_f = LBCreateTabsFeature(
            doc, link_obj, face_tabs,
            tab_slot_count, tab_slot_width, thickness, gap_width, tab_slot_mode, tab_taper, margin1, margin2, refine=True, kerf=kerf,
            plate_for_name=plate_for_name,
        )

        if tabs_f is None:
            return False

        slot_base = tabs_f
        slot_shape = tabs_f.Shape

    raw_slots = laser_face_names_for_front_back_slots_on_tabbed_shape(slot_shape, thickness)
    face_slots = laser_face_names_whose_mate_is_included(slot_shape, raw_slots, included)

    if not face_slots:
        if tabs_f is None:
            return False

        if not raw_slots:
            App.Console.PrintWarning("LaserMakeBox: No slot faces (±X) after tabs for '{}' — tabs only.\n".format(plate_obj.Label))

        if not plate_obj.isDerivedFrom('PartDesign::Body'):
            group.addObject(tabs_f)

        return True

    slots_f = LBCreateSlotsFeature(
        doc, slot_base, face_slots,
        slot_count, slot_width, thickness, slot_gap, tab_slot_mode, margin1, margin2, 0.0, refine=True, kerf=kerf
    )

    if slots_f is None:
        if tabs_f is not None and not plate_obj.isDerivedFrom('PartDesign::Body'):
            group.addObject(tabs_f)
        return tabs_f is not None

    if not plate_obj.isDerivedFrom('PartDesign::Body'):
        group.addObject(slots_f)
    return True


def laser_add_top_bottom_dual_slots_to_group(group, plate_obj, thickness, tab_slot_count, tab_slot_width, gap_width, tab_slot_mode, margin1, margin2, kerf=0.0, included=None):
    """Top/Bottom plates: slots on left/right edges (world ±X) with margin1 = margin2 = thickness, then on front/back edges (world ±Y).

    A face that meets a panel which is not being built is left plain. The ±Y pass still runs when both
    left and right slots are omitted; it is cut on the plain plate. The ±X pass runs first when it has
    faces: its thickness margins keep it clear of the corners, so the ±Y faces keep their nominal length.
    (Running ±Y first could notch the corners and shorten the ±X faces, changing the slot layout there.)
    The second slot feature links to the first when the first exists. No full document recompute between steps.
    """
    doc = plate_obj.Document
    link_obj, shape = laser_link_target_and_shape_for_face_pick(plate_obj)
    raw_lr = laser_face_names_two_largest_joint_faces_per_axis(shape, thickness, 'X')

    if not raw_lr:
        App.Console.PrintWarning(
            "LaserMakeBox: No slot faces (±X / left-right) for '{}'; skipping top/bottom slot chain.\n".format(plate_obj.Label)
        )
        return False

    face_lr = laser_face_names_whose_mate_is_included(shape, raw_lr, included)
    plate_for_name = plate_obj if plate_obj.isDerivedFrom('PartDesign::Body') else None
    mt = float(thickness)
    slots_first = None
    second_base = link_obj
    second_shape = shape

    if face_lr:
        slots_first = LBCreateSlotsFeature(
            doc, link_obj, face_lr,
            tab_slot_count, tab_slot_width, thickness, gap_width, tab_slot_mode, mt, mt, 0.0, refine=True, kerf=kerf,
            plate_for_name=plate_for_name,
        )

        if slots_first is None:
            return False

        second_base = slots_first
        second_shape = slots_first.Shape

    raw_fb = laser_face_names_two_largest_joint_faces_per_axis(second_shape, thickness, 'Y')
    face_fb = laser_face_names_whose_mate_is_included(second_shape, raw_fb, included)

    if not face_fb:
        if slots_first is None:
            return False

        if not raw_fb:
            App.Console.PrintWarning(
                "LaserMakeBox: No slot faces (±Y / front-back) after first slots for '{}' — first slot pass only.\n".format(plate_obj.Label)
            )

        if not plate_obj.isDerivedFrom('PartDesign::Body'):
            group.addObject(slots_first)
        return True

    slots_second = LBCreateSlotsFeature(
        doc, second_base, face_fb,
        tab_slot_count, tab_slot_width, thickness, gap_width, tab_slot_mode, margin1, margin2, 0.0, refine=True, kerf=kerf,
        plate_for_name=plate_for_name,
    )

    if slots_second is None:
        if slots_first is not None and not plate_obj.isDerivedFrom('PartDesign::Body'):
            group.addObject(slots_first)
        return slots_first is not None

    if not plate_obj.isDerivedFrom('PartDesign::Body'):
        group.addObject(slots_second)
    return True


def laser_make_box_pieces_simple(length, width, height, thickness, top, bottom, left, right, front, back, use_tabs_and_slots, tab_slot_count, tab_slot_width, tab_taper, gap_width, tab_slot_mode, margin1, margin2, kerf=0.0):
    """Create box using Part workbench (Part::Feature objects, no sketches)."""
    group = App.ActiveDocument.addObject("App::DocumentObjectGroup", "Make Box Group")
    # Record a dict of which panels are being built (True/False) so we can skip slots/tabs for panels that are not being built
    included = laser_included_panels(top, bottom, left, right, front, back)

    # Bottom: length x width, at z = -height/2
    if bottom:
        bottom = laser_make_box_piece_simple(
            "Bottom",
            length, width, thickness,
            App.Vector(-length / 2, -width / 2, -height / 2)
        )
        feature_added = False
        if use_tabs_and_slots:
            feature_added = laser_add_top_bottom_dual_slots_to_group(
                group, bottom, thickness,
                tab_slot_count, tab_slot_width, gap_width, tab_slot_mode, margin1, margin2, kerf=kerf, included=included
            )
        laser_add_piece_to_make_box_group(group, bottom, feature_added)

    # Top: length x width, at z = height/2 - thickness
    if top:
        top = laser_make_box_piece_simple(
            "Top",
            length, width, thickness,
            App.Vector(-length / 2, -width / 2, height / 2 - thickness)
        )
        feature_added = False
        if use_tabs_and_slots:
            feature_added = laser_add_top_bottom_dual_slots_to_group(
                group, top, thickness,
                tab_slot_count, tab_slot_width, gap_width, tab_slot_mode, margin1, margin2, kerf=kerf, included=included
            )
        laser_add_piece_to_make_box_group(group, top, feature_added)

    # Left: thickness x (width - 2*thickness) x (height - 2*thickness), at x = -length/2
    if left:
        left = laser_make_box_piece_simple(
            "Left",
            thickness, width - 2 * thickness, height - 2 * thickness,
            App.Vector(-length / 2, -width / 2 + thickness, -height / 2 + thickness)
        )

        feature_added = False
        if use_tabs_and_slots:
            feature_added = laser_add_tabs_feature_to_group(
                group, left, thickness,
                tab_slot_count, tab_slot_width, tab_taper, gap_width, tab_slot_mode, margin1, margin2, kerf=kerf, included=included
            )
        laser_add_piece_to_make_box_group(group, left, feature_added)

    # Right: at x = length/2 - thickness
    if right:
        right = laser_make_box_piece_simple(
            "Right",
            thickness, width - 2 * thickness, height - 2 * thickness,
            App.Vector(length / 2 - thickness, -width / 2 + thickness, -height / 2 + thickness)
        )
        feature_added = False
        if use_tabs_and_slots:
            feature_added = laser_add_tabs_feature_to_group(
                group, right, thickness,
                tab_slot_count, tab_slot_width, tab_taper, gap_width, tab_slot_mode, margin1, margin2, kerf=kerf, included=included
            )
        laser_add_piece_to_make_box_group(group, right, feature_added)

    # Front: tabs on top/bottom (±Z), slots on left/right (±X); slots run on the tabbed solid
    if front:
        front = laser_make_box_piece_simple(
            "Front",
            length, thickness, height - 2 * thickness,
            App.Vector(-length / 2, width / 2 - thickness, -height / 2 + thickness)
        )
        feature_added = False
        if use_tabs_and_slots:
            feature_added = laser_add_front_back_tabs_then_slots_to_group(
                group, front, thickness,
                tab_slot_count, tab_slot_width, tab_taper, gap_width, tab_slot_mode, margin1, margin2, kerf=kerf, included=included
            )
        laser_add_piece_to_make_box_group(group, front, feature_added)

    # Back: same edge roles as Front (world ±Z tabs, ±X slots)
    if back:
        back = laser_make_box_piece_simple(
            "Back",
            length, thickness, height - 2 * thickness,
            App.Vector(-length / 2, -width / 2, -height / 2 + thickness)
        )
        feature_added = False
        if use_tabs_and_slots:
            feature_added = laser_add_front_back_tabs_then_slots_to_group(
                group, back, thickness,
                tab_slot_count, tab_slot_width, tab_taper, gap_width, tab_slot_mode, margin1, margin2, kerf=kerf, included=included
            )
        laser_add_piece_to_make_box_group(group, back, feature_added)

    App.ActiveDocument.recompute()
    return group


def laser_make_box_pieces(length, width, height, thickness, top, bottom, left, right, front, back, use_tabs_and_slots, tab_slot_count, tab_slot_width, tab_taper, gap_width, tab_slot_mode, margin1, margin2, kerf=0.0):
    """Create box using PartDesign workbench (bodies, sketches, pads)."""
    group = App.ActiveDocument.addObject("App::DocumentObjectGroup", "Make Box Group")
    # Record a dict of which panels are being built (True/False) so we can skip slots/tabs for panels that are not being built
    included = laser_included_panels(top, bottom, left, right, front, back)

    if bottom:
        bottom = laser_make_box_piece(length, width, thickness, -height / 2, 'XY_Plane', 'BodyBottom')
        feature_added = False
        if use_tabs_and_slots:
            feature_added = laser_add_top_bottom_dual_slots_to_group(
                group, bottom, thickness,
                tab_slot_count, tab_slot_width, gap_width, tab_slot_mode, margin1, margin2, kerf=kerf, included=included
            )
        laser_add_piece_to_make_box_group(group, bottom, feature_added)

    if top:
        top = laser_make_box_piece(length, width, thickness, (height / 2) - thickness, 'XY_Plane', 'BodyTop')
        feature_added = False
        if use_tabs_and_slots:
            feature_added = laser_add_top_bottom_dual_slots_to_group(
                group, top, thickness,
                tab_slot_count, tab_slot_width, gap_width, tab_slot_mode, margin1, margin2, kerf=kerf, included=included
            )
        laser_add_piece_to_make_box_group(group, top, feature_added)

    if left:
        left = laser_make_box_piece(width - thickness * 2, height - thickness * 2, thickness, -length / 2, 'YZ_Plane', 'BodyLeft')
        feature_added = False
        if use_tabs_and_slots:
            feature_added = laser_add_tabs_feature_to_group(
                group, left, thickness,
                tab_slot_count, tab_slot_width, tab_taper, gap_width, tab_slot_mode, margin1, margin2, kerf=kerf, included=included
            )
        laser_add_piece_to_make_box_group(group, left, feature_added)

    if right:
        right = laser_make_box_piece(width - thickness * 2, height - thickness * 2, thickness, (length / 2) - thickness, 'YZ_Plane', 'BodyRight')
        feature_added = False
        if use_tabs_and_slots:
            feature_added = laser_add_tabs_feature_to_group(
                group, right, thickness,
                tab_slot_count, tab_slot_width, tab_taper, gap_width, tab_slot_mode, margin1, margin2, kerf=kerf, included=included
            )
        laser_add_piece_to_make_box_group(group, right, feature_added)

    if front:
        front = laser_make_box_piece(length, height - thickness * 2, thickness, (width / 2) - thickness, 'XZ_Plane', 'BodyFront')
        feature_added = False
        if use_tabs_and_slots:
            feature_added = laser_add_front_back_tabs_then_slots_to_group(
                group, front, thickness,
                tab_slot_count, tab_slot_width, tab_taper, gap_width, tab_slot_mode, margin1, margin2, kerf=kerf, included=included
            )
        laser_add_piece_to_make_box_group(group, front, feature_added)

    if back:
        back = laser_make_box_piece(length, height - thickness * 2, thickness, -width / 2, 'XZ_Plane', 'BodyBack')
        feature_added = False
        if use_tabs_and_slots:
            feature_added = laser_add_front_back_tabs_then_slots_to_group(
                group, back, thickness,
                tab_slot_count, tab_slot_width, tab_taper, gap_width, tab_slot_mode, margin1, margin2, kerf=kerf, included=included
            )
        laser_add_piece_to_make_box_group(group, back, feature_added)

    App.ActiveDocument.recompute()
    return group