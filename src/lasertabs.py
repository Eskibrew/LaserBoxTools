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
###1) Prevent tabs on a curved surface (or make them work)

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
path_to_ui = os.path.join(__dir__, '../dialogs/tabs.ui')


def LBEnsureTabHookProperties(obj):
    """Add TabHook* properties if missing (backward compatibility for older saved objects)."""
    if not hasattr(obj, 'SwapEnds'):
        obj.addProperty("App::PropertyBool", "SwapEnds", "Parameters", "Swap Ends").SwapEnds = False
    if not hasattr(obj, 'SwapHookDirection'):
        obj.addProperty("App::PropertyBool", "SwapHookDirection", "Parameters", "Swap Hook Direction").SwapHookDirection = False
    if not hasattr(obj, 'TabHookDepth'):
        obj.addProperty("App::PropertyLength", "TabHookDepth", "Parameters", "Tab Hook Depth").TabHookDepth = 0.0
    if not hasattr(obj, 'TabHookLength'):
        obj.addProperty("App::PropertyLength", "TabHookLength", "Parameters", "Tab Hook Length").TabHookLength = 0.0
    if not hasattr(obj, 'TabHookRadius'):
        obj.addProperty("App::PropertyLength", "TabHookRadius", "Parameters", "Tab Hook Radius").TabHookRadius = 0.0


class LBGenerateTabs:
    def __init__(self, obj):
        '''"Generate Tabs" '''
        obj.Proxy = self
        selobj = Gui.Selection.getSelectionEx()[0]
        _tip_ = QtCore.QT_TRANSLATE_NOOP("App::Property","Auto Update")
        obj.addProperty("App::PropertyBool","AutoUpdate","ParametersExt",_tip_).AutoUpdate = False
        _tip_ = QtCore.QT_TRANSLATE_NOOP("App::Property","Tab Count")
        obj.addProperty("App::PropertyInteger","TabCount","Parameters",_tip_).TabCount = 0
        _tip_ = QtCore.QT_TRANSLATE_NOOP("App::Property","Tab Width")
        obj.addProperty("App::PropertyLength","TabWidth","Parameters",_tip_).TabWidth = 10.0
        _tip_ = QtCore.QT_TRANSLATE_NOOP("App::Property","Tab Depth")
        obj.addProperty("App::PropertyLength","TabDepth","Parameters",_tip_).TabDepth = 3.0
        _tip_ = QtCore.QT_TRANSLATE_NOOP("App::Property","Gap Width")
        obj.addProperty("App::PropertyLength","GapWidth","Parameters",_tip_).GapWidth = 10.0
        _tip_ = QtCore.QT_TRANSLATE_NOOP("App::Property","Base Object")
        obj.addProperty("App::PropertyLinkSub", "baseObject", "Parameters",_tip_).baseObject = (selobj.Object, selobj.SubElementNames)
        _tip_ = QtCore.QT_TRANSLATE_NOOP("App::Property","Use Refine")
        obj.addProperty("App::PropertyBool","Refine","ParametersExt",_tip_).Refine = True
        _tip_ = QtCore.QT_TRANSLATE_NOOP("App::Property","Where to start tabs")
        obj.addProperty("App::PropertyEnumeration", "TabMode", "Parameters", _tip_).TabMode = ["From One End", "From Both Ends", "From Middle"]
        _tip_ = QtCore.QT_TRANSLATE_NOOP("App::Property","Swap Ends")
        obj.addProperty("App::PropertyBool","SwapEnds","Parameters",_tip_).SwapEnds = False
        _tip_ = QtCore.QT_TRANSLATE_NOOP("App::Property","Tab Taper Angle")
        obj.addProperty("App::PropertyLength","TabTaper","Parameters",_tip_).TabTaper = 0.0
        _tip_ = QtCore.QT_TRANSLATE_NOOP("App::Property","Tab Depth")
        obj.addProperty("App::PropertyLength","Margin1","Parameters",_tip_).Margin1 = 0.0
        _tip_ = QtCore.QT_TRANSLATE_NOOP("App::Property","Tab Depth")
        obj.addProperty("App::PropertyLength","Margin2","Parameters",_tip_).Margin2 = 0.0
        _tip_ = QtCore.QT_TRANSLATE_NOOP("App::Property","Tab Hook Depth")
        obj.addProperty("App::PropertyLength","TabHookDepth","Parameters",_tip_).TabHookDepth = 0.0
        _tip_ = QtCore.QT_TRANSLATE_NOOP("App::Property","Tab Hook Length")
        obj.addProperty("App::PropertyLength","TabHookLength","Parameters",_tip_).TabHookLength = 0.0
        _tip_ = QtCore.QT_TRANSLATE_NOOP("App::Property","Tab Hook Radius")
        obj.addProperty("App::PropertyLength","TabHookRadius","Parameters",_tip_).TabHookRadius = 0.0
        _tip_ = QtCore.QT_TRANSLATE_NOOP("App::Property","Swap Hook Direction")
        obj.addProperty("App::PropertyBool","SwapHookDirection","Parameters",_tip_).SwapHookDirection = False

    def getElementMapVersion(self, _fp, ver, _prop, restored):
        #TODO not sure what this is
        if not restored:
            return "lb0.1.0"

    def execute(self, fp):
        '''"Print a short message when doing a recomputation, this method is mandatory" '''
        LBEnsureTabHookProperties(fp)
        # pass selected object shape
        Main_Object = fp.baseObject[0].Shape.copy()
        face = fp.baseObject[1]

        s = laserhelper.lbCreateTabs(tabCount = fp.TabCount, tabWidth = fp.TabWidth.Value, gapWidth = fp.GapWidth.Value,
                        tabDepth = fp.TabDepth.Value, mode = fp.TabMode, swapends = fp.SwapEnds, tabTaper = fp.TabTaper.Value,
                        margin1 = fp.Margin1.Value, margin2 = fp.Margin2.Value,
                        tabHookDepth = fp.TabHookDepth.Value, tabHookLength = fp.TabHookLength.Value, tabHookRadius = fp.TabHookRadius.Value,
                        swapHookDirection = fp.SwapHookDirection,
                        subtraction = False, refine = fp.Refine, selFaceNames = face, selObject = Main_Object)
        fp.baseObject[0].ViewObject.Visibility = False
        fp.Shape = s



class LBTabsViewProviderTree:
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
            if  prop == "TabDepth" or \
                prop == "TabWidth" or \
                prop == "GapWidth" or \
                prop == "TabCount" or \
                prop == "TabTaper" or \
                prop == "Refine" or \
                prop == "TabMode" or \
                prop == "Margin1" or \
                prop == "Margin2" or \
                prop == "baseObject" or \
                prop == "SwapEnds" or \
                prop == "TabHookDepth" or \
                prop == "TabHookLength" or \
                prop == "TabHookRadius" or \
                prop == "SwapHookDirection":
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
        return os.path.join(icons, 'tabs.svg')

    def setEdit(self, vobj, mode):
        if (mode != 0):
            return False #we only handle the detault mode

        laserhelper.lbActivateWorkbench()
        LBEnsureTabHookProperties(vobj.Object)
        taskd = LBTabsTaskPanel(True)
        taskd.obj = vobj.Object
        self.Object.AutoUpdate = False
        taskd.form.TabCount.setValue(self.Object.TabCount)
        taskd.form.TabWidth.setValue(self.Object.TabWidth)
        taskd.form.TabDepth.setValue(self.Object.TabDepth)
        taskd.form.GapWidth.setValue(self.Object.GapWidth)
        taskd.form.TabTaper.setValue(self.Object.TabTaper)
        taskd.form.TabMode.setCurrentText(self.Object.TabMode)
        taskd.form.SwapEnds.setChecked(self.Object.SwapEnds)
        taskd.form.Margin1.setValue(self.Object.Margin1)
        taskd.form.Margin2.setValue(self.Object.Margin2)
        taskd.form.TabHookDepth.setValue(self.Object.TabHookDepth)
        taskd.form.TabHookLength.setValue(self.Object.TabHookLength)
        taskd.form.TabHookRadius.setValue(self.Object.TabHookRadius)
        taskd.form.SwapHookDirection.setChecked(self.Object.SwapHookDirection)
        self.Object.AutoUpdate = True
        taskd.update()
        taskd.updateTabModeSwapEndsState()
        FreeCADGui.Control.showDialog(taskd)
        return True

    def unsetEdit(self, vobj, mode):
        if (mode != 0):
            return False #we only handle the detault mode
            
        FreeCADGui.Control.closeDialog()
        return False


class LBTabsViewProviderFlat:
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
            if  prop == "TabDepth" or \
                prop == "TabWidth" or \
                prop == "GapWidth" or \
                prop == "TabCount" or \
                prop == "TabTaper" or \
                prop == "Refine" or \
                prop == "TabMode" or \
                prop == "Margin1" or \
                prop == "Margin2" or \
                prop == "baseObject" or \
                prop == "SwapEnds" or \
                prop == "TabHookDepth" or \
                prop == "TabHookLength" or \
                prop == "TabHookRadius" or \
                prop == "SwapHookDirection":
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
        LBEnsureTabHookProperties(vobj.Object)
        taskd = LBTabsTaskPanel(True)
        taskd.obj = vobj.Object
        self.Object.AutoUpdate = False
        taskd.form.TabCount.setValue(self.Object.TabCount)
        taskd.form.TabWidth.setValue(self.Object.TabWidth)
        taskd.form.TabDepth.setValue(self.Object.TabDepth)
        taskd.form.GapWidth.setValue(self.Object.GapWidth)
        taskd.form.TabTaper.setValue(self.Object.TabTaper)
        taskd.form.TabMode.setCurrentText(self.Object.TabMode)
        taskd.form.SwapEnds.setChecked(self.Object.SwapEnds)
        taskd.form.Margin1.setValue(self.Object.Margin1)
        taskd.form.Margin2.setValue(self.Object.Margin2)
        taskd.form.TabHookDepth.setValue(self.Object.TabHookDepth)
        taskd.form.TabHookLength.setValue(self.Object.TabHookLength)
        taskd.form.TabHookRadius.setValue(self.Object.TabHookRadius)
        taskd.form.SwapHookDirection.setChecked(self.Object.SwapHookDirection)
        self.Object.AutoUpdate = True
        taskd.update()
        taskd.updateTabModeSwapEndsState()
        FreeCADGui.Control.showDialog(taskd)
        return True

    def unsetEdit(self,vobj,mode):
        if (mode != 0):
            return False #we only handle the detault mode
            
        FreeCADGui.Control.closeDialog()
        return False


class LBTabsTaskPanel:
    def __init__(self, editing):
        self.editing = editing
        self.obj = None
        # this will create a Qt widget from our ui file
        self.form = FreeCADGui.PySideUic.loadUi(path_to_ui)
        QtCore.QObject.connect(self.form.pbUpdateTabFaces, QtCore.SIGNAL("clicked()"), self.updateTabFaces)
        QtCore.QObject.connect(self.form.pbEditTabFaces, QtCore.SIGNAL("clicked()"), self.editTabFaces)
        # set some default values
        self.form.TabCount.setValue(0)
        self.form.TabWidth.setValue(10.0)
        self.form.TabDepth.setValue(3.0)
        self.form.GapWidth.setValue(10.0)
        self.form.TabTaper.setValue(0.0)
        self.form.TabMode.setCurrentIndex(0)
        self.form.SwapEnds.setChecked(False)
        self.form.Margin1.setValue(0.0)
        self.form.Margin2.setValue(0.0)
        self.form.TabHookDepth.setValue(0.0)
        self.form.TabHookLength.setValue(0.0)
        self.form.TabHookRadius.setValue(0.0)
        self.form.SwapHookDirection.setChecked(False)
        self.form.TabCount.valueChanged.connect(self.onTabCountChanged)
        self.form.TabWidth.valueChanged.connect(self.onTabWidthChanged)
        self.form.TabDepth.valueChanged.connect(self.onTabDepthChanged)
        self.form.GapWidth.valueChanged.connect(self.onGapWidthChanged)
        self.form.TabMode.currentTextChanged.connect(self.onTabModeChanged)
        self.form.SwapEnds.stateChanged.connect(self.onSwapEndsChanged)
        self.form.TabTaper.valueChanged.connect(self.onTabTaperChanged)
        self.form.Margin1.valueChanged.connect(self.onMargin1Changed)
        self.form.Margin2.valueChanged.connect(self.onMargin2Changed)
        self.form.TabHookDepth.valueChanged.connect(self.onTabHookDepthChanged)
        self.form.TabHookLength.valueChanged.connect(self.onTabHookLengthChanged)
        self.form.TabHookRadius.valueChanged.connect(self.onTabHookRadiusChanged)
        self.form.SwapHookDirection.stateChanged.connect(self.onSwapHookDirectionChanged)
        self.update()
        self.updateTabModeSwapEndsState()

    def updateTabModeSwapEndsState(self):
        """Disable TabMode and SwapEnds when TabCount is 0."""
        enabled = self.form.TabCount.value() != 0
        self.form.TabMode.setEnabled(enabled)
        self.form.SwapEnds.setEnabled(enabled and self.form.TabMode.currentText() == "From One End")

    def onTabCountChanged(self, val):
        self.updateTabModeSwapEndsState()
        if self.obj:
            if self.obj.TabMode == "From Both Ends":
                if val % 2 != 0:
                    #it needs to be an even number in this mode
                    if self.obj.TabCount > val:
                        val = val - 1
                    else:
                        val = val + 1

                    self.form.TabCount.setValue(val)
            self.obj.TabCount = val

    def onTabWidthChanged(self, val):
        self.obj.TabWidth = val

    def onTabDepthChanged(self, val):
        self.obj.TabDepth = val

    def onGapWidthChanged(self, val):
        self.obj.GapWidth = val

    def onTabModeChanged(self, val):
        if self.obj:
            self.obj.TabMode = val
        self.updateTabModeSwapEndsState()

        if self.obj and val == "From Both Ends":
            if self.obj.TabCount % 2 != 0:
                self.form.TabCount.setValue(self.obj.TabCount + 1)

    def onSwapEndsChanged(self, val):
        self.obj.SwapEnds = val

    def onSwapHookDirectionChanged(self, val):
        self.obj.SwapHookDirection = val

    def onTabTaperChanged(self, val):
        self.obj.TabTaper = val

    def onMargin1Changed(self, val):
        self.obj.Margin1 = val

    def onMargin2Changed(self, val):
        self.obj.Margin2 = val

    def onTabHookDepthChanged(self, val):
        self.obj.TabHookDepth = val

    def onTabHookLengthChanged(self, val):
        self.obj.TabHookLength = val

    def onTabHookRadiusChanged(self, val):
        self.obj.TabHookRadius = val

    def update(self):
        'fills the treeWidgetTabFaces'
        self.form.treeWidgetTabFaces.clear()
        if self.obj:
            f = self.obj.baseObject
            if isinstance(f[1], list):
                for subf in f[1]:
                    item = QtGui.QTreeWidgetItem(self.form.treeWidgetTabFaces)
                    item.setText(0, f[0].Name)
                    item.setIcon(0, QtGui.QIcon(":/icons/Tree_Part.svg"))
                    item.setText(1, subf)
            else:
                item = QtGui.QTreeWidgetItem(self.form.treeWidgetTabFaces)
                item.setText(0, f[0].Name)
                item.setIcon(0, QtGui.QIcon(":/icons/Tree_Part.svg"))
                item.setText(1, f[1][0])
        self.retranslateUi(self.form)

    def editTabFaces(self):
        print(f"edit tab faces")  
        self.obj.baseObject[0].ViewObject.Visibility = True
        self.obj.ViewObject.Visibility = False
        self.form.pbEditTabFaces.setEnabled(False)
        self.form.pbUpdateTabFaces.setEnabled(True)
        self.form.treeWidgetTabFaces.setEnabled(True)
        self.copyBaseObject = self.obj.baseObject

    def updateTabFaces(self):
        self.form.pbEditTabFaces.setEnabled(True)
        self.form.pbUpdateTabFaces.setEnabled(False)
        self.form.treeWidgetTabFaces.setEnabled(False)
        print(f"update tab faces")  
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
        self.form.pbUpdateTabFaces.setText(QtGui.QApplication.translate("draft", "Update", None))


'''My Command Class'''
class LBTabs:

    '''My new command'''
    def __init__(self):
        return

    '''Return the resources for this command'''
    def GetResources(self):
        return {'Pixmap': os.path.join(icons, 'tabs.svg'),
                'MenuText': "Add tabs to face",
                'ToolTip': "Add tabs to face"}

    '''Do something here'''
    def Activated(self):
        "Show the task panel so the user can specify the number of tabs etc"
        doc = FreeCAD.ActiveDocument
        view = Gui.ActiveDocument.ActiveView
        activeBody = None
        selobj = Gui.Selection.getSelectionEx()[0].Object
        
        if hasattr(view,'getActiveObject'):
            activeBody = view.getActiveObject('pdbody')
        
        if not laserhelper.lbIsOperationLegal(activeBody, selobj):
            return
        
        doc.openTransaction("Tabs")
        
        if activeBody is None or not laserhelper.lbIsPartDesign(selobj):
            a = doc.addObject("Part::FeaturePython","Tabs")
            cls = LBGenerateTabs(a)
            LBTabsViewProviderTree(a.ViewObject)
            a.AutoUpdate = True
            cls.execute(a)
        else:
            a = doc.addObject("PartDesign::FeaturePython","Tabs")
            cls = LBGenerateTabs(a)
            LBTabsViewProviderFlat(a.ViewObject)
            a.AutoUpdate = True
            activeBody.addObject(a)
            cls.execute(a)
        
        panel = LBTabsTaskPanel(False)
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
Gui.addCommand('LBTabs', LBTabs())
