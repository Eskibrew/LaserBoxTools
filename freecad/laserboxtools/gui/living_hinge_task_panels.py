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
path_to_ui = os.path.join(__dir__, '../resources/ui/hinge.ui')


class LBLivingHingeTaskPanel:
    def __init__(self, editing):
        self.editing = editing
        self.obj = None
        self._expressionBound = False
        # this will create a Qt widget from our ui file
        self.form = App.Gui.PySideUic.loadUi(path_to_ui)
        QtCore.QObject.connect(self.form.pbUpdateElementFaces, QtCore.SIGNAL("clicked()"), self.updateElementFaces)
        QtCore.QObject.connect(self.form.pbEditElementFaces, QtCore.SIGNAL("clicked()"), self.editElementFaces)
        self.form.ElementMode.setCurrentIndex(0)
        self.form.ElementType.setCurrentIndex(0)
        self.form.SwapEnds.setChecked(False)
        self.form.Autofill.stateChanged.connect(self.onAutofillChanged)
        self.form.ElementCount.valueChanged.connect(self.onElementCountChanged)
        self.form.ElementMode.currentTextChanged.connect(self.onElementModeChanged)
        self.form.ElementType.currentTextChanged.connect(self.onElementTypeChanged)
        self.form.SwapEnds.stateChanged.connect(self.onSwapEndsChanged)
        self._applyAutofillElementCount(self.form.Autofill.isChecked(), write_count=False)
        self.update()

    def _applyAutofillElementCount(self, autofill, write_count):
        """Put the ElementCount spin box into the state Autofill requires.

        Enabled state and minimum are updated before the value. The spin box
        clamps anything outside its range, and the expression binding writes
        that clamped value back onto the object. Signals stay blocked for the
        whole update so that write-back, and the even-count adjustment, cannot
        run against the old minimum.
        """
        spin = self.form.ElementCount
        # Minimum stays 1 when Autofill is off so a smaller count can still be chosen.
        # The value itself returns to 4, the count a new hinge is created with.
        minimum = 0 if autofill else 1
        count = 0 if autofill else 4
        spin.blockSignals(True)
        try:
            spin.setEnabled(not autofill)
            spin.setProperty("minimum", minimum)
            if write_count and self.obj:
                # Autofill leaves ElementCount read-only in the Data pane.
                self.obj.setEditorMode("ElementCount", 0)
            if write_count:
                spin.setProperty("value", count)
                if self.obj:
                    self.obj.ElementCount = count
        finally:
            spin.blockSignals(False)
        self.updateElementModeSwapEndsState()

    def bindExpressions(self):
        if self._expressionBound or not self.obj:
            return
        obj = self.obj
        # Minimum must already allow the stored count before the binder copies it in.
        self._applyAutofillElementCount(bool(obj.Autofill), write_count=False)
        laserhelper.lbBindIntSpinBox(self.form.ElementCount, obj, "ElementCount")
        laserhelper.lbBindQuantitySpinBox(self.form.ElementWidth, obj, "ElementWidth")
        laserhelper.lbBindQuantitySpinBox(self.form.ElementDepth, obj, "ElementDepth")
        laserhelper.lbBindQuantitySpinBox(self.form.ElementSpacing, obj, "ElementSpacing")
        laserhelper.lbBindQuantitySpinBox(self.form.Margin1, obj, "Margin1")
        laserhelper.lbBindQuantitySpinBox(self.form.Margin2, obj, "Margin2")
        self.form.ElementMode.setCurrentText(obj.ElementMode)
        self.form.ElementType.setCurrentText(obj.ElementType)
        self.form.SwapEnds.setChecked(obj.SwapEnds)
        blocked = self.form.Autofill.blockSignals(True)
        self.form.Autofill.setChecked(bool(obj.Autofill))
        self.form.Autofill.blockSignals(blocked)
        self._expressionBound = True
        self.updateElementModeSwapEndsState()

    def onAutofillChanged(self, val):
        if not self.obj:
            return
        # stateChanged passes Qt.Checked (2) or Qt.Unchecked (0).
        autofill = bool(val)
        self._applyAutofillElementCount(autofill, write_count=True)
        self.obj.Autofill = autofill

    def updateElementModeSwapEndsState(self):
        """Disable ElementMode and SwapEnds when ElementCount is 0."""
        count = self.form.ElementCount.property("value") if self._expressionBound else self.form.ElementCount.value()
        enabled = count != 0
        self.form.ElementMode.setEnabled(enabled)
        self.form.SwapEnds.setEnabled(enabled and self.form.ElementMode.currentText() == "From One End")

    def onElementCountChanged(self, val):
        self.updateElementModeSwapEndsState()
        if self.obj and self.obj.ElementMode == "From Both Ends":
            if val % 2 != 0:
                if self.obj.ElementCount > val:
                    val = val - 1
                else:
                    val = val + 1
                self.form.ElementCount.setProperty("value", val)

    def onElementModeChanged(self, val):
        if self.obj:
            self.obj.ElementMode = val
        self.updateElementModeSwapEndsState()

        if self.obj and val == "From Both Ends":
            if self.obj.ElementCount % 2 != 0:
                self.form.ElementCount.setProperty("value", self.obj.ElementCount + 1)

    def onElementTypeChanged(self, val):
        if self.obj:
            self.obj.ElementType = val

    def onSwapEndsChanged(self, val):
        self.obj.SwapEnds = val

    def update(self):
        if self.obj:
            self.bindExpressions()
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

            if self.obj.Autofill:
                self._applyAutofillElementCount(True, write_count=False)
            elif self.obj.ElementCount == 0:
                self._applyAutofillElementCount(False, write_count=True)
            else:
                self._applyAutofillElementCount(False, write_count=False)

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
