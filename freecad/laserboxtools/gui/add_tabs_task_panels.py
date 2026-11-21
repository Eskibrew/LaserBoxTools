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
path_to_ui = os.path.join(__dir__, '../resources/ui/tabs.ui')


class LBTabsTaskPanel:
    """MakeBox - Task panel for the MakeBox feature"""

    def __init__(self, editing):
        self.editing = editing
        self.obj = None
        self._expressionBound = False
        # this will create a Qt widget from our ui file
        self.form = App.Gui.PySideUic.loadUi(path_to_ui)
        QtCore.QObject.connect(self.form.pbUpdateTabFaces, QtCore.SIGNAL("clicked()"), self.updateTabFaces)
        QtCore.QObject.connect(self.form.pbEditTabFaces, QtCore.SIGNAL("clicked()"), self.editTabFaces)
        self.form.TabMode.setCurrentIndex(0)
        self.form.SwapEnds.setChecked(False)
        self.form.SwapHookDirection.setChecked(False)
        self.form.Autofill.stateChanged.connect(self.onAutofillChanged)
        self.form.TabCount.valueChanged.connect(self.onTabCountChanged)
        self.form.TabMode.currentTextChanged.connect(self.onTabModeChanged)
        self.form.SwapEnds.stateChanged.connect(self.onSwapEndsChanged)
        self.form.SwapHookDirection.stateChanged.connect(self.onSwapHookDirectionChanged)
        self._applyAutofillTabCount(self.form.Autofill.isChecked(), write_count=False)
        self.update()

    def _applyAutofillTabCount(self, autofill, write_count):
        """Put the TabCount spin box into the state Autofill requires.

        Enabled state and minimum are updated before the value. The spin box
        clamps anything outside its range, and the expression binding writes
        that clamped value back onto the object. Signals stay blocked for the
        whole update so that write-back, and the even-count adjustment, cannot
        run against the old minimum.
        """
        spin = self.form.TabCount
        count = 0 if autofill else 1
        spin.blockSignals(True)
        try:
            spin.setEnabled(not autofill)
            spin.setProperty("minimum", count)
            if write_count and self.obj:
                # Autofill leaves TabCount read-only in the Data pane.
                self.obj.setEditorMode("TabCount", 0)
            if write_count:
                spin.setProperty("value", count)
                if self.obj:
                    self.obj.TabCount = count
        finally:
            spin.blockSignals(False)

    def bindExpressions(self):
        if self._expressionBound or not self.obj:
            return
        obj = self.obj
        # Minimum must already allow the stored count before the binder copies it in.
        self._applyAutofillTabCount(bool(obj.Autofill), write_count=False)
        laserhelper.lbBindIntSpinBox(self.form.TabCount, obj, "TabCount")
        laserhelper.lbBindQuantitySpinBox(self.form.TabWidth, obj, "TabWidth")
        laserhelper.lbBindQuantitySpinBox(self.form.TabDepth, obj, "TabDepth")
        laserhelper.lbBindQuantitySpinBox(self.form.GapWidth, obj, "GapWidth")
        laserhelper.lbBindQuantitySpinBox(self.form.TabTaper, obj, "TabTaper")
        laserhelper.lbBindQuantitySpinBox(self.form.Margin1, obj, "Margin1")
        laserhelper.lbBindQuantitySpinBox(self.form.Margin2, obj, "Margin2")
        laserhelper.lbBindQuantitySpinBox(self.form.TabHookDepth, obj, "TabHookDepth")
        laserhelper.lbBindQuantitySpinBox(self.form.TabHookLength, obj, "TabHookLength")
        laserhelper.lbBindQuantitySpinBox(self.form.TabHookRadius, obj, "TabHookRadius")
        laserhelper.lbBindQuantitySpinBox(self.form.Kerf, obj, "Kerf")
        self.form.TabMode.setCurrentText(obj.TabMode)
        self.form.SwapEnds.setChecked(obj.SwapEnds)
        self.form.SwapHookDirection.setChecked(obj.SwapHookDirection)
        blocked = self.form.Autofill.blockSignals(True)
        self.form.Autofill.setChecked(bool(obj.Autofill))
        self.form.Autofill.blockSignals(blocked)
        self._expressionBound = True

    def onAutofillChanged(self, val):
        if not self.obj:
            return
        # stateChanged passes Qt.Checked (2) or Qt.Unchecked (0).
        autofill = bool(val)
        self._applyAutofillTabCount(autofill, write_count=True)
        self.obj.Autofill = autofill

    def onTabCountChanged(self, val):
        if self.obj and self.obj.TabMode == "From Both Ends":
            if val % 2 != 0:
                if self.obj.TabCount > val:
                    val = val - 1
                else:
                    val = val + 1
                self.form.TabCount.setProperty("value", val)

    def onTabModeChanged(self, val):
        if self.obj:
            self.obj.TabMode = val

        if self.obj and val == "From Both Ends":
            if self.obj.TabCount % 2 != 0:
                self.form.TabCount.setProperty("value", self.obj.TabCount + 1)

    def onSwapEndsChanged(self, val):
        self.obj.SwapEnds = val

    def onSwapHookDirectionChanged(self, val):
        self.obj.SwapHookDirection = val

    def update(self):
        if self.obj:
            self.bindExpressions()
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
            
            if self.obj.Autofill:
                self._applyAutofillTabCount(True, write_count=False)
            elif self.obj.TabCount == 0:
                self._applyAutofillTabCount(False, write_count=True)
            else:
                self._applyAutofillTabCount(False, write_count=False)

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


