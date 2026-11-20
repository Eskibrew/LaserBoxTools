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
#from ..features import make_box_feature_object as make_box_feature_object
from ..src.make_box import laser_make_box_pieces_simple, laser_make_box_pieces


__dir__ = os.path.dirname(__file__)
path_to_ui = os.path.join(__dir__, '../resources/ui/makebox.ui')


class LaserMakeBoxTaskPanel:
    """MakeBox - Task panel for the MakeBox feature"""

    def __init__(self, params_obj):
        self.params_obj = params_obj
        self.form = App.Gui.PySideUic.loadUi(path_to_ui)
        self.form.rbPartDesign.setChecked(True)
        self.form.cbTop.setChecked(True)
        self.form.cbBottom.setChecked(True)
        self.form.cbLeft.setChecked(True)
        self.form.cbRight.setChecked(True)
        self.form.cbFront.setChecked(True)
        self.form.cbBack.setChecked(True)
        self.form.cbUseTabsAndSlots.setChecked(False)
        self.bindExpressions()

    def bindExpressions(self):
        obj = self.params_obj
        laserhelper.lbBindQuantitySpinBox(self.form.BoxLength, obj, "BoxLength")
        laserhelper.lbBindQuantitySpinBox(self.form.BoxWidth, obj, "BoxWidth")
        laserhelper.lbBindQuantitySpinBox(self.form.BoxHeight, obj, "BoxHeight")
        laserhelper.lbBindQuantitySpinBox(self.form.BoxThickness, obj, "BoxThickness")
        laserhelper.lbBindIntSpinBox(self.form.TabSlotCount, obj, "TabSlotCount")
        laserhelper.lbBindQuantitySpinBox(self.form.TabSlotWidth, obj, "TabSlotWidth")
        laserhelper.lbBindQuantitySpinBox(self.form.GapWidth, obj, "GapWidth")
        laserhelper.lbBindQuantitySpinBox(self.form.TabTaper, obj, "TabTaper")
        laserhelper.lbBindQuantitySpinBox(self.form.Kerf, obj, "Kerf")

    def _removeParamsObject(self):
        doc = App.ActiveDocument
        if self.params_obj and doc.getObject(self.params_obj.Name):
            doc.removeObject(self.params_obj.Name)

    def accept(self):
        length = self.params_obj.BoxLength.Value
        width = self.params_obj.BoxWidth.Value
        height = self.params_obj.BoxHeight.Value
        thickness = self.params_obj.BoxThickness.Value

        if length == 0:
            laserhelper.laser_show_error_message('length cannot be zero!')
            return

        if width == 0:
            laserhelper.laser_show_error_message('width cannot be zero!')
            return

        if height == 0:
            laserhelper.laser_show_error_message('height cannot be zero!')
            return

        if thickness == 0:
            laserhelper.laser_show_error_message('thickness cannot be zero!')
            return

        if not self.form.cbTop.isChecked() and not self.form.cbBottom.isChecked() and not self.form.cbLeft.isChecked() and not self.form.cbRight.isChecked() and not self.form.cbFront.isChecked() and not self.form.cbBack.isChecked():
            laserhelper.laser_show_error_message('At least one box part must be selected!')
            return

        tab_slot_count = self.params_obj.TabSlotCount
        tab_slot_width = self.params_obj.TabSlotWidth.Value
        tab_taper = self.params_obj.TabTaper.Value
        gap_width = self.params_obj.GapWidth.Value
        kerf = self.params_obj.Kerf.Value

        self._removeParamsObject()

        if self.form.rbPart.isChecked():
            laser_make_box_pieces_simple(length, width, height, thickness,
                                                                self.form.cbTop.isChecked(),
                                                                self.form.cbBottom.isChecked(),
                                                                self.form.cbLeft.isChecked(),
                                                                self.form.cbRight.isChecked(),
                                                                self.form.cbFront.isChecked(),
                                                                self.form.cbBack.isChecked(),
                                                                self.form.cbUseTabsAndSlots.isChecked(),
                                                                tab_slot_count,
                                                                tab_slot_width,
                                                                tab_taper,
                                                                gap_width,
                                                                "From Middle",
                                                                0,
                                                                0,
                                                                kerf=kerf
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
                                                        tab_slot_count,
                                                        tab_slot_width,
                                                        tab_taper,
                                                        gap_width,
                                                        "From Middle",
                                                        0,
                                                        0,
                                                        kerf=kerf
                                                        )
        App.Gui.Control.closeDialog()
        view = App.Gui.ActiveDocument.ActiveView
        if view:
            view.fitAll()
            view.viewIsometric()

    def reject(self):
        self._removeParamsObject()
        App.Gui.Control.closeDialog()


