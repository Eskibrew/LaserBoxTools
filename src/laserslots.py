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

## Problems
###1) Prevent slots on a curved surface (or make them work)

from FreeCAD import Gui
import FreeCAD
import FreeCADGui
import Part
#import Sketcher
import os
from PySide import QtCore, QtGui

import src.laserhelper as laserhelper

import FreeCAD, FreeCADGui, Part, os, math
import FreeCAD as App
import sys
freecadpython = sys.executable.replace('freecad', 'python')
App.Console.PrintMessage('Using ' + freecadpython +'\n')

#import debugpy
#debugpy.configure(python=freecadpython)
#
#if not debugpy.is_client_connected():
#    debugpy.listen(5678)
#        
#print("waiting for debugger attach")
#debugpy.wait_for_client()

__dir__ = os.path.dirname(__file__)
icons = os.path.join(__dir__, '../Resources/icons')
path_to_ui = os.path.join(__dir__, '../dialogs/slots.ui')

def LBEnsureSlotHookProperties(obj):
    """Add Slot* properties if missing (backward compatibility for older saved objects)."""
    if not hasattr(obj, 'SwapEnds'):
        obj.addProperty("App::PropertyBool", "SwapEnds", "Parameters", "Swap Ends").SwapEnds = False
    if not hasattr(obj, 'SwapHookDirection'):
        obj.addProperty("App::PropertyBool", "SwapHookDirection", "Parameters", "Swap Hook Direction").SwapHookDirection = False
    if not hasattr(obj, 'SlotHookLength'):
        obj.addProperty("App::PropertyLength", "SlotHookLength", "Parameters", "Slot Hook Length").SlotHookLength = 0.0


class LBGenerateSlots:
    def __init__(self, obj):
        '''"Generate Slots" '''
        obj.Proxy = self
        selobj = Gui.Selection.getSelectionEx()[0]
        _tip_ = QtCore.QT_TRANSLATE_NOOP("App::Property","Auto Update")
        obj.addProperty("App::PropertyBool","AutoUpdate","ParametersExt",_tip_).AutoUpdate = False
        _tip_ = QtCore.QT_TRANSLATE_NOOP("App::Property","Slot Count")
        obj.addProperty("App::PropertyInteger","SlotCount","Parameters",_tip_).SlotCount = 0
        _tip_ = QtCore.QT_TRANSLATE_NOOP("App::Property","Slot Length")
        obj.addProperty("App::PropertyLength","SlotLength","Parameters",_tip_).SlotLength = 10.0
        _tip_ = QtCore.QT_TRANSLATE_NOOP("App::Property","Slot Depth")
        obj.addProperty("App::PropertyLength","SlotDepth","Parameters",_tip_).SlotDepth = 3.0
        _tip_ = QtCore.QT_TRANSLATE_NOOP("App::Property","Gap Width")
        obj.addProperty("App::PropertyLength","GapWidth","Parameters",_tip_).GapWidth = 10.0
        _tip_ = QtCore.QT_TRANSLATE_NOOP("App::Property","Base Object")
        obj.addProperty("App::PropertyLinkSub", "baseObject", "Parameters",_tip_).baseObject = (selobj.Object, selobj.SubElementNames)
        _tip_ = QtCore.QT_TRANSLATE_NOOP("App::Property","Use Refine")
        obj.addProperty("App::PropertyBool","Refine","ParametersExt",_tip_).Refine = True
        _tip_ = QtCore.QT_TRANSLATE_NOOP("App::Property","Where to start slots")
        obj.addProperty("App::PropertyEnumeration", "SlotMode", "Parameters", _tip_).SlotMode = ["From One End", "From Both Ends", "From Middle"]
        _tip_ = QtCore.QT_TRANSLATE_NOOP("App::Property","SwapEnds")
        obj.addProperty("App::PropertyBool","SwapEnds","Parameters",_tip_).SwapEnds = False
        _tip_ = QtCore.QT_TRANSLATE_NOOP("App::Property","Slot Margin1")
        obj.addProperty("App::PropertyLength","Margin1","Parameters",_tip_).Margin1 = 0.0
        _tip_ = QtCore.QT_TRANSLATE_NOOP("App::Property","Slot Margin2")
        obj.addProperty("App::PropertyLength","Margin2","Parameters",_tip_).Margin2 = 0.0
        _tip_ = QtCore.QT_TRANSLATE_NOOP("App::Property","Slot Hook Depth")
        obj.addProperty("App::PropertyLength","SlotHookLength","Parameters",_tip_).SlotHookLength = 0.0
        _tip_ = QtCore.QT_TRANSLATE_NOOP("App::Property","Swap Hook Direction")
        obj.addProperty("App::PropertyBool","SwapHookDirection","Parameters",_tip_).SwapHookDirection = False
        _tip_ = QtCore.QT_TRANSLATE_NOOP("App::Property","Slot Offset from face")
        obj.addProperty("App::PropertyLength","OffsetFromFace","Parameters",_tip_).OffsetFromFace = 0.0

    def getElementMapVersion(self, _fp, ver, _prop, restored):
        #TODO not sure what this is
        if not restored:
            return "lb0.1.0"

    def execute(self, fp):
        '''"Print a short message when doing a recomputation, this method is mandatory" '''
        LBEnsureSlotHookProperties(fp)
        # pass selected object shape
        Main_Object = fp.baseObject[0].Shape.copy()
        face = fp.baseObject[1]

        s = laserhelper.lbCreateSlots(slotCount = fp.SlotCount, slotLength = fp.SlotLength.Value, gapWidth = fp.GapWidth.Value,
                        slotDepth = fp.SlotDepth.Value, mode = fp.SlotMode, swapends = fp.SwapEnds,
                        margin1 = fp.Margin1.Value, margin2 = fp.Margin2.Value, offsetFromFace = fp.OffsetFromFace.Value,
                        slotHookLength = fp.SlotHookLength.Value, swapHookDirection = fp.SwapHookDirection,
                        subtraction = False, refine = fp.Refine, selFaceNames = face, selObject = Main_Object)
        fp.Shape = s


class LBSlotsViewProviderTree:
    "A View provider that nests children objects under the created one, like Part"

    def __init__(self, vobj):
        vobj.Proxy = self
        self.Object = vobj.Object

    def attach(self, vobj):
        self.Object = vobj.Object
        return

    def setupContextMenu(self, viewObject, menu):
        action = menu.addAction(FreeCAD.Qt.translate("QObject", "Edit %1").replace("%1", viewObject.Object.Label))
        action.triggered.connect(lambda: self.startDefaultEditMode(viewObject))
        return False

    def startDefaultEditMode(self, viewObject):
        document = viewObject.Document.Document
        if not document.HasPendingTransaction:
            text = FreeCAD.Qt.translate("QObject", "Edit %1").replace("%1", viewObject.Object.Label)
            document.openTransaction(text)
        viewObject.Document.setEdit(viewObject.Object, 0)

    def updateData(self, fp, prop):
        '''If a property of the handled feature has changed we have the chance to handle this here'''
        # Do NOT call fp.Document.recompute() here - it causes recursive recompute when
        # dependents (e.g. Slots on Tabs) exist. FreeCAD's dependency graph handles recompute.
        return

    def getDisplayModes(self, vobj):
        modes=[]
        return modes

    def setDisplayMode(self,mode):
        return mode

    def __getstate__(self):
        return None

    def __setstate__(self,state):
        if state is not None:
            doc = FreeCAD.ActiveDocument
            self.Object = doc.getObject(state['ObjectName'])

    def claimChildren(self):
        objs = []
        if hasattr(self.Object,"baseObject"):
            objs.append(self.Object.baseObject[0])
        if hasattr(self.Object,"Sketch"):
            objs.append(self.Object.Sketch)
        return objs
    
    def getIcon(self):
        return os.path.join(icons, 'slots.svg')

    def setEdit(self, vobj, mode):
        if (mode != 0):
            return False #we only handle the detault mode

        laserhelper.lbActivateWorkbench()
        LBEnsureSlotHookProperties(vobj.Object)
        taskd = LBSlotsTaskPanel(True)
        taskd.obj = vobj.Object
        self.Object.AutoUpdate = False
        taskd.form.SlotCount.setValue(self.Object.SlotCount)
        taskd.form.SlotLength.setValue(self.Object.SlotLength)
        taskd.form.SlotDepth.setValue(self.Object.SlotDepth)
        taskd.form.GapWidth.setValue(self.Object.GapWidth)
        taskd.form.SlotMode.setCurrentText(self.Object.SlotMode)
        taskd.form.SwapEnds.setChecked(self.Object.SwapEnds)
        taskd.form.SlotHookLength.setValue(self.Object.SlotHookLength)
        taskd.form.SwapHookDirection.setChecked(self.Object.SwapHookDirection)
        taskd.form.Margin1.setValue(self.Object.Margin1)
        taskd.form.Margin2.setValue(self.Object.Margin2)
        taskd.form.OffsetFromFace.setValue(self.Object.OffsetFromFace)
        self.Object.AutoUpdate = True
        taskd.update()
        taskd.updateSlotDepthLabel()
        FreeCADGui.Control.showDialog(taskd)
        return True

    def unsetEdit(self, vobj, mode):
        if (mode != 0):
            return False #we only handle the detault mode
            
        FreeCADGui.Control.closeDialog()
        return False


class LBSlotsViewProviderFlat:
    "A View provider that places objects flat under base object, like PartDesign"

    def __init__(self, obj):
        obj.Proxy = self
        self.Object = obj.Object

    def attach(self, obj):
        self.Object = obj.Object
        return

    def updateData(self, fp, prop):
        '''If a property of the handled feature has changed we have the chance to handle this here'''
        if fp.AutoUpdate:
            if  prop == "SlotDepth" or \
                prop == "SlotLength" or \
                prop == "GapWidth" or \
                prop == "SlotCount" or \
                prop == "Refine" or \
                prop == "SlotMode" or \
                prop == "Margin1" or \
                prop == "Margin2" or \
                prop == "OffsetFromFace" or \
                prop == "baseObject" or \
                prop == "SwapEnds" or \
                prop == "SlotHookLength" or \
                prop == "SwapHookDirection":
                fp.Document.recompute()  # Full document recompute so dependents (e.g. Tabs) update
        return

    def getDisplayModes(self,obj):
        modes=[]
        return modes

    def setDisplayMode(self,mode):
        return mode

    def __getstate__(self):
        return None

    def __setstate__(self,state):
        if state is not None:
            doc = FreeCAD.ActiveDocument
            self.Object = doc.getObject(state['ObjectName'])

    def claimChildren(self):
        objs = []
        if hasattr(self.Object,"Sketch"):
            objs.append(self.Object.Sketch)
        return objs
    
    def getIcon(self):
        return os.path.join(icons, 'tabs.svg')

    def setEdit(self,vobj,mode):
        if (mode != 0):
            return False #we only handle the detault mode

        laserhelper.lbActivateWorkbench()
        LBEnsureSlotHookProperties(vobj.Object)
        taskd = LBSlotsTaskPanel(True)
        taskd.obj = vobj.Object
        self.Object.AutoUpdate = False
        taskd.form.SlotCount.setValue(self.Object.SlotCount)
        taskd.form.SlotLength.setValue(self.Object.SlotLength)
        taskd.form.SlotDepth.setValue(self.Object.SlotDepth)
        taskd.form.GapWidth.setValue(self.Object.GapWidth)
        taskd.form.SlotMode.setCurrentText(self.Object.SlotMode)
        taskd.form.SwapEnds.setChecked(self.Object.SwapEnds)
        taskd.form.SlotHookLength.setValue(self.Object.SlotHookLength)
        taskd.form.SwapHookDirection.setChecked(self.Object.SwapHookDirection)
        taskd.form.Margin1.setValue(self.Object.Margin1)
        taskd.form.Margin2.setValue(self.Object.Margin2)
        taskd.form.OffsetFromFace.setValue(self.Object.OffsetFromFace)
        self.Object.AutoUpdate = True
        taskd.update()
        taskd.updateSlotDepthLabel()
        taskd.updateSlotModeSwapEndsState()
        FreeCADGui.Control.showDialog(taskd)
        return True

    def unsetEdit(self,vobj,mode):
        if (mode != 0):
            return False #we only handle the detault mode
            
        FreeCADGui.Control.closeDialog()
        return False


class LBSlotsTaskPanel:
    def __init__(self, editing):
        self.editing = editing
        self.obj = None
        # this will create a Qt widget from our ui file
        self.form = FreeCADGui.PySideUic.loadUi(path_to_ui)
        QtCore.QObject.connect(self.form.pbUpdateSlotFaces, QtCore.SIGNAL("clicked()"), self.updateSlotFaces)
        QtCore.QObject.connect(self.form.pbEditSlotFaces, QtCore.SIGNAL("clicked()"), self.editSlotFaces)
        # set some default values
        self.form.SlotCount.setValue(0)
        self.form.SlotLength.setValue(10.0)
        self.form.SlotDepth.setValue(3.0)
        self.form.GapWidth.setValue(10.0)
        self.form.SlotMode.setCurrentIndex(0)
        self.form.SwapEnds.setChecked(False)
        self.form.SlotHookLength.setValue(0.0)
        self.form.SwapHookDirection.setChecked(False)
        self.form.Margin1.setValue(0.0)
        self.form.Margin2.setValue(0.0)
        self.form.OffsetFromFace.setValue(0.0)
        self.form.SlotCount.valueChanged.connect(self.onSlotCountChanged)
        self.form.SlotLength.valueChanged.connect(self.onSlotLengthChanged)
        self.form.SlotDepth.valueChanged.connect(self.onSlotDepthChanged)
        self.form.GapWidth.valueChanged.connect(self.onGapWidthChanged)
        self.form.SlotMode.currentTextChanged.connect(self.onSlotModeChanged)
        self.form.SwapEnds.stateChanged.connect(self.onSwapEndsChanged)
        self.form.SlotHookLength.valueChanged.connect(self.onSlotHookLengthChanged)
        self.form.SwapHookDirection.stateChanged.connect(self.onSwapHookDirectionChanged)
        self.form.Margin1.valueChanged.connect(self.onMargin1Changed)
        self.form.Margin2.valueChanged.connect(self.onMargin2Changed)
        self.form.OffsetFromFace.valueChanged.connect(self.onOffsetFromFaceChanged)
        self.update()
        self.updateSlotDepthLabel()
        self.updateSlotModeSwapEndsState()

    def updateSlotModeSwapEndsState(self):
        """Disable SlotMode and SwapEnds when SlotCount is 0."""
        enabled = self.form.SlotCount.value() != 0
        self.form.SlotMode.setEnabled(enabled)
        self.form.SwapEnds.setEnabled(enabled and self.form.SlotMode.currentText() == "From One End")

    def onSlotCountChanged(self, val):
        self.updateSlotModeSwapEndsState()
        if self.obj.SlotMode == "From Both Ends":
            if val % 2 != 0:
                #it needs to be an even number in this mode
                if self.obj.SlotCount > val:
                    val = val - 1
                else:
                    val = val + 1

                self.form.SlotCount.setValue(val)
        self.obj.SlotCount = val

    def onSlotLengthChanged(self, val):
        self.obj.SlotLength = val

    def onSlotDepthChanged(self, val):
        self.obj.SlotDepth = val

    def onGapWidthChanged(self, val):
        self.obj.GapWidth = val

    def onSlotModeChanged(self, val):
        if self.obj:
            self.obj.SlotMode = val
        self.updateSlotModeSwapEndsState()

        if self.obj and val == "From Both Ends":
            if self.obj.SlotCount % 2 != 0:
                self.form.SlotCount.setValue(self.obj.SlotCount + 1)

    def onSwapEndsChanged(self, val):
        self.obj.SwapEnds = val

    def onSlotHookLengthChanged(self, val):
        self.obj.SlotHookLength = val

    def onSwapHookDirectionChanged(self, val):
        self.obj.SwapHookDirection = val

    def onMargin1Changed(self, val):
        self.obj.Margin1 = val

    def onMargin2Changed(self, val):
        self.obj.Margin2 = val

    def onOffsetFromFaceChanged(self, val):
        self.obj.OffsetFromFace = val
        self.updateSlotDepthLabel()

    def updateSlotDepthLabel(self):
        """Update Slot Depth label based on OffsetFromFace value"""
        offset = self.form.OffsetFromFace.value() if self.form else 0.0
        label = self.form.label_3 if self.form else None
        if label:
            label.setText("Slot Width" if offset != 0.0 else "Slot Depth")

    def update(self):
        'fills the treeWidgetSlotFaces'
        self.form.treeWidgetSlotFaces.clear()
        if self.obj:
            f = self.obj.baseObject
            if isinstance(f[1], list):
                for subf in f[1]:
                    item = QtGui.QTreeWidgetItem(self.form.treeWidgetSlotFaces)
                    item.setText(0, f[0].Name)
                    item.setIcon(0, QtGui.QIcon(":/icons/Tree_Part.svg"))
                    item.setText(1, subf)
            else:
                item = QtGui.QTreeWidgetItem(self.form.treeWidgetSlotFaces)
                item.setText(0, f[0].Name)
                item.setIcon(0, QtGui.QIcon(":/icons/Tree_Part.svg"))
                item.setText(1, f[1][0])
        self.retranslateUi(self.form)

    def editSlotFaces(self):
        print(f"edit slot faces")  
        self.obj.baseObject[0].ViewObject.Visibility = True
        self.obj.ViewObject.Visibility = False
        self.form.pbEditSlotFaces.setEnabled(False)
        self.form.pbUpdateSlotFaces.setEnabled(True)
        self.form.treeWidgetSlotFaces.setEnabled(True)
        self.copyBaseObject = self.obj.baseObject

    def updateSlotFaces(self):
        self.form.pbEditSlotFaces.setEnabled(True)
        self.form.pbUpdateSlotFaces.setEnabled(False)
        self.form.treeWidgetSlotFaces.setEnabled(False)
        print(f"update slot faces")  
        if self.obj:
            if len(FreeCADGui.Selection.getSelectionEx()) < 1:
                laserhelper.lbErrorMessage("Error: Invalid selection")
            else:
                sel = FreeCADGui.Selection.getSelectionEx()[0]
                if sel.HasSubObjects:
                    obj = sel.Object
                    for elt in sel.SubElementNames:
                        if "Face" in elt:
                            face = self.obj.baseObject
                            found = False
                            if (face[0] == obj.Name):
                                if isinstance(face[1], tuple):
                                    for subf in face[1]:
                                        if subf == elt:
                                            found = True
                                else:
                                    if (face[1][0] == elt):
                                        found = True

                            if not found:
                                    self.obj.baseObject = (sel.Object, sel.SubElementNames)
                self.update()
        self.obj.baseObject[0].ViewObject.Visibility = False
        self.obj.ViewObject.Visibility = True

    def accept(self):
        FreeCAD.ActiveDocument.recompute()
        FreeCAD.ActiveDocument.commitTransaction()
        FreeCADGui.Control.closeDialog()
        FreeCADGui.ActiveDocument.resetEdit()
        return True

    def reject(self):
        if not self.editing:  # creating: abort transaction to undo creation
            self.obj.baseObject[0].ViewObject.Visibility = True
            self.obj.ViewObject.Visibility = False
        if FreeCAD.ActiveDocument.HasPendingTransaction:
            FreeCAD.ActiveDocument.abortTransaction()
        FreeCAD.ActiveDocument.recompute()
        FreeCADGui.Control.closeDialog()

    def retranslateUi(self, TaskPanel):
        self.form.pbUpdateSlotFaces.setText(QtGui.QApplication.translate("draft", "Update", None))


'''My Command Class'''
class LBSlots:

    '''My new command'''
    def __init__(self):
        return

    '''Return the resources for this command'''
    def GetResources(self):
        return {'Pixmap': os.path.join(icons, 'slots.svg'),
                'MenuText': "Add slots to face",
                'ToolTip': "Add slots to face"}

    '''Do something here'''
    def Activated(self):
        "Show the task panel so the user can specify the number of slots etc"
        doc = FreeCAD.ActiveDocument
        view = Gui.ActiveDocument.ActiveView
        activeBody = None
        selobj = Gui.Selection.getSelectionEx()[0].Object
        
        if hasattr(view,'getActiveObject'):
            activeBody = view.getActiveObject('pdbody')
        
        if not laserhelper.lbIsOperationLegal(activeBody, selobj):
            return
        
        doc.openTransaction("Slots")
        
        #we have to check if the active body is a part or a part design
        if activeBody is None or not laserhelper.lbIsPartDesign(selobj):
            #if it is a part design, we use the tree view provider
            a = doc.addObject("Part::FeaturePython","Slots")
            cls = LBGenerateSlots(a)
            LBSlotsViewProviderTree(a.ViewObject)
            a.AutoUpdate = True
            cls.execute(a)
        else:
            #if it is a part, we use the flat view provider
            a = doc.addObject("PartDesign::FeaturePython","Slots")
            cls = LBGenerateSlots(a)
            LBSlotsViewProviderFlat(a.ViewObject)
            a.AutoUpdate = True
            activeBody.addObject(a)
            cls.execute(a)
        
        panel = LBSlotsTaskPanel(False)
        panel.obj = a
        panel.update()
        FreeCADGui.Control.showDialog(panel)
        return

    '''Here you can define if the command must be active or not (greyed) if certain conditions are met or not. This function is optional.'''
    def IsActive(self):
        if len(Gui.Selection.getSelection()) < 1 or len(Gui.Selection.getSelectionEx()[0].SubElementNames) < 1:
            return False
        selobj = Gui.Selection.getSelection()[0]
        if selobj.isDerivedFrom("Sketcher::SketchObject"):
            return False
        for selFace in Gui.Selection.getSelectionEx()[0].SubObjects:
            if type(selFace) == Part.Vertex :
                return False
            if type(selFace) == Part.Edge :
                return False
        return True


'''Add the new command in to FreeCAD'''
Gui.addCommand('LBSlots', LBSlots())
