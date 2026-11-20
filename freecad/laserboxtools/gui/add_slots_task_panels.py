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
import os
from PySide import QtCore, QtGui

from ..src import laser_helper as laserhelper


__dir__ = os.path.dirname(__file__)
path_to_ui = os.path.join(__dir__, '../resources/ui/slots.ui')


class LBSlotsTaskPanel:
    """MakeBox - Task panel for the MakeBox feature"""

    def __init__(self, editing):
        self.editing = editing
        self.obj = None
        self._expressionBound = False
        # this will create a Qt widget from our ui file
        self.form = App.Gui.PySideUic.loadUi(path_to_ui)
        QtCore.QObject.connect(self.form.pbUpdateSlotFaces, QtCore.SIGNAL("clicked()"), self.updateSlotFaces)
        QtCore.QObject.connect(self.form.pbEditSlotFaces, QtCore.SIGNAL("clicked()"), self.editSlotFaces)
        self.form.SlotMode.setCurrentIndex(0)
        self.form.SwapEnds.setChecked(False)
        self.form.SwapHookDirection.setChecked(False)
        self.form.SlotCount.valueChanged.connect(self.onSlotCountChanged)
        self.form.SlotMode.currentTextChanged.connect(self.onSlotModeChanged)
        self.form.SwapEnds.stateChanged.connect(self.onSwapEndsChanged)
        self.form.SwapHookDirection.stateChanged.connect(self.onSwapHookDirectionChanged)
        self.form.OffsetFromFace.valueChanged.connect(self.onOffsetFromFaceChanged)
        self.update()
        self.updateSlotDepthLabel()

    def bindExpressions(self):
        if self._expressionBound or not self.obj:
            return
        obj = self.obj
        laserhelper.lbBindIntSpinBox(self.form.SlotCount, obj, "SlotCount")
        laserhelper.lbBindQuantitySpinBox(self.form.SlotLength, obj, "SlotLength")
        laserhelper.lbBindQuantitySpinBox(self.form.SlotDepth, obj, "SlotDepth")
        laserhelper.lbBindQuantitySpinBox(self.form.GapWidth, obj, "GapWidth")
        laserhelper.lbBindQuantitySpinBox(self.form.Margin1, obj, "Margin1")
        laserhelper.lbBindQuantitySpinBox(self.form.Margin2, obj, "Margin2")
        laserhelper.lbBindQuantitySpinBox(self.form.OffsetFromFace, obj, "OffsetFromFace", self.updateSlotDepthLabel)
        laserhelper.lbBindQuantitySpinBox(self.form.SlotHookLength, obj, "SlotHookLength")
        laserhelper.lbBindQuantitySpinBox(self.form.Kerf, obj, "Kerf")
        self.form.SlotMode.setCurrentText(obj.SlotMode)
        self.form.SwapEnds.setChecked(obj.SwapEnds)
        self.form.SwapHookDirection.setChecked(obj.SwapHookDirection)
        self._expressionBound = True

    def onSlotCountChanged(self, val):
        if self.obj and self.obj.SlotMode == "From Both Ends":
            if val % 2 != 0:
                if self.obj.SlotCount > val:
                    val = val - 1
                else:
                    val = val + 1
                self.form.SlotCount.setProperty("value", val)

    def onSlotModeChanged(self, val):
        if self.obj:
            self.obj.SlotMode = val

        if self.obj and val == "From Both Ends":
            if self.obj.SlotCount % 2 != 0:
                self.form.SlotCount.setProperty("value", self.obj.SlotCount + 1)

    def onSwapEndsChanged(self, val):
        self.obj.SwapEnds = val

    def onSwapHookDirectionChanged(self, val):
        self.obj.SwapHookDirection = val

    def onOffsetFromFaceChanged(self, val):
        self.updateSlotDepthLabel()

    def updateSlotDepthLabel(self):
        """Update Slot Depth label based on OffsetFromFace value"""
        offset = self.obj.OffsetFromFace.Value if self.obj else 0.0
        label = self.form.label_3 if self.form else None
        if label:
            label.setText("Slot Width" if offset != 0.0 else "Slot Depth")

    def update(self):
        if self.obj:
            self.bindExpressions()
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
            if len(App.Gui.Selection.getSelectionEx()) < 1:
                laserhelper.lbErrorMessage("Error: Invalid selection")
            else:
                sel = App.Gui.Selection.getSelectionEx()[0]
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

    def _removeParamsObject(self):
        doc = App.ActiveDocument
        if self.params_obj and doc.getObject(self.params_obj.Name):
            doc.removeObject(self.params_obj.Name)

    def accept(self):
        App.ActiveDocument.recompute()
        App.ActiveDocument.commitTransaction()
        App.Gui.Control.closeDialog()
        App.Gui.ActiveDocument.resetEdit()
        return True

    def reject(self):
        if not self.editing:  # creating: abort transaction to undo creation
            self.obj.baseObject[0].ViewObject.Visibility = True
            self.obj.ViewObject.Visibility = False
        if App.ActiveDocument.HasPendingTransaction:
            App.ActiveDocument.abortTransaction()
        App.ActiveDocument.recompute()
        App.Gui.Control.closeDialog()


