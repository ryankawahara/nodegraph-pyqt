#!/usr/bin/env python

from unload_packages import *
unload_packages(silent=False, packages=["nodegraph"])

# import os
import sys

# import networkx
from Qt import QtWidgets, QtGui

from nodegraph.scene import Scene
from nodegraph.view import View


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
        print(type(target))
        # target._update_title("Ryan")
        # object_methods = [method_name for method_name in dir(target)
        #                   if callable(getattr(target, method_name))]
        # print(object_methods)


class Input_window(QtWidgets.QWidget):
    def __init__(self):
        super(Input_window, self).__init__(parent=None)
        self.setObjectName("Dialog")
        self.resize(500, 450)
        self.gridLayout = QtWidgets.QGridLayout(self)
        self.gridLayout.setObjectName("gridLayout")
        self.pushButton = QtWidgets.QPushButton(self)
        self.pushButton.setObjectName("pushButton")
        self.gridLayout.addWidget(self.pushButton, 0, 0, 1, 1)
        self.pushButton_2 = QtWidgets.QPushButton(self)
        self.pushButton_2.setObjectName("pushButton_2")
        self.gridLayout.addWidget(self.pushButton_2, 0, 1, 1, 1)


        self.widget = QtWidgets.QWidget(self)
        self.widget.setObjectName("widget")
        self.gridLayout.addWidget(self.widget, 2, 0, 1, 2)

        self.nodegraph = NodeGraphWidget("main", parent=self)
        self.gridLayout.addWidget(self.nodegraph, 2, 0, 1, 2)

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
            selectable=False,
            movable=False,
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
            width=180,
            height=360,
            selectable=False,
            movable=False,
        )
        target.setPos(150, 0)
        # edge = self.nodegraph.graph_scene.create_edge(
        # cam._outputs[0],
        # model._inputs[0])
        print(type(target))
        # target._update_title("Ryan")
        # object_methods = [method_name for method_name in dir(target)
        #                   if callable(getattr(target, method_name))]
        # print(object_methods)



        self.pushButton_3 = QtWidgets.QPushButton(self)
        self.pushButton_3.setObjectName("pushButton_3")
        self.gridLayout.addWidget(self.pushButton_3, 3, 0, 1, 2)
        self.checkBox = QtWidgets.QCheckBox(self)
        self.checkBox.setObjectName("checkBox")
        self.gridLayout.addWidget(self.checkBox, 1, 0, 1, 1, QtCore.Qt.AlignRight)

        self.setWindowTitle("Dialog")
        self.pushButton.setText("Set Source")
        self.pushButton_2.setText("Set Target")
        self.pushButton_3.setText("Zhu Li! Do the thing!")
        self.checkBox.setText("Invert")

        self.pushButton_4 = QtWidgets.QPushButton(self)
        font = QtGui.QFont()
        font.setBold(False)
        font.setItalic(False)
        font.setWeight(50)
        self.pushButton_4.setFont(font)
        self.pushButton_4.setStyleSheet("background-color: rgb(255, 0, 127)")
        self.pushButton_4.setCheckable(False)
        self.pushButton_4.setObjectName("pushButton_4")
        self.pushButton_4.setText("Clear")
        self.gridLayout.addWidget(self.pushButton_4, 1, 1, 1, 1)

        QtCore.QMetaObject.connectSlotsByName(self)



class NodeGraphWidget(QtWidgets.QWidget):

    """
    Handles node graph view
    """

    def __init__(self, name, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.name = name
        self.parent = parent
        
        convert_func = lambda name:name.lower()[0] + name.lower()[-1]
        self.graph_scene = Scene(parent=self.parent,
                                 nodegraph_widget=self,
                                 multiple_input_allowed=False,
                                 convert = convert_func)
        self.graph_view = View(self.graph_scene, parent=self.parent, is_zoom=True)
        # find out why it's not scaling!!!!
        self.graph_view.scale_view(0.85)
        self.horizontal_layout = QtWidgets.QHBoxLayout(self)
        self.horizontal_layout.addWidget(self.graph_view)


if __name__ == "__main__":
    # dialog = NodeGraphDialog()
    # dialog.show()
    box = Input_window()
    box.show()
