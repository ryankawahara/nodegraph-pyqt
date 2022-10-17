#!/usr/bin/env python
import maya.cmds as cmds
from unload_packages import *
unload_packages(silent=False, packages=["nodegraph", "rk_copyAnimation"])
from rk_copyAnimation import CopyAnimation
# import os
import sys

# import networkx
from Qt import QtWidgets, QtGui, QtCore

from nodegraph.scene import Scene
from nodegraph.view import View

class ConnectionCollection:
    def __init__(self):
        self.connection_dict = {}
        print("hello there")

    def add(self, source_channel, target_channel, invert):
        if source_channel in self.connection_dict:
            # if target_channel not in self.connection_dict[source_channel]:
            if not self.contains(target_channel, source_channel):
                self.connection_dict[source_channel].append(ConnectionItem(target_channel, invert))
        else:
            self.connection_dict[source_channel] = [ConnectionItem(target_channel, invert)]

    def remove(self, remove_source_name, remove_target_name):
        if remove_source_name in self.connection_dict:
            output_list = self.connection_dict[remove_source_name]
            for item in output_list:
                print(str(item))
            if len(output_list) < 2:
                self.connection_dict.pop(remove_source_name)
            else:
                print(remove_target_name)
                index = self.search_item_by_name(remove_target_name, output_list)   
                print(index)

                del output_list[index]
                # output_list.remove(index)
            return True
        else:
            return False

    def contains(self, search, source_channel):
        for val in self.connection_dict[source_channel]:
            print(search, val, search in val)
            if search in val:
                return True
            print('not found')
        return False

    def search_item_by_name(self, target_channel, output_list):
        print("searching for", target_channel)
        for item in output_list:
            print("checking", str(item))
        for item in output_list:
            if item.target_channel == target_channel:
                return output_list.index(item)
        return -1

    def toggle_invert(self, source_channel, target_channel):
        item_list = self.connection_dict[source_channel]
        index = self.search_item_by_name(target_channel, item_list)
        print('before',item_list[index].invert )
        item_list[index].invert = not item_list[index].invert
        print('after', item_list[index].invert)

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
        print("CONTAINS", val == self.target_channel, type(val), type(self.target_channel))
        if val == self.target_channel:
            print("contains")
            return True
        return False



class NodeGraphDialog(QtWidgets.QMainWindow):

    """
    Handles top level dialog of Node grap
    """

    def __init__(self, parent=None):


        QtWidgets.QMainWindow.__init__(self, parent)
        self.parent = parent or self

        self.nodegraph = NodeGraphWidget("main", parent=self.parent)
        self.setCentralWidget(self.nodegraph)
        self.resize(800, 600)
        self.setWindowTitle("Node graph -")

        # center = self.nodegraph.graph_view.sceneRect().center()
        source = self.nodegraph.graph_scene.create_node(
            "Source",
            inputs=[],
            outputs=[
                "All",
                "Translate X",
                "Translate Y",
                "Translate Z",
                "Rotate X",
                "Rotate Y",
                "Rotate Z",
                "Scale X",
                "Scale Y",
                "Scale Z",
                "csV"
            ],
            width=180,
            height=360,
            selectable = False,
            movable = False,
        )
        source.setPos(-200, 0)
        target = self.nodegraph.graph_scene.create_node(
            "Target",
            inputs=[
                "All",
                "Translate X",
                "Translate Y",
                "Translate Z",
                "Rotate X",
                "Rotate Y",
                "Rotate Z",
                "Scale X",
                "Scale Y",
                "Scale Z",
                "Visibility"
            ],
            outputs=[],
            width = 180,
            height = 360,
            selectable = False,
            movable = False,
        )
        target.setPos(150, 0)
        # edge = self.nodegraph.graph_scene.create_edge(
           # cam._outputs[0],
           # model._inputs[0])


        # target._update_title("Ryan")
        # object_methods = [method_name for method_name in dir(target)
        #                   if callable(getattr(target, method_name))]
        # print(object_methods)


class Input_window(QtWidgets.QWidget):
    def __init__(self, output_template=None):
        super(Input_window, self).__init__(parent=None)

        self.output_template = output_template
        self.setObjectName("Dialog")
        self.resize(500, 450)
        self.gridLayout = QtWidgets.QGridLayout(self)
        self.gridLayout.setObjectName("gridLayout")
        self.set_source = QtWidgets.QPushButton(self)
        self.set_source.setObjectName("set_source")
        self.gridLayout.addWidget(self.set_source, 0, 0, 1, 1)
        self.set_target = QtWidgets.QPushButton(self)
        self.set_target.setObjectName("set_target")
        self.gridLayout.addWidget(self.set_target, 0, 1, 1, 1)

        self.animation_copier = CopyAnimation()

        self.target_objects = []

        self.widget = QtWidgets.QWidget(self)
        self.widget.setObjectName("widget")
        self.gridLayout.addWidget(self.widget, 2, 0, 1, 2)

        self.nodegraph = NodeGraphWidget("main", parent=self, output_template=self.output_template)
        self.nodegraph.mousePressEvent = lambda event: cmds.select(clear=True)
        self.gridLayout.addWidget(self.nodegraph, 2, 0, 1, 2)

        self.source = self.nodegraph.graph_scene.create_node(
            "Source",
            inputs=[],
            outputs=[
                "All",
                "Translate X",
                "Translate Y",
                "Translate Z",
                "Rotate X",
                "Rotate Y",
                "Rotate Z",
                "Scale X",
                "Scale Y",
                "Scale Z",
                "csV"
            ],
            width=180,
            height=360,
            selectable=False,
            movable=False,
        )
        self.source.setPos(-200, 0)
        self.target = self.nodegraph.graph_scene.create_node(
            "Target",
            inputs=[
                "All",
                "Translate X",
                "Translate Y",
                "Translate Z",
                "Rotate X",
                "Rotate Y",
                "Rotate Z",
                "Scale X",
                "Scale Y",
                "Scale Z",
                "Visibility"
            ],
            outputs=[],
            width=180,
            height=360,
            selectable=False,
            movable=False,
        )
        self.target.setPos(150, 0)
        # edge = self.nodegraph.graph_scene.create_edge(
        # cam._outputs[0],
        # model._inputs[0])
        print(type(self.target))
        # self.target._update_title("Ryan")
        # object_methods = [method_name for method_name in dir(target)
        #                   if callable(getattr(target, method_name))]
        # print(object_methods)

        self.nodegraph.graph_scene.add_exclusive_connection("All", "All")



        self.go_button = QtWidgets.QPushButton(self)
        self.go_button.setObjectName("go_button")
        self.gridLayout.addWidget(self.go_button, 3, 0, 1, 2)
        self.invert_checkbox = QtWidgets.QCheckBox(self)
        self.invert_checkbox.setObjectName("invert_checkbox")
        self.gridLayout.addWidget(self.invert_checkbox, 1, 0, 1, 1, QtCore.Qt.AlignRight)

        self.set_source.clicked.connect(self.set_source_object)
        self.go_button.clicked.connect(self.execute)
        self.set_target.clicked.connect(self.set_target_objects)

        self.setWindowTitle("Dialog")
        self.set_source.setText("Set Source")
        self.set_target.setText("Set Target")
        self.go_button.setText("Zhu Li! Do the thing!")
        self.invert_checkbox.setText("Invert All")

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
        self.clear_button.clicked.connect(self.delete_all_lines)
        self.gridLayout.addWidget(self.clear_button, 1, 1, 1, 1)

        QtCore.QMetaObject.connectSlotsByName(self)

    def delete_all_lines(self):
        self.nodegraph.graph_scene.delete_all_edges(self.target._inputs[0])

    def toggle_invert_all(self):
        invert_or_deinvert =  self.invert_checkbox.isChecked()
        self.nodegraph.graph_scene.toggle_invert_all_edges(self.target._inputs[0], invert_or_deinvert)

    def execute(self):
        invert = self.invert_checkbox.isChecked()
        print(invert)
        # self.animation_copier.clear_target_channels()
        # try:
        print(type(self.target))
        channel_dict = self.nodegraph.graph_scene.connections_dict
        print(self.nodegraph.graph_scene.connections_dict)
        res = ""
        for key, val in self.nodegraph.graph_scene.connections_dict.items():
            res += f"|{key}|"
            for v in val:
                res += f"[{v}]"
            res += ", "
        print(res)
        #self.animation_copier.store_target(target_objects)
        for obj in self.target_objects:
            self.animation_copier.store_target(obj)

            for src, targets in channel_dict.items():
                self.animation_copier.clear_target_channels()
                self.animation_copier.set_source_channel(src)
                for trgt in targets:
                    print(src, trgt)
                    self.animation_copier.set_target_channel(trgt)
                    print(self.animation_copier.source, self.animation_copier.target, self.animation_copier.selectedTargets, self.animation_copier.sourceChannel)

                    self.animation_copier.copyAnimation()
        #
        # except UnboundLocalError as e:
        #     pass

    def set_source_object(self):
        sel = cmds.ls(sl=True)
        target_item = sel[0]
        self.animation_copier.clear_source()
        self.animation_copier.store_source(target_item)
        self.source._update_title(target_item)

    def set_target_objects(self):
        self.animation_copier.clear_target()
        print("hi")
        sel = cmds.ls(sl=True)
        self.target_objects = sel

        self.target._update_title(f"{len(self.target_objects)} Objects")






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

    def __init__(self, name, parent=None, output_template=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.name = name
        self.parent = parent
        
        convert_func = lambda name:name.lower()[0] + name.lower()[-1]
        self.graph_scene = Scene(parent=self.parent,
                                 nodegraph_widget=self,
                                 multiple_input_allowed=False,
                                 convert = convert_func,
                                 output_template = output_template)
        self.graph_view = View(self.graph_scene, parent=self.parent, is_zoom=False, scale=0.85)
        self.graph_view.mousePressedEvent = lambda event: cmds.select(clear=True)
        # find out why it's not scaling!!!!
        self.horizontal_layout = QtWidgets.QHBoxLayout(self)
        self.horizontal_layout.addWidget(self.graph_view)

        self.setMouseTracking(True)

    def mousePressEvent(self, event):
        cmds.select(clear=True)


if __name__ == "__main__":
    # dialog = NodeGraphDialog()
    # dialog.show()
    box = Input_window(output_template=ConnectionCollection())
    box.show()

# add break node shortcut