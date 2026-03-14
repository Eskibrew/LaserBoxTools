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

__dir__ = os.path.dirname(__file__)
icons = os.path.join(__dir__, '../Resources/icons')
path_to_ui = os.path.join(__dir__, '../dialogs/basicbox.ui')

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


def laser_make_box_pieces_simple(length, width, height, thickness):
    """Create box using Part workbench (Part::Feature objects, no sketches)."""
    group = FreeCAD.ActiveDocument.addObject("App::DocumentObjectGroup", "Basic Box Group")

    # Bottom: length x width, at z = -height/2
    bottom = laser_make_box_piece_simple(
        "Bottom",
        length, width, thickness,
        FreeCAD.Vector(-length / 2, -width / 2, -height / 2)
    )
    group.addObject(bottom)

    # Top: length x width, at z = height/2 - thickness
    top = laser_make_box_piece_simple(
        "Top",
        length, width, thickness,
        FreeCAD.Vector(-length / 2, -width / 2, height / 2 - thickness)
    )
    group.addObject(top)

    # Left: thickness x (width - 2*thickness) x (height - 2*thickness), at x = -length/2
    left = laser_make_box_piece_simple(
        "Left",
        thickness, width - 2 * thickness, height - 2 * thickness,
        FreeCAD.Vector(-length / 2, -width / 2 + thickness, -height / 2 + thickness)
    )
    group.addObject(left)

    # Right: at x = length/2 - thickness
    right = laser_make_box_piece_simple(
        "Right",
        thickness, width - 2 * thickness, height - 2 * thickness,
        FreeCAD.Vector(length / 2 - thickness, -width / 2 + thickness, -height / 2 + thickness)
    )
    group.addObject(right)

    # Front: (length - 2*thickness) x thickness x (height - 2*thickness), at y = width/2 - thickness
    front = laser_make_box_piece_simple(
        "Front",
        length, thickness, height - 2 * thickness,
        FreeCAD.Vector(-length / 2, width / 2 - thickness, -height / 2 + thickness)
    )
    group.addObject(front)

    # Back: at y = -width/2
    back = laser_make_box_piece_simple(
        "Back",
        length, thickness, height - 2 * thickness,
        FreeCAD.Vector(-length / 2, -width / 2, -height / 2 + thickness)
    )
    group.addObject(back)

    FreeCAD.ActiveDocument.recompute()
    return group


def laser_make_box_pieces(length, width, height, thickness):
    """Create box using PartDesign workbench (bodies, sketches, pads)."""
    group = FreeCAD.ActiveDocument.addObject("App::DocumentObjectGroup", "Basic Box Group")

    bottom = laser_make_box_piece(length, width, thickness, -height / 2, 'XY_Plane', 'BodyBottom')
    group.addObject(bottom)

    top = laser_make_box_piece(length, width, thickness, (height / 2) - thickness, 'XY_Plane', 'BodyTop')
    group.addObject(top)

    left = laser_make_box_piece(width - thickness * 2, height - thickness * 2, thickness, -length / 2, 'YZ_Plane', 'BodyLeft')
    group.addObject(left)

    right = laser_make_box_piece(width - thickness * 2, height - thickness * 2, thickness, (length / 2) - thickness, 'YZ_Plane', 'BodyRight')
    group.addObject(right)

    front = laser_make_box_piece(length, height - thickness * 2, thickness, (width / 2) - thickness, 'XZ_Plane', 'BodyFront')
    group.addObject(front)

    back = laser_make_box_piece(length, height - thickness * 2, thickness, -width / 2, 'XZ_Plane', 'BodyBack')
    group.addObject(back)

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

        if self.form.rbPart.isChecked():
            laser_make_box_pieces_simple(length, width, height, thickness)
        else:
            laser_make_box_pieces(length, width, height, thickness)
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
