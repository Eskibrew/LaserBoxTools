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
###1) Prevent hinges on a curved surface (or make them work)
###2) Add different hinge styles - see here https://obrary.com/products/living-hinge-patterns

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

__dir__ = os.path.dirname(__file__)
icons = os.path.join(__dir__, '../Resources/icons')
path_to_ui = os.path.join(__dir__, '../dialogs/hinge.ui')


def LBEnsureLivingHingeProperties(obj):
    """Add LivingHinge* properties if missing (backward compatibility for older saved objects)."""
    if not hasattr(obj, 'SwapEnds'):
        obj.addProperty("App::PropertyBool", "SwapEnds", "Parameters", "Swap Ends").SwapEnds = False
    if not hasattr(obj, 'ElementType'):
        obj.addProperty("App::PropertyEnumeration", "ElementType", "Parameters", "What shape are the hinge elements").ElementType = ["Straight"]


class LBGenerateLivingHinge:
    def __init__(self, obj):
        '''"Generate Tabs" '''
        obj.Proxy = self
        selobj = Gui.Selection.getSelectionEx()[0]
        _tip_ = QtCore.QT_TRANSLATE_NOOP("App::Property","Auto Update")
        obj.addProperty("App::PropertyBool","AutoUpdate","ParametersExt",_tip_).AutoUpdate = False
        _tip_ = QtCore.QT_TRANSLATE_NOOP("App::Property","Element Count")
        obj.addProperty("App::PropertyInteger","ElementCount","Parameters",_tip_).ElementCount = 4
        _tip_ = QtCore.QT_TRANSLATE_NOOP("App::Property","Element Width")
        obj.addProperty("App::PropertyLength","ElementWidth","Parameters",_tip_).ElementWidth = 0.1
        _tip_ = QtCore.QT_TRANSLATE_NOOP("App::Property","Element Depth")
        obj.addProperty("App::PropertyLength","ElementDepth","Parameters",_tip_).ElementDepth = 3.0
        _tip_ = QtCore.QT_TRANSLATE_NOOP("App::Property","Element Spacing")
        obj.addProperty("App::PropertyLength","ElementSpacing","Parameters",_tip_).ElementSpacing = 1.0
        _tip_ = QtCore.QT_TRANSLATE_NOOP("App::Property","Base Object")
        obj.addProperty("App::PropertyLinkSub", "baseObject", "Parameters",_tip_).baseObject = (selobj.Object, selobj.SubElementNames)
        _tip_ = QtCore.QT_TRANSLATE_NOOP("App::Property","Use Refine (slower but cleaner result)")
        obj.addProperty("App::PropertyBool","Refine","ParametersExt",_tip_).Refine = False
        _tip_ = QtCore.QT_TRANSLATE_NOOP("App::Property","Where to start hinge elements")
        obj.addProperty("App::PropertyEnumeration", "ElementMode", "Parameters", _tip_).ElementMode = ["From One End", "From Both Ends", "From Middle"]
        _tip_ = QtCore.QT_TRANSLATE_NOOP("App::Property","Swap Ends")
        obj.addProperty("App::PropertyBool","SwapEnds","Parameters",_tip_).SwapEnds = False
        _tip_ = QtCore.QT_TRANSLATE_NOOP("App::Property","Margin1")
        obj.addProperty("App::PropertyLength","Margin1","Parameters",_tip_).Margin1 = 0.0
        _tip_ = QtCore.QT_TRANSLATE_NOOP("App::Property","Margin2")
        obj.addProperty("App::PropertyLength","Margin2","Parameters",_tip_).Margin2 = 0.0
        _tip_ = QtCore.QT_TRANSLATE_NOOP("App::Property","What shape are the hinge elements")
        obj.addProperty("App::PropertyEnumeration", "ElementType", "Parameters", _tip_).ElementType = ["Straight"]

    def getElementMapVersion(self, _fp, ver, _prop, restored):
        #TODO not sure what this is
        if not restored:
            return "lb0.1.0"

    def execute(self, fp):
        '''"Print a short message when doing a recomputation, this method is mandatory" '''
        LBEnsureLivingHingeProperties(fp)
        # pass selected object shape
        Main_Object = fp.baseObject[0].Shape.copy()
        face = fp.baseObject[1]

        s = laserhelper.lbCreateLivingHinge(elementCount = fp.ElementCount, elementWidth = fp.ElementWidth.Value, elementDepth = fp.ElementDepth.Value, elementSpacing = fp.ElementSpacing.Value, elementMode = fp.ElementMode, elementType = fp.ElementType, swapends = fp.SwapEnds, margin1 = fp.Margin1.Value, margin2 = fp.Margin2.Value, subtraction = False, refine = fp.Refine, selFaceNames = face, selObject = Main_Object)
        fp.baseObject[0].ViewObject.Visibility = False
        fp.Shape = s



class LBLivingHingeViewProviderTree:
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
        if fp.AutoUpdate:
            if  prop == "ElementDepth" or \
                prop == "ElementWidth" or \
                prop == "ElementCount" or \
                prop == "ElementSpacing" or \
                prop == "Refine" or \
                prop == "ElementMode" or \
                prop == "ElementType" or \
                prop == "Margin1" or \
                prop == "Margin2" or \
                prop == "baseObject" or \
                prop == "SwapEnds":
                fp.Document.recompute()  # Full document recompute so dependents update immediately
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
        return os.path.join(icons, 'livinghinge.svg')

    def setEdit(self, vobj, mode):
        if (mode != 0):
            return False #we only handle the detault mode

        laserhelper.lbActivateWorkbench()
        LBEnsureLivingHingeProperties(vobj.Object)
        taskd = LBLivingHingeTaskPanel(True)
        taskd.obj = vobj.Object
        self.Object.AutoUpdate = False
        taskd.form.ElementCount.setValue(self.Object.ElementCount)
        taskd.form.ElementWidth.setValue(self.Object.ElementWidth)
        taskd.form.ElementDepth.setValue(self.Object.ElementDepth)
        taskd.form.ElementSpacing.setValue(self.Object.ElementSpacing)
        taskd.form.ElementMode.setCurrentText(self.Object.ElementMode)
        taskd.form.ElementType.setCurrentText(self.Object.ElementType)
        taskd.form.SwapEnds.setChecked(self.Object.SwapEnds)
        taskd.form.Margin1.setValue(self.Object.Margin1)
        taskd.form.Margin2.setValue(self.Object.Margin2)
        self.Object.AutoUpdate = True
        taskd.update()
        taskd.updateElementModeSwapEndsState()
        FreeCADGui.Control.showDialog(taskd)
        return True

    def unsetEdit(self, vobj, mode):
        if (mode != 0):
            return False #we only handle the detault mode
            
        FreeCADGui.Control.closeDialog()
        return False


class LBLivingHingeViewProviderFlat:
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
            if  prop == "ElementDepth" or \
                prop == "ElementWidth" or \
                prop == "ElementCount" or \
                prop == "ElementSpacing" or \
                prop == "Refine" or \
                prop == "ElementMode" or \
                prop == "ElementType" or \
                prop == "Margin1" or \
                prop == "Margin2" or \
                prop == "baseObject" or \
                prop == "SwapEnds":
                fp.Document.recompute()  # Full document recompute so dependents update immediately
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
        LBEnsureLivingHingeProperties(vobj.Object)
        taskd = LBLivingHingeTaskPanel(True)
        taskd.obj = vobj.Object
        self.Object.AutoUpdate = False
        taskd.form.ElementCount.setValue(self.Object.ElementCount)
        taskd.form.ElementWidth.setValue(self.Object.ElementWidth)
        taskd.form.ElementDepth.setValue(self.Object.ElementDepth)
        taskd.form.ElementSpacing.setValue(self.Object.ElementSpacing)
        taskd.form.ElementMode.setCurrentText(self.Object.ElementMode)
        taskd.form.ElementType.setCurrentText(self.Object.ElementType)
        taskd.form.SwapEnds.setChecked(self.Object.SwapEnds)
        taskd.form.Margin1.setValue(self.Object.Margin1)
        taskd.form.Margin2.setValue(self.Object.Margin2)
        self.Object.AutoUpdate = True
        taskd.update()
        taskd.updateElementModeSwapEndsState()
        FreeCADGui.Control.showDialog(taskd)
        return True

    def unsetEdit(self,vobj,mode):
        if (mode != 0):
            return False #we only handle the detault mode
            
        FreeCADGui.Control.closeDialog()
        return False


class LBLivingHingeTaskPanel:
    def __init__(self, editing):
        self.editing = editing
        self.obj = None
        # this will create a Qt widget from our ui file
        self.form = FreeCADGui.PySideUic.loadUi(path_to_ui)
        QtCore.QObject.connect(self.form.pbUpdateElementFaces, QtCore.SIGNAL("clicked()"), self.updateElementFaces)
        QtCore.QObject.connect(self.form.pbEditElementFaces, QtCore.SIGNAL("clicked()"), self.editElementFaces)
        # set some default values
        self.form.ElementCount.setValue(4)
        self.form.ElementWidth.setValue(0.1)
        self.form.ElementDepth.setValue(3.0)
        self.form.ElementSpacing.setValue(1.0)
        self.form.ElementMode.setCurrentIndex(0)
        self.form.ElementType.setCurrentIndex(0)
        self.form.SwapEnds.setChecked(False)
        self.form.Margin1.setValue(0.0)
        self.form.Margin2.setValue(0.0)
        self.form.ElementCount.valueChanged.connect(self.onElementCountChanged)
        self.form.ElementWidth.valueChanged.connect(self.onElementWidthChanged)
        self.form.ElementDepth.valueChanged.connect(self.onElementDepthChanged)
        self.form.ElementSpacing.valueChanged.connect(self.onElementSpacingChanged)
        self.form.ElementMode.currentTextChanged.connect(self.onElementModeChanged)
        self.form.ElementType.currentTextChanged.connect(self.onElementTypeChanged)
        self.form.SwapEnds.stateChanged.connect(self.onSwapEndsChanged)
        self.form.Margin1.valueChanged.connect(self.onMargin1Changed)
        self.form.Margin2.valueChanged.connect(self.onMargin2Changed)
        self.update()
        self.updateElementModeSwapEndsState()

    def updateElementModeSwapEndsState(self):
        """Disable ElementMode and SwapEnds when ElementCount is 0."""
        enabled = self.form.ElementCount.value() != 0
        self.form.ElementMode.setEnabled(enabled)
        self.form.SwapEnds.setEnabled(enabled and self.form.ElementMode.currentText() == "From One End")

    def onElementCountChanged(self, val):
        self.updateElementModeSwapEndsState()
        if self.obj:
            if self.obj.ElementMode == "From Both Ends":
                if val % 2 != 0:
                    #it needs to be an even number in this mode
                    if self.obj.ElementCount > val:
                        val = val - 1
                    else:
                        val = val + 1

                    self.form.ElementCount.setValue(val)
            self.obj.ElementCount = val

    def onElementWidthChanged(self, val):
        self.obj.ElementWidth = val

    def onElementDepthChanged(self, val):
        self.obj.ElementDepth = val

    def onElementSpacingChanged(self, val):
        self.obj.ElementSpacing = val

    def onElementModeChanged(self, val):
        if self.obj:
            self.obj.ElementMode = val
        self.updateElementModeSwapEndsState()

        if self.obj and val == "From Both Ends":
            if self.obj.ElementCount % 2 != 0:
                self.form.ElementCount.setValue(self.obj.ElementCount + 1)

    def onElementTypeChanged(self, val):
        if self.obj:
            self.obj.ElementType = val

    def onSwapEndsChanged(self, val):
        self.obj.SwapEnds = val

    def onMargin1Changed(self, val):
        self.obj.Margin1 = val

    def onMargin2Changed(self, val):
        self.obj.Margin2 = val

    def update(self):
        'fills the treeWidgetElementFaces'
        self.form.treeWidgetElementFaces.clear()
        if self.obj:
            f = self.obj.baseObject
            if isinstance(f[1], list):
                for subf in f[1]:
                    item = QtGui.QTreeWidgetItem(self.form.treeWidgetElementFaces)
                    item.setText(0, f[0].Name)
                    item.setIcon(0, QtGui.QIcon(":/icons/Tree_Part.svg"))
                    item.setText(1, subf)
            else:
                item = QtGui.QTreeWidgetItem(self.form.treeWidgetElementFaces)
                item.setText(0, f[0].Name)
                item.setIcon(0, QtGui.QIcon(":/icons/Tree_Part.svg"))
                item.setText(1, f[1][0])
        self.retranslateUi(self.form)

    def editElementFaces(self):
        print(f"edit Element faces")  
        self.obj.baseObject[0].ViewObject.Visibility = True
        self.obj.ViewObject.Visibility = False
        self.form.pbEditElementFaces.setEnabled(False)
        self.form.pbUpdateElementFaces.setEnabled(True)
        self.form.treeWidgetElementFaces.setEnabled(True)
        self.copyBaseObject = self.obj.baseObject

    def updateElementFaces(self):
        self.form.pbEditElementFaces.setEnabled(True)
        self.form.pbUpdateElementFaces.setEnabled(False)
        self.form.treeWidgetElementFaces.setEnabled(False)
        print(f"update Element faces")  
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
        self.form.pbUpdateElementFaces.setText(QtGui.QApplication.translate("draft", "Update", None))


'''My Command Class'''
class LBLivingHinge:

    '''My new command'''
    def __init__(self):
        return

    '''Return the resources for this command'''
    def GetResources(self):
        return {'Pixmap': os.path.join(icons, 'livinghinge.svg'),
                'MenuText': "Add living hinge to face",
                'ToolTip': "Add living hinge to face"}

    '''Do something here'''
    def Activated(self):
        "Show the task panel so the user can specify the number of living hinge etc"
        doc = FreeCAD.ActiveDocument
        view = Gui.ActiveDocument.ActiveView
        activeBody = None
        selobj = Gui.Selection.getSelectionEx()[0].Object
        
        if hasattr(view,'getActiveObject'):
            activeBody = view.getActiveObject('pdbody')
        
        if not laserhelper.lbIsOperationLegal(activeBody, selobj):
            return
        
        doc.openTransaction("LivingHinge")
        
        if activeBody is None or not laserhelper.lbIsPartDesign(selobj):
            a = doc.addObject("Part::FeaturePython","LivingHinge")
            cls = LBGenerateLivingHinge(a)
            LBLivingHingeViewProviderTree(a.ViewObject)
            a.AutoUpdate = True
            cls.execute(a)
        else:
            a = doc.addObject("PartDesign::FeaturePython","LivingHinge")
            cls = LBGenerateLivingHinge(a)
            LBLivingHingeViewProviderFlat(a.ViewObject)
            a.AutoUpdate = True
            activeBody.addObject(a)
            cls.execute(a)
        
        panel = LBLivingHingeTaskPanel(False)
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
Gui.addCommand('LBLivingHinge', LBLivingHinge())
