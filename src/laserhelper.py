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
#import FreeCADGui

import Part
#import Sketcher
import os, math
from PySide import QtCore, QtGui
import BOPTools.SplitFeatures

#__dir__ = os.path.dirname(__file__)
#icons = os.path.join(__dir__, '../Resources/icons')
#path_to_ui = os.path.join(__dir__, '../dialogs/tabs.ui')

lbEpsilon = 0.0000001

def lbGetThicknessFromFace(selFace, selObject, thicknessDir):
    """Get the distance from the selected face to the opposite face in the given normal direction.
    thicknessDir should point outward from the selected face (e.g. face normal).
    Returns the thickness (distance into the solid) or None if not found."""
    thicknessDir = thicknessDir.normalize()
    pt = selFace.CenterOfMass
    max_dist = 0.0
    for face in selObject.Faces:
        if face.isSame(selFace):
            continue
        # Face must be in the -thicknessDir direction (inside the solid)
        to_face = face.CenterOfMass - pt
        if to_face.dot(thicknessDir) >= -lbEpsilon:
            continue  # face is not in the "into solid" direction
        d, _, _ = selFace.distToShape(face)
        # Use maximum: adjacent faces (sharing an edge) have d=0; opposite face has d=thickness
        if d > max_dist:
            max_dist = d
    if max_dist > 0:
        return max_dist
    # Fallback: use shortest edge (works for rectangular faces, same as tabs/slots)
    min_edge = float('inf')
    for edge in selFace.Edges:
        if abs(edge.Length) < min_edge:
            min_edge = abs(edge.Length)
    return min_edge if min_edge != float('inf') else None


def lbEdgesParallel(edge1, edge2, tolerance=1e-6):
    """Check if two edges are parallel by comparing their direction vectors."""
    p1 = edge1.valueAt(edge1.FirstParameter)
    p2 = edge1.valueAt(edge1.LastParameter)
    p3 = edge2.valueAt(edge2.FirstParameter)
    p4 = edge2.valueAt(edge2.LastParameter)
    d1 = p2 - p1
    d2 = p4 - p3
    if d1.Length < lbEpsilon or d2.Length < lbEpsilon:
        return False  # degenerate edge
    d1 = d1.normalize()
    d2 = d2.normalize()
    # Parallel if cross product is (nearly) zero
    return d1.cross(d2).Length < tolerance

def lbActivateWorkbench():
    """Activate the LaserBoxTools workbench when editing tabs, slots or living hinge features.
    Uses QTimer to defer activation so the workbench combo box updates correctly."""
    def _do_activate():
        for name in ("LaserBoxToolsWorkbench", "LaserBoxesWorkbench"):
            try:
                FreeCADGui.activateWorkbench(name)
                return
            except Exception:
                continue
    # Defer to next event loop; 50ms delay helps combo box refresh after task panel opens
    QtCore.QTimer.singleShot(50, _do_activate)


def lbErrorMessage(msg):
    diag = QtGui.QMessageBox(QtGui.QMessageBox.Warning, 'Error', msg)
    diag.setWindowModality(QtCore.Qt.ApplicationModal)
    diag.exec_()


def lbBelongToBody(item, body):
    if (body is None):
        return False
    for obj in body.Group:
        if obj.Name == item.Name:
            return True
    return False


def lbIsSketchObject(obj):
    return str(obj).find("<Sketcher::") == 0


def lbIsPartObject(obj):
    return str(obj).find("<Part::") == 0


def lbIsPartDesign(obj):
    return str(obj).find("<PartDesign::") == 0


def lbIsOperationLegal(body, selobj):
    if lbIsPartObject(selobj):
        return True
    elif lbIsSketchObject(selobj) or not lbBelongToBody(selobj, body):
        lbErrorMessage("The selected geometry does not belong to the active Body.\nPlease make the container of this item active by\ndouble clicking on it.")
        return False
    return True


def lbRoundDown(n, decimals=0):
    multiplier = 10 ** decimals
    return math.floor(n * multiplier) / multiplier


def lbMakeFaces(type, edge, depthDir, widthDir, tabWidth, tabDepth, tabCount, gapWidth, mode, swapends, tabTaper, margin1, margin2, tabHookDepth, tabHookLength, tabHookRadius, swapHookDirection):
    #create a number of polygons, turn them into faces and return them in a list
    #mode can be "From Middle" (M), "From One End" (E) or "From Both Ends" (B)
    #gapWidth works for M and E modes and sets the gap between tabs; it cannot work for B mode.

    #if gapWidth is set to 0, the gaps are calculated based on the edge length, tabCount and tabWidth
    #if tabWidth is set to 0, the tabWidths are calculated on the edge length, gapWidth and tabCount
    #if tabWidth and gapWidth are 0, the tabWidth and tagGap will be equal and calculated from edge length and tabCount
    #if tabCount is 0, as many will be fitted as possible based on gapWidth and tabWidth

    #we may want to have tapered tabs so this allows for a taper angle
    faces = []
    taperLength = tabDepth * math.tan(math.radians(tabTaper))

    if abs(widthDir.x) > abs(widthDir.y) and abs(widthDir.x) > abs(widthDir.z):
        if widthDir.x < 0:
            widthDir.x = -widthDir.x
            widthDir.y = -widthDir.y
            widthDir.z = -widthDir.z
        firstValue = edge.valueAt(edge.FirstParameter).x
        lastValue = edge.valueAt(edge.LastParameter).x
    elif abs(widthDir.y) > abs(widthDir.z):
        if widthDir.y < 0:
            widthDir.x = -widthDir.x
            widthDir.y = -widthDir.y
            widthDir.z = -widthDir.z
        firstValue = edge.valueAt(edge.FirstParameter).y
        lastValue = edge.valueAt(edge.LastParameter).y
    else:
        if widthDir.z < 0:
            widthDir.x = -widthDir.x
            widthDir.y = -widthDir.y
            widthDir.z = -widthDir.z
        firstValue = edge.valueAt(edge.FirstParameter).z
        lastValue = edge.valueAt(edge.LastParameter).z

    if (taperLength * 2) > tabWidth:
        lbErrorMessage("Error: the taper angle is too high for the chosen tab depth and tab width.\nPlease adjust at least one parameter")
        return []

    if swapends:
        taperLength = -taperLength

    edgeLength = edge.Length - margin1 - margin2

    if gapWidth == 0 and tabWidth == 0 and tabCount == 0:
        lbErrorMessage("Error: gapWidth, tabWidth and tabCount are all zero.\nPlease make at least one parameter non-zero")
        return []

    if gapWidth == 0:
        if tabWidth == 0 or tabCount == 0:
            lbErrorMessage("Error: If gapWidth is zero, tabWidth and tabCount cannot be zero.\nPlease make at least one parameter non-zero")
            return []

    if tabWidth == 0:
        if gapWidth == 0 or tabCount == 0:
            lbErrorMessage("Error: If tabWidth is zero, gapWidth and tabCount cannot be zero.\nPlease make at least one parameter non-zero")
            return []

    if tabCount == 0:
        if gapWidth == 0 or tabWidth == 0:
            lbErrorMessage("Error: If tabCount is zero, tabWidth and gapWidth cannot be zero.\nPlease make at least one parameter non-zero")
            return []

    taperVector = widthDir * taperLength

    if mode == "From One End" or mode == "From Both Ends": 
        gapCount = tabCount

        if mode == "From Both Ends":
            if tabCount % 2 != 0:
                tabCount = tabCount + 1

        if gapWidth == 0 and tabWidth == 0:
            gapWidth = (edgeLength / tabCount) / 2
            tabWidth = gapWidth

        elif gapWidth == 0:
            gapWidth = (edgeLength - (tabCount * tabWidth)) / gapCount

        elif tabWidth == 0:
            tabWidth = (edgeLength - (gapCount * gapWidth)) / tabCount

        elif tabCount == 0:
            tabCount = 0
            gapCount = 0
            totalLength = 0

            while totalLength <= edgeLength:
                totalLength = totalLength + tabWidth

                if totalLength <= edgeLength:
                    tabCount = tabCount + 1
                    if ((totalLength + gapWidth) <= edgeLength):
                        totalLength = totalLength + gapWidth
                        gapCount = gapCount + 1
                    else:
                        break

        #we want to start at one end or the other end with a tab
        if swapends:
            if lastValue > firstValue:
                p1 = edge.valueAt(edge.LastParameter)
                p5 = edge.valueAt(edge.FirstParameter)
            else:
                p1 = edge.valueAt(edge.FirstParameter)
                p5 = edge.valueAt(edge.LastParameter)

            tabVector = widthDir * -tabWidth
            gapVector = widthDir * -gapWidth
            margin1Vector = widthDir * -margin1
            margin2Vector = widthDir * -margin2
        else:
            if lastValue < firstValue:
                p1 = edge.valueAt(edge.LastParameter)
                p5 = edge.valueAt(edge.FirstParameter)
            else:
                p1 = edge.valueAt(edge.FirstParameter)
                p5 = edge.valueAt(edge.LastParameter)

            tabVector = widthDir * tabWidth
            gapVector = widthDir * gapWidth
            margin1Vector = widthDir * margin1
            margin2Vector = widthDir * margin2

        p1 = p1 - gapVector - tabVector + margin1Vector
        p5 = p5 + gapVector + tabVector - margin2Vector

    elif mode == "From Middle":
        #we want to start in the middle
        #if there are an even number of tabs, we start with a gap in the middle
        #otherwise if there are an odd number, we start with a tab in the middle
        if tabCount % 2 == 0:
            #even number of tabs therefore odd number of gaps
            gapCount = tabCount + 1
        else:
            #odd number of tabs therefore even number of gaps
            gapCount = tabCount - 1

        if gapWidth == 0 and tabWidth == 0:
            gapWidth = (edgeLength / (tabCount + gapCount)) * gapCount
            tabWidth = (edgeLength / (tabCount + gapCount)) * tabCount

        elif gapWidth == 0:
            gapWidth = (edgeLength - (tabCount * tabWidth)) / gapCount

        elif tabWidth == 0:
            tabWidth = (edgeLength - (gapCount * gapWidth)) / tabCount

        elif tabCount == 0:
            tabCount = 0
            gapCount = 0
            totalLength = 0

            while totalLength <= edgeLength:
                totalLength = totalLength + tabWidth

                if totalLength <= edgeLength:
                    tabCount = tabCount + 1
                    if ((totalLength + gapWidth) <= edgeLength):
                        totalLength = totalLength + gapWidth
                        gapCount = gapCount + 1
                    else:
                        break

        #we want to start in the middle with either a tab or a gap
        #find the middle position alnog the face
        p1 = edge.valueAt((edge.LastParameter + edge.FirstParameter) / 2)

        tabVector = widthDir * tabWidth
        gapVector = widthDir * gapWidth

        if tabCount % 2 == 0:
            #even number of tabs therefore odd number of gaps
            #we therefore have a gap in the centre so subtract half a gap width
            p1 = p1 - (gapVector * (gapCount / 2))
            #then subtract half the number of tab widths
            p1 = p1 - (tabVector * (tabCount / 2))
            p1 = p1 - tabVector
        else:
            #odd number of tabs therefore even number of gaps
            #we therefore have a tab in the centre so subtract half a tab width
            p1 = p1 - (tabVector * (tabCount / 2))
            #then subtract half the number of gap widths
            p1 = p1 - (gapVector * (gapCount / 2))
            p1 = p1 - gapVector - tabVector

    if margin1 + margin2 + (tabWidth * tabCount) + (gapWidth * gapCount) > edge.Length:
        lbErrorMessage("Error: With these setting, the tabs will not fit on the face.\nPlease adjust at least one parameter")
        return []

    numTabs = tabCount

    while numTabs > 0:
        if (type == "Tab") or ((type == "Slot") and (tabHookLength == 0.0)):
            p1 = p1 + gapVector + tabVector
            p2 = p1 + tabVector
        else:
            if swapHookDirection:
                p = p1 + gapVector + tabVector - (tabHookLength * widthDir)
                p2 = p1 + gapVector + (2 * tabVector)
                p1 = p
            else:
                p = p1 + gapVector + tabVector
                p2 = p1 + gapVector + (2 * tabVector) + (tabHookLength * widthDir)
                p1 = p

        p3 = p2 - taperVector + (depthDir * tabDepth)
        p4 = p1 + taperVector + (depthDir * tabDepth)

        #now use our vertexes to make a polygon wire
        w = Part.makePolygon([p1,p2,p3,p4,p1])

        if (type == "Slot") and (tabHookLength > 0.0) and (swapHookDirection):
            p1 = p1 + (tabHookLength * widthDir)

        #use the resulting wire to make a face
        face = Part.Face(w)
        faces.append(face)

        if (type == "Tab") and (tabTaper == 0.0) and (tabHookDepth > 0) and (tabHookLength > 0):
            #as long as tabTaper is not active, we can add a tab hook if required
            #create a tab hook face
            #extending the tab hook along the depth direction with the hook end attached to p4
            if swapHookDirection:
                p6 = p4 - widthDir * tabHookLength
                p7 = p3
            else:
                p6 = p4
                p7 = p3 + widthDir * tabHookLength
                
            #p6 = p4
            #p7 = p3 + widthDir * tabHookLength

            p8 = p7 + depthDir * tabHookDepth
            p9 = p6 + depthDir * tabHookDepth
            if tabHookRadius > 0:
                # Build wire with filleted corners at p8 and p9
                r8 = min(tabHookRadius, (p7 - p8).Length * 0.99, (p9 - p8).Length * 0.99)
                r9 = min(tabHookRadius, (p8 - p9).Length * 0.99, (p6 - p9).Length * 0.99)
                if r8 > lbEpsilon and r9 > lbEpsilon:
                    # Fillet at p8
                    arc_start_8 = p8 + (p7 - p8).normalize() * r8
                    arc_end_8 = p8 + (p9 - p8).normalize() * r8
                    v1_8 = (arc_start_8 - p8).normalize()
                    v2_8 = (arc_end_8 - p8).normalize()
                    angle_8 = math.acos(max(-1, min(1, v1_8.dot(v2_8))))
                    bisector_8 = (v1_8 + v2_8).normalize()
                    arc_center_8 = p8 + bisector_8 * (r8 / math.sin(angle_8 / 2))
                    arc_mid_8 = arc_center_8 + ((arc_start_8 - arc_center_8).normalize() + (arc_end_8 - arc_center_8).normalize()).normalize() * r8
                    # Fillet at p9
                    arc_start_9 = p9 + (p8 - p9).normalize() * r9
                    arc_end_9 = p9 + (p6 - p9).normalize() * r9
                    v1_9 = (arc_start_9 - p9).normalize()
                    v2_9 = (arc_end_9 - p9).normalize()
                    angle_9 = math.acos(max(-1, min(1, v1_9.dot(v2_9))))
                    bisector_9 = (v1_9 + v2_9).normalize()
                    arc_center_9 = p9 + bisector_9 * (r9 / math.sin(angle_9 / 2))
                    arc_mid_9 = arc_center_9 + ((arc_start_9 - arc_center_9).normalize() + (arc_end_9 - arc_center_9).normalize()).normalize() * r9
                    e1 = Part.Edge(Part.LineSegment(p6, p7))
                    e2 = Part.Edge(Part.LineSegment(p7, arc_start_8))
                    e3 = Part.Edge(Part.Arc(arc_start_8, arc_mid_8, arc_end_8))
                    e4 = Part.Edge(Part.LineSegment(arc_end_8, arc_start_9))
                    e5 = Part.Edge(Part.Arc(arc_start_9, arc_mid_9, arc_end_9))
                    e6 = Part.Edge(Part.LineSegment(arc_end_9, p6))
                    tabHookFace = Part.Face(Part.Wire([e1, e2, e3, e4, e5, e6]))
                else:
                    tabHookFace = Part.Face(Part.makePolygon([p6, p7, p8, p9, p6]))
            else:
                tabHookFace = Part.makePolygon([p6, p7, p8, p9, p6])
                tabHookFace = Part.Face(tabHookFace)
            faces.append(tabHookFace)

        if mode == "From Both Ends":
            numTabs = numTabs - 2
        else:
            numTabs = numTabs - 1

    if mode == "From Both Ends":
        numTabs = tabCount
        p1 = p5

        while numTabs > 0:
            if (type == "Tab") or ((type == "Slot") and (tabHookLength == 0.0)):
                p1 = p1 - gapVector - tabVector
                p2 = p1 - tabVector
            else:
                if swapHookDirection:
                    p = p1 - gapVector - tabVector
                    p2 = p1 - gapVector - (2 * tabVector) - (tabHookLength * widthDir)
                    p1 = p
                else:
                    p = p1 - gapVector - tabVector + (tabHookLength * widthDir)
                    p2 = p1 - gapVector - (2 * tabVector)
                    p1 = p

            p3 = p2 + taperVector + (depthDir * tabDepth)
            p4 = p1 - taperVector + (depthDir * tabDepth)

            #now use our vertexes to make a polygon wire
            w = Part.makePolygon([p1,p2,p3,p4,p1])

            if (type == "Slot") and (tabHookLength > 0.0) and (swapHookDirection):
                p1 = p1 - (tabHookLength * widthDir)

            #use the resulting wire to make a face
            face = Part.Face(w)
            faces.append(face)
            numTabs = numTabs - 2

            if (type == "Tab") and (tabTaper == 0.0) and (tabHookDepth > 0) and (tabHookLength > 0):
                #as long as tabTaper is not active, we can add a tab hook if required
                #create a tab hook face
                #extending the tab hook along the depth direction with the hook end attached to p4
                if swapHookDirection:
                    p6 = p4
                    p7 = p3 - widthDir * tabHookLength
                else:
                    p6 = p4 + widthDir * tabHookLength
                    p7 = p3
                    
                p8 = p7 + depthDir * tabHookDepth
                p9 = p6 + depthDir * tabHookDepth
                if tabHookRadius > 0:
                    # Build wire with filleted corners at p8 and p9
                    r8 = min(tabHookRadius, (p7 - p8).Length * 0.99, (p9 - p8).Length * 0.99)
                    r9 = min(tabHookRadius, (p8 - p9).Length * 0.99, (p6 - p9).Length * 0.99)
                    if r8 > lbEpsilon and r9 > lbEpsilon:
                        # Fillet at p8
                        arc_start_8 = p8 + (p7 - p8).normalize() * r8
                        arc_end_8 = p8 + (p9 - p8).normalize() * r8
                        v1_8 = (arc_start_8 - p8).normalize()
                        v2_8 = (arc_end_8 - p8).normalize()
                        angle_8 = math.acos(max(-1, min(1, v1_8.dot(v2_8))))
                        bisector_8 = (v1_8 + v2_8).normalize()
                        arc_center_8 = p8 + bisector_8 * (r8 / math.sin(angle_8 / 2))
                        arc_mid_8 = arc_center_8 + ((arc_start_8 - arc_center_8).normalize() + (arc_end_8 - arc_center_8).normalize()).normalize() * r8
                        # Fillet at p9
                        arc_start_9 = p9 + (p8 - p9).normalize() * r9
                        arc_end_9 = p9 + (p6 - p9).normalize() * r9
                        v1_9 = (arc_start_9 - p9).normalize()
                        v2_9 = (arc_end_9 - p9).normalize()
                        angle_9 = math.acos(max(-1, min(1, v1_9.dot(v2_9))))
                        bisector_9 = (v1_9 + v2_9).normalize()
                        arc_center_9 = p9 + bisector_9 * (r9 / math.sin(angle_9 / 2))
                        arc_mid_9 = arc_center_9 + ((arc_start_9 - arc_center_9).normalize() + (arc_end_9 - arc_center_9).normalize()).normalize() * r9
                        e1 = Part.Edge(Part.LineSegment(p6, p7))
                        e2 = Part.Edge(Part.LineSegment(p7, arc_start_8))
                        e3 = Part.Edge(Part.Arc(arc_start_8, arc_mid_8, arc_end_8))
                        e4 = Part.Edge(Part.LineSegment(arc_end_8, arc_start_9))
                        e5 = Part.Edge(Part.Arc(arc_start_9, arc_mid_9, arc_end_9))
                        e6 = Part.Edge(Part.LineSegment(arc_end_9, p6))
                        tabHookFace = Part.Face(Part.Wire([e1, e2, e3, e4, e5, e6]))
                    else:
                        tabHookFace = Part.Face(Part.makePolygon([p6, p7, p8, p9, p6]))
                else:
                    tabHookFace = Part.makePolygon([p6, p7, p8, p9, p6])
                    tabHookFace = Part.Face(tabHookFace)
                faces.append(tabHookFace)

    return faces


def lbCreateLivingHingeElements(elementCount, elementVector, elementDepth, lengthDir, spacingVector, elementMode, elementType, Edge1, Edge2, Edge1End2, Edge2End2):
    faces = []

    numElements = elementCount

    if elementType != "Straight":
        FreeCAD.Console.PrintWarning("LivingHinge: Element type {} not implemented yet\n".format(elementType))
        return faces

    while numElements > 0:
        #FreeCAD.Console.PrintMessage("Creating face for element num: {}\n".format(numElements))
        if (numElements % 2 == 0):
            #FreeCAD.Console.PrintMessage("Creating face for even element num: {}\n".format(numElements))
            p1 = Edge1
            p2 = Edge1 + elementVector
            p3 = p2 + (lengthDir * elementDepth)
            p4 = p1 + (lengthDir * elementDepth)
            Edge1 = Edge1 + spacingVector + elementVector
            Edge2 = Edge2 + spacingVector + elementVector
        else:
            #FreeCAD.Console.PrintMessage("Creating face for odd element num: {}\n".format(numElements))
            p1 = Edge2
            p2 = Edge2 + elementVector
            p3 = p2 + (-lengthDir * elementDepth)
            p4 = p1 + (-lengthDir * elementDepth)
            Edge1 = Edge1 + spacingVector + elementVector
            Edge2 = Edge2 + spacingVector + elementVector

        #now use our vertexes to make a polygon wire
        w = Part.makePolygon([p1,p2,p3,p4,p1])

        #use the resulting wire to make a face
        #FreeCAD.Console.PrintMessage("Creating face p1: {}, p2: {}, p3: {}, p4: {}\n".format(p1, p2, p3, p4))
        face = Part.Face(w)
        faces.append(face)
        #Part.show(face)
        numElements = numElements - 1

    if elementMode == "From Both Ends":
        numElements = elementCount
        Edge1 = Edge1End2
        Edge2 = Edge2End2

        while numElements > 0:
            if (numElements % 2 == 0):
                p1 = Edge1
                p2 = Edge1 - elementVector
                p3 = p2 + (lengthDir * elementDepth)
                p4 = p1 + (lengthDir * elementDepth)
                Edge1 = Edge1 - spacingVector - elementVector
                Edge2 = Edge2 - spacingVector - elementVector
            else:
                p1 = Edge2
                p2 = Edge2 - elementVector
                p3 = p2 + (-lengthDir * elementDepth)
                p4 = p1 + (-lengthDir * elementDepth)
                Edge1 = Edge1 - spacingVector - elementVector
                Edge2 = Edge2 - spacingVector - elementVector

            #now use our vertexes to make a polygon wire
            w = Part.makePolygon([p1,p2,p3,p4,p1])

            #use the resulting wire to make a face
            #FreeCAD.Console.PrintMessage("Creating face FBE, p1: {}, p2: {}, p3: {}, p4: {}\n".format(p1, p2, p3, p4))
            face = Part.Face(w)
            faces.append(face)
            #Part.show(face)
            numElements = numElements - 1

    return faces


def lbMakeElementFaces(edge1, edge2, lengthDir, widthDir, elementCount, elementWidth, elementDepth, elementSpacing, elementMode, elementType, swapends, margin1, margin2):
    #create a number of polygons, turn them into faces and return them in a list
    #mode can be "From Middle" (M), "From One End" (E) or "From Both Ends" (B)

    #if elementCount is 0, as many will be fitted as possible based on elementSpacing and elementWidth

    #note: even numbered elements start at edge1, odd numbered elements start at edge2

    faces = []

    if abs(widthDir.x) > abs(widthDir.y) and abs(widthDir.x) > abs(widthDir.z):
        if widthDir.x < 0:
            widthDir.x = -widthDir.x
            widthDir.y = -widthDir.y
            widthDir.z = -widthDir.z
        firstValue = edge1.valueAt(edge1.FirstParameter).x
        lastValue = edge1.valueAt(edge1.LastParameter).x
    elif abs(widthDir.y) > abs(widthDir.z):
        if widthDir.y < 0:
            widthDir.x = -widthDir.x
            widthDir.y = -widthDir.y
            widthDir.z = -widthDir.z
        firstValue = edge1.valueAt(edge1.FirstParameter).y
        lastValue = edge1.valueAt(edge1.LastParameter).y
    else:
        if widthDir.z < 0:
            widthDir.x = -widthDir.x
            widthDir.y = -widthDir.y
            widthDir.z = -widthDir.z
        firstValue = edge1.valueAt(edge1.FirstParameter).z
        lastValue = edge1.valueAt(edge1.LastParameter).z

    if edge1.Length != edge2.Length:
        if edge1.Length < edge2.Length:
            edgeLength = edge1.Length - margin1 - margin2
        else:
            edgeLength = edge2.Length - margin1 - margin2
    else:
        edgeLength = edge1.Length - margin1 - margin2

    if elementMode == "From One End" or elementMode == "From Both Ends": 
        gapCount = elementCount + 1

        if elementCount == 0:
            # totalLength = space used (margins + gaps + elements); compare to full edge length not edgeLength
            totalLength = margin1 + margin2 + (2 * elementSpacing)  # first gap + last gap
            fullEdgeLength = edgeLength + margin1 + margin2  # actual edge length we're fitting to

            while totalLength <= fullEdgeLength:
                totalLength = totalLength + elementWidth

                if totalLength <= fullEdgeLength:
                    elementCount = elementCount + 1
                    if ((totalLength + elementSpacing) <= fullEdgeLength):
                        totalLength = totalLength + elementSpacing
                        gapCount = gapCount + 1
                    else:
                        break

        #we want to start at one end or the other end with a gap and then the first element
        if swapends:
            elementVector = widthDir * -elementWidth
            spacingVector = widthDir * -elementSpacing
            margin1Vector = widthDir * -margin1
            margin2Vector = widthDir * -margin2

            if lastValue > firstValue:
                #checked
                #FreeCAD.Console.PrintMessage("OK - Swapped but Last Value > First Value\n")
                Edge1 = edge1.valueAt(edge1.LastParameter) + spacingVector + margin2Vector
                Edge1End2 = edge1.valueAt(edge1.FirstParameter) + spacingVector + margin1Vector
                Edge2 = edge2.valueAt(edge2.LastParameter) + spacingVector + margin2Vector
                Edge2End2 = edge2.valueAt(edge2.FirstParameter) + spacingVector + margin1Vector
            else:
                #FreeCAD.Console.PrintMessage("Swapped but Last Value < First Value\n")
                Edge1 = edge1.valueAt(edge1.FirstParameter) + spacingVector + margin1Vector
                Edge1End2 = edge1.valueAt(edge1.LastParameter) - spacingVector - margin2Vector
                Edge2 = edge2.valueAt(edge2.FirstParameter) + spacingVector + margin1Vector
                Edge2End2 = edge2.valueAt(edge2.LastParameter) - spacingVector - margin2Vector
        else:
            elementVector = widthDir * elementWidth
            spacingVector = widthDir * elementSpacing
            margin1Vector = widthDir * margin1
            margin2Vector = widthDir * margin2

            if lastValue < firstValue:
                #FreeCAD.Console.PrintMessage("Not swapped but Last Value > First Value\n")
                Edge1 = edge1.valueAt(edge1.LastParameter) + spacingVector + margin1Vector
                Edge1End2 = edge1.valueAt(edge1.FirstParameter) + spacingVector + margin2Vector
                Edge2 = edge2.valueAt(edge2.LastParameter) + spacingVector + margin1Vector
                Edge2End2 = edge2.valueAt(edge2.FirstParameter) + spacingVector + margin2Vector
            else:
                #checked
                #FreeCAD.Console.PrintMessage("OK - Not swapped but Last Value < First Value\n")
                Edge1 = edge1.valueAt(edge1.FirstParameter) + spacingVector + margin1Vector
                Edge1End2 = edge1.valueAt(edge1.LastParameter) - spacingVector - margin2Vector
                Edge2 = edge2.valueAt(edge2.FirstParameter) + spacingVector + margin1Vector
                Edge2End2 = edge2.valueAt(edge2.LastParameter) - spacingVector - margin2Vector

    elif elementMode == "From Middle":
        #we want to start in the middle
        #if there are an even number of elements, we start with a gap in the middle
        #otherwise if there are an odd number, we start with an element in the middle
        gapCount = elementCount - 1

        if elementCount == 0:
            elementCount = 0
            gapCount = 0
            totalLength = margin1 + margin2 + (2 * elementSpacing)  # first gap + last gap
            fullEdgeLength = edgeLength + margin1 + margin2

            while totalLength <= fullEdgeLength:
                totalLength = totalLength + elementWidth

                if totalLength <= fullEdgeLength:
                    elementCount = elementCount + 1
                    if ((totalLength + elementSpacing) <= fullEdgeLength):
                        totalLength = totalLength + elementSpacing
                        gapCount = gapCount + 1
                    else:
                        break

        #we want to start in the middle with either a element or a gap
        #find the middle position alnog the face
        Edge1 = edge1.valueAt((edge1.LastParameter + edge1.FirstParameter) / 2)
        Edge2 = edge2.valueAt((edge2.LastParameter + edge2.FirstParameter) / 2)

        elementVector = widthDir * elementWidth
        spacingVector = widthDir * elementSpacing

        Edge1End2 = edge1.valueAt(edge1.FirstParameter)
        Edge2End2 = edge2.valueAt(edge2.FirstParameter)

        if elementCount % 2 == 0:
            #even number of elements therefore odd number of gaps
            #we therefore have a gap in the centre so subtract half a gap width
            Edge1 = Edge1 - (spacingVector * (gapCount / 2))
            #then subtract half the number of element widths
            Edge1 = Edge1 - (elementVector * (elementCount / 2))

            Edge2 = Edge2 - (spacingVector * (gapCount / 2))
            #then subtract half the number of element widths
            Edge2 = Edge2 - (elementVector * (elementCount / 2))
        else:
            #odd number of elements therefore even number of gaps
            #we therefore have a element in the centre so subtract half a element width
            Edge1 = Edge1 - (elementVector * (elementCount / 2))
            #then subtract half the number of gap widths
            Edge1 = Edge1 - (spacingVector * (gapCount / 2))

            Edge2 = Edge2 - (elementVector * (elementCount / 2))
            #then subtract half the number of gap widths
            Edge2 = Edge2 - (spacingVector * (gapCount / 2))

    if margin1 + margin2 + (elementWidth * elementCount) + (elementSpacing * gapCount) > edge1.Length:
        lbErrorMessage("Error: With these setting, the elements will not fit on the face.\nPlease adjust at least one parameter")
        return []

    faces = lbCreateLivingHingeElements(elementCount, elementVector, elementDepth, lengthDir, spacingVector, elementMode, elementType, Edge1, Edge2, Edge1End2, Edge2End2)

    return faces

def lbGetValidFaceNames(selFaceNames):
    """Normalize and filter face names - invalid names (e.g. ?Face1 from broken toponaming) are skipped."""
    if selFaceNames is None:
        return []
    # Normalize to list (PropertyLinkSub can return tuple or single string)
    if isinstance(selFaceNames, str):
        names = [selFaceNames] if selFaceNames else []
    else:
        names = list(selFaceNames) if selFaceNames else []
    # Filter out invalid names (FreeCAD uses ? prefix when toponaming reference is broken)
    return [n for n in names if n and not n.startswith('?')]


def lbCreateTabs(tabCount, tabWidth, gapWidth, tabDepth, mode, swapends, tabTaper, margin1, margin2, tabHookDepth, tabHookLength, tabHookRadius, swapHookDirection, subtraction = False, refine = True, selFaceNames = '', selObject = ''):
    finalShape = selObject
    solidlist =[]
    
    selFaceNames = lbGetValidFaceNames(selFaceNames)
    if not selFaceNames:
        FreeCAD.Console.PrintWarning("Tabs: No valid face references - base object may need to be re-selected. (Topological naming can break after boolean operations.)\n")
        return finalShape

    for selFaceName in selFaceNames:
        try:
            selFace = selObject.getElement(selFaceName)
        except (ValueError, RuntimeError) as e:
            FreeCAD.Console.PrintWarning("Tabs: Skipping invalid face '{}': {}\n".format(selFaceName, str(e)))
            continue

        # find the narrow edge
        thickness = 999999.0
        for edge in selFace.Edges:
            if abs(edge.Length) < thickness:
                thickness = abs(edge.Length)
                thicknessEdge = edge

        # find the length edge
        p0 = thicknessEdge.valueAt(thicknessEdge.FirstParameter)
        for lengthEdge in selFace.Edges:
            p1 = lengthEdge.valueAt(lengthEdge.FirstParameter)
            p2 = lengthEdge.valueAt(lengthEdge.LastParameter)
            if lengthEdge.isSame(thicknessEdge):
                continue
            if (p1 - p0).Length < lbEpsilon:
                break
            if (p2 - p0).Length < lbEpsilon:
                break

        # find the large face connected with selected face
        list2 = selObject.ancestorsOfType(lengthEdge, Part.Face)
        for connectedFace in list2:
            if not(connectedFace.isSame(selFace)) :
                break

        # determine extrusion direction
        pThicknessDir1 = selFace.CenterOfMass
        pThicknessDir2 = lengthEdge.Curve.value(lengthEdge.Curve.parameter(pThicknessDir1))
        thicknessDir = pThicknessDir1.sub(pThicknessDir2)
        thicknessDir = thicknessDir.normalize()

        # determine tab depth direction
        depthDir = selFace.normalAt(0,0).normalize()

        # determine tab width direction
        pWidthDir1 = selFace.CenterOfMass
        pWidthDir2 = thicknessEdge.Curve.value(thicknessEdge.Curve.parameter(pWidthDir1))
        widthDir = pWidthDir2.sub(pWidthDir1)
        widthDir = widthDir.normalize()

        tab_faces = []

        if tabDepth > 0.0:
            # create tabs on face selected
            # we first create the faces
            tab_faces = lbMakeFaces("Tab", lengthEdge, depthDir, widthDir, tabWidth, tabDepth, tabCount, gapWidth, mode, swapends, tabTaper, margin1, margin2, tabHookDepth, tabHookLength, tabHookRadius, swapHookDirection)

            for tab_face in tab_faces:
                # then extrude each face to create a tab
                tabSolid = tab_face.extrude(thicknessDir * thickness)
                # add the tab to the list of solids
                solidlist.append(tabSolid)
                #Part.show(tabSolid)

    resultSolid = selObject

    # if we have any solids, we need to fuse them together to create the final shape
    if len(solidlist) > 0:
        for solid in solidlist:
            resultSolid = resultSolid.fuse(solid)

        if refine:
            resultSolid = resultSolid.removeSplitter()

        # Merge final list
        finalShape = finalShape.cut(resultSolid)
        finalShape = finalShape.fuse(resultSolid)

    return finalShape

def lbCreateSlots(slotCount, slotLength, gapWidth, slotDepth, mode, swapends, margin1, margin2, offsetFromFace, slotHookLength, swapHookDirection, subtraction = False, refine = True, selFaceNames = '', selObject = ''):
    finalShape = selObject
    solidlist =[]
    
    selFaceNames = lbGetValidFaceNames(selFaceNames)
    if not selFaceNames:
        FreeCAD.Console.PrintWarning("Slots: No valid face references - base object may need to be re-selected. (Topological naming can break after boolean operations.)\n")
        return finalShape

    for selFaceName in selFaceNames:
        try:
            selFace = selObject.getElement(selFaceName)
        except (ValueError, RuntimeError) as e:
            FreeCAD.Console.PrintWarning("Slots: Skipping invalid face '{}': {}\n".format(selFaceName, str(e)))
            continue

        # find the narrow edge
        thickness = 999999.0
        for edge in selFace.Edges:
            if abs(edge.Length) < thickness:
                thickness = abs(edge.Length)
                thicknessEdge = edge

        # find the length edge
        p0 = thicknessEdge.valueAt(thicknessEdge.FirstParameter)
        for lengthEdge in selFace.Edges:
            p1 = lengthEdge.valueAt(lengthEdge.FirstParameter)
            p2 = lengthEdge.valueAt(lengthEdge.LastParameter)
            if lengthEdge.isSame(thicknessEdge):
                continue
            if (p1 - p0).Length < lbEpsilon:
                break
            if (p2 - p0).Length < lbEpsilon:
                break

        # find the large face connected with selected face
        list2 = selObject.ancestorsOfType(lengthEdge, Part.Face)
        for connectedFace in list2:
            if not(connectedFace.isSame(selFace)) :
                break

        # determine extrusion direction
        pThicknessDir1 = selFace.CenterOfMass
        pThicknessDir2 = lengthEdge.Curve.value(lengthEdge.Curve.parameter(pThicknessDir1))
        thicknessDir = pThicknessDir1.sub(pThicknessDir2)
        thicknessDir = thicknessDir.normalize()

        # determine slot depth direction (opposite to face normal so slot cuts into the solid)
        depthDir = -selFace.normalAt(0,0).normalize()

        # determine slot length direction
        pLengthDir1 = selFace.CenterOfMass
        pLengthDir2 = thicknessEdge.Curve.value(thicknessEdge.Curve.parameter(pLengthDir1))
        LengthDir = pLengthDir2.sub(pLengthDir1)
        LengthDir = LengthDir.normalize()

        # use offset edge when offsetFromFace is specified
        slotEdge = lengthEdge
        if offsetFromFace != 0.0:
            p1 = lengthEdge.valueAt(lengthEdge.FirstParameter)
            p2 = lengthEdge.valueAt(lengthEdge.LastParameter)
            # offset in direction of face normal (depthDir points into solid)
            # use copy - multiply() modifies in place and would corrupt depthDir for lbMakeFaces
            offsetVec = FreeCAD.Vector(depthDir).multiply(offsetFromFace)
            slotEdge = Part.makeLine(p1.add(offsetVec), p2.add(offsetVec))

        slot_faces = []

        if slotDepth > 0.0:
            # create slots on face selected
            # we first create the faces
            slot_faces = lbMakeFaces("Slot", slotEdge, depthDir, LengthDir, slotLength, slotDepth, slotCount, gapWidth, mode, swapends, 0.0, margin1, margin2, slotDepth, slotHookLength, 0.0, swapHookDirection)

            for slot_face in slot_faces:
                # then extrude each face to create a negative slot (much like a tab)
                slotSolid = slot_face.extrude(thicknessDir * thickness)
                # add the slot to the list of solids
                solidlist.append(slotSolid)
                #Part.show(slotSolid)  # Debug: add to tree for visual inspection

    # Cut each slot solid from the base object (accumulate cuts)
    if len(solidlist) > 0:
        for solid in solidlist:
            finalShape = finalShape.cut(solid)

        if refine:
            finalShape = finalShape.removeSplitter()

    return finalShape

def lbCreateLivingHinge(elementCount, elementWidth, elementDepth, elementSpacing, elementMode, elementType, swapends, margin1, margin2, subtraction = False, refine = True, selFaceNames = '', selObject = ''):
    finalShape = selObject
    solidlist =[]
    
    #we have not implemented the elementType yet
    if elementType != "Straight":
        FreeCAD.Console.PrintWarning("LivingHinge: Element type not implemented yet\n")
        return finalShape

    selFaceNames = lbGetValidFaceNames(selFaceNames)
    if not selFaceNames:
        FreeCAD.Console.PrintWarning("LivingHinge: No valid face references - base object may need to be re-selected. (Topological naming can break after boolean operations.)\n")
        return finalShape

    for selFaceName in selFaceNames:
        try:
            selFace = selObject.getElement(selFaceName)
        except (ValueError, RuntimeError) as e:
            FreeCAD.Console.PrintWarning("LivingHinge: Skipping invalid face '{}': {}\n".format(selFaceName, str(e)))
            continue

        # find the narrow edge (shortest) and length edges (longest pair)
        maxLength = 0.0
        lengthEdge1 = None
        
        for edge in selFace.Edges:
            if abs(edge.Length) > maxLength:
                maxLength = abs(edge.Length)
                lengthEdge1 = edge

        if lengthEdge1 is None:
            FreeCAD.Console.PrintWarning("LivingHinge: Face has no edges\n")
            return finalShape

        # find lengthEdge2: another edge parallel to lengthEdge1 (the other long edge)
        lengthEdge2 = None
        for edge in selFace.Edges:
            if edge.isSame(lengthEdge1):
                continue
            if lbEdgesParallel(edge, lengthEdge1):
                lengthEdge2 = edge
                break

        if lengthEdge2 is None:
            FreeCAD.Console.PrintWarning("LivingHinge: No parallel length edge found on face\n")
            return finalShape


        # ensure both edges point in the same direction (FirstParameter at same end of face)
        dir1 = (lengthEdge1.valueAt(lengthEdge1.LastParameter) - lengthEdge1.valueAt(lengthEdge1.FirstParameter)).normalize()
        dir2 = (lengthEdge2.valueAt(lengthEdge2.LastParameter) - lengthEdge2.valueAt(lengthEdge2.FirstParameter)).normalize()
        if dir1.dot(dir2) < 0:
            # reverse lengthEdge2: create new edge with swapped endpoints
            p1 = lengthEdge2.valueAt(lengthEdge2.FirstParameter)
            p2 = lengthEdge2.valueAt(lengthEdge2.LastParameter)
            lengthEdge2 = Part.makeLine(p2, p1)

        # find the large face connected with selected face
        list2 = selObject.ancestorsOfType(lengthEdge1, Part.Face)
        for connectedFace in list2:
            if not(connectedFace.isSame(selFace)) :
                break

        # determine extrusion direction
        thicknessDir = selFace.normalAt(0,0).normalize()

        # compute thickness: distance from selected face to opposite face in normal direction
        thickness = lbGetThicknessFromFace(selFace, selObject, thicknessDir)
        #FreeCAD.Console.PrintMessage("LivingHinge: Thickness: {}\n".format(thickness))
        if thickness is None or thickness <= 0:
            FreeCAD.Console.PrintWarning("LivingHinge: Could not determine thickness, using 10mm\n")
            thickness = 10.0

        # vector perpendicular to lengthDir (in plane of face) - cross with ref least parallel to avoid singularity
        if abs(thicknessDir.z) < 0.9:
            lengthDir = thicknessDir.cross(FreeCAD.Vector(0, 0, 1)).normalize()
        else:
            lengthDir = thicknessDir.cross(FreeCAD.Vector(1, 0, 0)).normalize()

        widthDir = thicknessDir.cross(FreeCAD.Vector(0, 1, 0)).normalize()
        element_faces = []

        # create hinge elements on face selected
        # we first create the faces
        element_faces = lbMakeElementFaces(lengthEdge1, lengthEdge2, lengthDir, widthDir, elementCount, elementWidth, elementDepth, elementSpacing, elementMode, elementType, swapends, margin1, margin2)

        for element_face in element_faces:
            elementSolid = element_face.extrude(-thicknessDir * thickness)
            if elementSolid.isNull() or not elementSolid.isValid():
                FreeCAD.Console.PrintWarning("LivingHinge: Extrusion produced invalid solid, skipping\n")
                continue
            # add the element to the list of solids
            solidlist.append(elementSolid)
            #Part.show(elementSolid)

    # Cut all elements in one operation. Multi-tool cut is faster than fuse-then-cut or N sequential cuts.
    if len(solidlist) > 0:
        try:
            if len(solidlist) == 1:
                cutResult = finalShape.cut(solidlist[0])
            else:
                cutResult = finalShape.cut(tuple(solidlist))
            if cutResult.isNull() or not cutResult.isValid():
                FreeCAD.Console.PrintWarning("LivingHinge: Cut produced invalid result\n")
            else:
                finalShape = cutResult
        except Exception as e:
            # Fallback: fuse then cut (multi-tool cut may need OCCT 6.9+)
            try:
                combinedCutter = solidlist[0]
                for solid in solidlist[1:]:
                    combinedCutter = combinedCutter.fuse(solid)
                cutResult = finalShape.cut(combinedCutter)
                if not (cutResult.isNull() or not cutResult.isValid()):
                    finalShape = cutResult
            except Exception as e2:
                FreeCAD.Console.PrintWarning("LivingHinge: Cut failed: {}\n".format(str(e2)))

    if refine:
        finalShape = finalShape.removeSplitter()

    return finalShape
