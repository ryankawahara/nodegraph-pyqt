#!/usr/bin/env python
import maya.cmds as cmds
from unload_packages import *

unload_packages(silent=False, packages=["nodegraph", "rk_copyAnimation"])
from rk_copyAnimation import CopyAnimation
import copy
import sys

# import networkx
from Qt import QtWidgets, QtGui, QtCore
from nodegraph.scene import Scene
from nodegraph.view import View

WIDTH = 220

class ConnectionCollection:
    def __init__(self):
        self.connection_dict = {}
        print("hello there")

    def add(self, source_channel, target_channel, invert):
        newObj = ConnectionItem(target_channel, invert)
        if source_channel in self.connection_dict:
            # if target_channel not in self.connection_dict[source_channel]:
            if not self.contains(target_channel, source_channel):
                self.connection_dict[source_channel].append(newObj)
        else:
            self.connection_dict[source_channel] = [newObj]

        return newObj

    def remove(self, remove_source_name, remove_target_name):
        if remove_source_name in self.connection_dict:
            output_list = self.connection_dict[remove_source_name]
            # for item in output_list:
            #     print(str(item))
            if len(output_list) < 2:
                self.connection_dict.pop(remove_source_name)
            else:
                # print(remove_target_name)
                index = self.search_item_by_name(remove_target_name, output_list)
                # print(index)

                del output_list[index]
                # output_list.remove(index)
            return True
        else:
            return False

    def contains(self, search, source_channel):
        for val in self.connection_dict[source_channel]:
            # print(search, val, search in val)
            if search in val:
                return True
            # print('not found')
        return False

    def search_item_by_name(self, target_channel, output_list):
        # print("searching for", target_channel)
        # for item in output_list:
        #     print("checking", str(item))
        for item in output_list:
            if item.target_channel == target_channel:
                return output_list.index(item)
        return -1

    def toggle_invert(self, source_channel, target_channel):
        item_list = self.connection_dict[source_channel]
        index = self.search_item_by_name(target_channel, item_list)
        # print('before',item_list[index].invert )
        item_list[index].invert = not item_list[index].invert
        # print('after', item_list[index].invert)

    def set_invert(self, source_channel, target_channel, invert):
        item_list = self.connection_dict[source_channel]
        index = self.search_item_by_name(target_channel, item_list)
        item_list[index].invert = invert


class ConnectionItem:
    def __init__(self, target_channel, invert):
        self.target_channel = target_channel
        self.invert = invert

    def __str__(self):
        return f"{self.target_channel} {self.invert}"

    def __contains__(self, val):
        if val == self.target_channel:
            return True
        return False


class Input_window(QtWidgets.QWidget):
    def __init__(self, output_template=None):
        super(Input_window, self).__init__(parent=None)

        self.output_template = output_template
        self.setObjectName("Copy Animation")
        self.resize(500, 450)
        self.setMinimumSize(500, 350)
        self.setMaximumWidth(500)
        self.gridLayout = QtWidgets.QGridLayout(self)
        self.gridLayout.setObjectName("gridLayout")
        self.set_source = QtWidgets.QPushButton(self)
        self.set_source.setObjectName("set_source")
        # self.gridLayout.addWidget(self.set_source, 0, 0, 1, 1)
        self.gridLayout.addWidget(self.set_source, 1, 0, 1, 1)
        self.set_target = QtWidgets.QPushButton(self)
        self.set_target.setObjectName("set_target")
        # self.gridLayout.addWidget(self.set_target, 0, 1, 1, 1)
        self.gridLayout.addWidget(self.set_target, 1, 1, 1, 1)

        self.animation_copier = CopyAnimation()

        self.target_objects = []

        self.widget = QtWidgets.QWidget(self)
        self.widget.setObjectName("widget")

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.widget.sizePolicy().hasHeightForWidth())
        self.widget.setSizePolicy(sizePolicy)

        self.gridLayout.addWidget(self.widget, 3, 0, 1, 2)
        # self.gridLayout.addWidget(self.widget, 2, 0, 1, 2)
        self.window_size = self.widget.size()
        attr_dict_names, attr_dict = self.setup_attributes()
        self.nodegraph = NodeGraphWidget("main", parent=self, output_template=self.output_template,
                                         attributes=attr_dict)
        # self.nodegraph.mousePressEvent = lambda event: cmds.select(clear=True)
        self.gridLayout.addWidget(self.nodegraph, 3, 0, 1, 2)

        self.user_defined_targ_attrs = set()

        self.source = self.nodegraph.graph_scene.create_node(
            "Source",
            inputs=[],
            outputs=attr_dict_names,
            width=WIDTH,
            height=360,
            selectable=False,
            movable=False,
        )
        self.source.setPos(-200, 0)
        # self.source.setPos(self.nodegraph.graph_scene.width(), 0)

        self.target = self.nodegraph.graph_scene.create_node(
            "Target",
            inputs=attr_dict_names,
            outputs=[],
            width=WIDTH,
            height=360,
            selectable=False,
            movable=False,
        )

        self.target.setPos(150, 0)

        self.go_button = QtWidgets.QPushButton(self)
        self.go_button.setObjectName("go_button")
        self.gridLayout.addWidget(self.go_button, 4, 0, 1, 2)

        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.select_all_checkbox = QtWidgets.QCheckBox(self)
        self.select_all_checkbox.setObjectName("select_all_checkbox")
        self.horizontalLayout.addWidget(self.select_all_checkbox, 0, QtCore.Qt.AlignHCenter)
        self.invert_checkbox = QtWidgets.QCheckBox(self)
        self.invert_checkbox.setObjectName("invert_checkbox")
        self.horizontalLayout.addWidget(self.invert_checkbox, 0, QtCore.Qt.AlignHCenter)
        # self.gridLayout.addLayout(self.horizontalLayout, 1, 0, 1, 1)
        self.gridLayout.addLayout(self.horizontalLayout, 2, 0, 1, 1)

        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.all_attributes = QtWidgets.QCheckBox(self)
        self.all_attributes.setObjectName("all_attributes")
        self.all_attributes.setText("Show All Attributes")
        self.all_attributes.setToolTip("By default, only attributes shared by the selected objects are shown")
        self.all_attributes.clicked.connect(self.toggle_all_attributes)
        self.horizontalLayout_2.addWidget(self.all_attributes, 0, QtCore.Qt.AlignHCenter)
        self.gridLayout.addLayout(self.horizontalLayout_2, 2, 1, 1, 1)

        self.set_source.clicked.connect(self.set_source_object)
        self.go_button.clicked.connect(self.execute)
        self.set_target.clicked.connect(self.set_target_objects)

        self.setWindowTitle("Copy Animation")
        self.set_source.setText("Set Source")
        self.set_target.setText("Set Target")
        self.go_button.setText("Zhu Li! Do the thing!")
        self.invert_checkbox.setText("Invert All")
        self.select_all_checkbox.setText("Connect All")

        self.clear_button = QtWidgets.QPushButton(self)
        font = QtGui.QFont()
        font.setBold(False)
        font.setItalic(False)
        font.setWeight(50)
        self.clear_button.setFont(font)
        self.clear_button.setStyleSheet("background-color: rgb(255, 0, 127)")
        self.clear_button.setCheckable(False)
        self.clear_button.setObjectName("clear_button")
        self.clear_button.setText("Clear")

        self.invert_checkbox.stateChanged.connect(self.toggle_invert_all)
        self.select_all_checkbox.clicked.connect(self.connect_all_slots)
        self.clear_button.clicked.connect(self.delete_all_lines)
        # self.gridLayout.addWidget(self.clear_button, 1, 1, 1, 1)
        self.gridLayout.addWidget(self.clear_button, 0, 0, 1, 2)

        QtCore.QMetaObject.connectSlotsByName(self)

    # def resizeEvent(self, event: QtGui.QResizeEvent):
    #     print(self.widget.size())
    #     old_size = self.window_size
    #     old_area = old_size.width() * old_size.height()
    #     new_size = self.widget.size()
    #     new_area = new_size.width() * new_size.height()
    #     resize_scale = new_area/old_area
    #     print(new_area, old_area, new_area/old_area)
    #     self.window_size = new_size
    #
    #     view_center = self.nodegraph.graph_view.mapToScene(self.nodegraph.graph_view.viewport().rect().center())
    #     center = self.nodegraph.graph_view.sceneRect().center()
    #
    #     print(f"view center: {view_center}, center: {center}")
    #
    #     view_rect = self.nodegraph.graph_view.mapToScene(self.nodegraph.graph_view.viewport().rect())
    #     width = view_rect.boundingRect().width()
    #
    #
    #     # print("center", view_rect.center())
    #     diff = width-96
    #     # self.target.moveBy(25,0)
    #     # print("POS", 150+diff)
    #     # self.nodegraph.graph_view.scale_center_view(resize_scale)
    #     # source.setPos(self.nodegraph.graph_scene.width() - 200, 0)

    def toggle_all_attributes(self):

        prev_connects = []

        for active in self.target.active_inputs:
            edge = self.nodegraph.graph_scene.get_edge_by_hash(list(active._edge)[0])
            if edge:
                prev_connects.append(edge.slots)
        self.nodegraph.graph_scene.delete_all_edges(self.target.inputs[0])
        self.update_target_attributes()

        # does not work if more than 1 is connected. deletes. FIX!!!!
        for slot_pair in prev_connects:
            source = slot_pair[0]
            target = None

            for slot in self.target._inputs:
                if slot.name == slot_pair[1].name:
                    target = slot
                    break

            if target:
                new_edge = self.nodegraph.graph_scene.create_edge(source, target)

        self.update_target_title(self.target_objects)

    def keyPressEvent(self, event):
        if event.key() in [QtCore.Qt.Key_Delete, QtCore.Qt.Key_Backspace]:
            print("goodbye")
            self.select_all_checkbox.setChecked(False)

    def setup_attributes(self):
        outputs = [
            "Translate X",
            "Translate Y",
            "Translate Z",
            "Rotate X",
            "Rotate Y",
            "Rotate Z",
            "Scale X",
            "Scale Y",
            "Scale Z",
        ]


        attr_dict = {}
        for attr in outputs:
            attr_dict[attr] = attr.lower()[0] + attr.lower()[-1]

        attr_dict["Visibility"] = "visibility"
        # attr_dict[""] = ""

        attr_dict_names = attr_dict.keys()

        # insert spacers
        attr_dict_names = self.insert_gaps([3, 7, 11], attr_dict_names)

        return attr_dict_names, attr_dict

    def insert_gaps(self, spacer_index_locations, attr_dict_names):
        attr_dict_names = list(attr_dict_names)
        for indx in spacer_index_locations:
            attr_dict_names.insert(indx, "")

        return attr_dict_names

    def connect_all_slots(self):
        create_or_delete = self.select_all_checkbox.isChecked()
        self.nodegraph.graph_scene.delete_all_edges(self.target.inputs[0])
        self.nodegraph.graph_scene.connect_all_slots(self.source, self.target, create_or_delete)

    def delete_all_lines(self):
        self.select_all_checkbox.setChecked(False)
        self.nodegraph.graph_scene.delete_all_edges(self.target._inputs[0])

    def toggle_invert_all(self):
        invert_or_deinvert = self.invert_checkbox.isChecked()
        self.nodegraph.graph_scene.invert_new_edges = invert_or_deinvert
        self.nodegraph.graph_scene.toggle_invert_all_edges(self.target._inputs[0], invert_or_deinvert)

    def execute(self):
        invert = self.invert_checkbox.isChecked()
        # self.animation_copier.clear_target_channels()
        # try:
        channel_dict = self.nodegraph.graph_scene.connections_dict.items()
        res = ""
        if len(channel_dict) == 0:
            warning = QtWidgets.QMessageBox()
            warning.setText("No nodes selected")
            warning.setIcon(QtWidgets.QMessageBox.Warning)
            warning.exec()
            return
        for key, val in self.nodegraph.graph_scene.connections_dict.items():

            res += f"|{key}|"
            for v in val:
                res += f"[{v}]"
            res += ", "
        print(res)
        # self.animation_copier.store_target(target_objects)
        # if len(self.target_objects) == 0 or not self.source

        if len(self.animation_copier.source) == 0 or len(self.animation_copier.target) == 0:
            if len(self.animation_copier.source) == 0:
                warning = QtWidgets.QMessageBox()
                warning.setText("No source selected")
                warning.setIcon(QtWidgets.QMessageBox.Warning)
                warning.exec()

            if len(self.animation_copier.target) == 0:
                warning = QtWidgets.QMessageBox()
                warning.setText("No target selected")
                warning.setIcon(QtWidgets.QMessageBox.Warning)
                warning.exec()
            return

        for obj in self.target_objects:
            self.animation_copier.store_target(obj)
            for source_chan, target_chan_list in self.nodegraph.graph_scene.connections_dict.items():
                self.animation_copier.clear_target_channels()
                self.animation_copier.set_source_channel(source_chan)
                for target_chan in target_chan_list:
                    self.animation_copier.set_target_channel(target_chan.target_channel)
                    self.animation_copier.copyAnimation(invert=target_chan.invert)

        #
        # for obj in self.target_objects:
        #     self.animation_copier.store_target(obj)
        #
        #     for src, targets in channel_dict.items():
        #         self.animation_copier.clear_target_channels()
        #         self.animation_copier.set_source_channel(src)
        #         for trgt in targets:
        #             print(src, trgt)
        #             self.animation_copier.set_target_channel(trgt)
        #             print(self.animation_copier.source, self.animation_copier.target, self.animation_copier.selectedTargets, self.animation_copier.sourceChannel)
        #
        #             self.animation_copier.copyAnimation()
        #
        # except UnboundLocalError as e:
        #     pass

    def add_user_defined_attributes(self, node, ud_attr):
        self.nodegraph.graph_scene.delete_node(node)
        attr_dict_names, attr_dict = self.setup_attributes()
        attr_dict_names.append("")
        attr_dict_names += ud_attr

        for attr in ud_attr:
            self.nodegraph.attributes[attr] = attr

        return attr_dict_names

    def reset_source_node(self):
        self.nodegraph.graph_scene.delete_node(self.source)
        attr_dict_names, attr_dict = self.setup_attributes()

        self.source = self.nodegraph.graph_scene.create_node(
            "Source",
            inputs=[],
            outputs=attr_dict_names,
            width=WIDTH,
            height=360,
            selectable=False,
            movable=False,
        )
        print("hi")
        self.source.setPos(-200, 0)
        self.source.refresh()

    def reset_target_node(self):
        # save connections

        self.nodegraph.graph_scene.delete_node(self.target)
        attr_dict_names, attr_dict = self.setup_attributes()

        self.target = self.nodegraph.graph_scene.create_node(
            "Target",
            inputs=attr_dict_names,
            outputs=[],
            width=WIDTH,
            height=360,
            selectable=False,
            movable=False,
        )
        self.target.setPos(150, 0)
        # reconnect

    def set_source_object(self):
        sel = cmds.ls(sl=True)
        if len(sel) > 0:
            source_item = sel[0]
            ud_attr = cmds.listAttr(source_item, ud=True)
            if ud_attr:
                attr_dict_names = self.add_user_defined_attributes(self.source, ud_attr)

                self.source = self.nodegraph.graph_scene.create_node(
                    "Source",
                    inputs=[],
                    outputs=attr_dict_names,
                    width=WIDTH,
                    height=360,
                    selectable=False,
                    movable=False,
                )
                self.source.setPos(-200, 0)
            else:
                # reset to default
                self.reset_source_node()
            self.animation_copier.clear_source()
            self.animation_copier.store_source(source_item)
            self.source._update_title(source_item)

        else:
            self.source._update_title("Source")
            self.reset_source_node()
            warning = QtWidgets.QMessageBox()
            warning.setText("No source item selected")
            warning.setIcon(QtWidgets.QMessageBox.Warning)
            warning.exec()

    def update_target_attributes(self):
        shared_targ_attrs = set()
        if len(self.target_objects) > 0:
            shared_targ_attrs = set(cmds.listAttr(self.target_objects[0], ud=True))
            if self.all_attributes.isChecked() == False:
                for obj in self.target_objects[1:]:
                    shared_targ_attrs.intersection_update(cmds.listAttr(obj, ud=True))
            else:
                for obj in self.target_objects[1:]:
                    shared_targ_attrs.update(cmds.listAttr(obj, ud=True))

        self.user_defined_targ_attrs = shared_targ_attrs

        if len(shared_targ_attrs) > 0:
            attr_dict_names = self.add_user_defined_attributes(self.target, list(shared_targ_attrs))

            self.target = self.nodegraph.graph_scene.create_node(
                "Target",
                inputs=attr_dict_names,
                outputs=[],
                width=WIDTH,
                height=360,
                selectable=False,
                movable=False,
            )
            self.target.setPos(150, 0)
        else:
            self.reset_target_node()

    def set_target_objects(self):
        print('hi')
        self.animation_copier.clear_target()
        sel = cmds.ls(sl=True)

        if sel:
            custom_attr = cmds.listAttr(sel[0], ud=True)
            if custom_attr:
                shared_targ_attrs = set(custom_attr)

                if self.all_attributes.isChecked() == False:
                    for obj in sel[1:]:
                        shared_targ_attrs.intersection_update(cmds.listAttr(obj, ud=True))
                else:
                    for obj in sel[1:]:
                        shared_targ_attrs.update(cmds.listAttr(obj, ud=True))

                if len(shared_targ_attrs) > 0:
                    attr_dict_names = self.add_user_defined_attributes(self.target, list(shared_targ_attrs))

                    self.target = self.nodegraph.graph_scene.create_node(
                        "Target",
                        inputs=attr_dict_names,
                        outputs=[],
                        width=WIDTH,
                        height=360,
                        selectable=False,
                        movable=False,
                    )
                    self.target.setPos(150, 0)
                    # self.target._height
                    print("DIFF", self.target.full_height - self.target._height)
                    self.resize(self.width(), self.height() + self.target.full_height)
                    print("no")
                else:
                    print("ohhhh this should gos")
                    self.reset_target_node()

                self.target_objects = sel
                self.update_target_title(self.target_objects)
                # if len(sel) > 1:
                #     self.target._update_title(f"{len(self.target_objects)} Objects")
                #     objs = ''.join(f'{obj}\n' for obj in self.target_objects)
                #     objs = objs.strip()
                #     self.target.setToolTip(objs)
                # elif len(sel) == 1:
                #     self.target._update_title(self.target_objects[0])
                #
                # else:
                #     self.target._update_title("Target")
                #     self.reset_target_node()
                #     warning = QtWidgets.QMessageBox()
                #     warning.setText("No target items selected")
                #     warning.setIcon(QtWidgets.QMessageBox.Warning)
                #     warning.exec()
            else:
                self.reset_target_node()
                self.target_objects = sel
                self.update_target_title(self.target_objects)

    def update_target_title(self, target_objects):
        if len(target_objects) > 1:
            self.target._update_title(f"{len(self.target_objects)} Objects")
            objs = ''.join(f'{obj}\n' for obj in self.target_objects)
            objs = objs.strip()
            self.target.setToolTip(objs)
        elif len(target_objects) == 1:
            self.target._update_title(self.target_objects[0])

        else:
            self.target._update_title("Target")
            self.reset_target_node()
            self.all_attributes.setChecked(False)
            warning = QtWidgets.QMessageBox()
            warning.setText("No target items selected")
            warning.setIcon(QtWidgets.QMessageBox.Warning)
            warning.exec()

        # test.store_source("pCube1")
        # test.store_target("pCube2")
        # test.set_source_channel("ty")
        # test.set_target_channel("tz")
        # test.copyAnimation()
        # self.source._update_title("Ryan")


class NodeGraphWidget(QtWidgets.QWidget):
    """
    Handles node graph view
    """

    def __init__(self, name, parent=None, output_template=None, attributes=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.name = name
        self.parent = parent
        self.attributes = attributes

        # convert_func = lambda name:name.lower()[0] + name.lower()[-1]
        self.graph_scene = Scene(parent=self.parent,
                                 nodegraph_widget=self,
                                 multiple_input_allowed=False,
                                 # convert = convert_func,
                                 output_template=output_template,
                                 attributes=self.attributes)
        self.graph_view = View(self.graph_scene, parent=self.parent, is_zoom=False, scale=0.85)
        self.graph_view.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)
        # self.graph_view.mousePressedEvent = lambda event: cmds.select(clear=True)
        # find out why it's not scaling!!!!
        self.horizontal_layout = QtWidgets.QHBoxLayout(self)
        self.horizontal_layout.addWidget(self.graph_view)

        self.setMouseTracking(True)

    # def mousePressEvent(self, event):
    #     cmds.select(clear=True)


if __name__ == "__main__":

    window_name = "Copy Animation"

    # this prevents duplication of the window
    if cmds.window(window_name, ex=True):
        cmds.deleteUI(window_name)

    box = Input_window(output_template=ConnectionCollection())
    box.show()

# add break node shortcut
