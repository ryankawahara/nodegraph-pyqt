#!/usr/bin/env python

# import os
import sys

# import networkx
from Qt import QtWidgets

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
        cam = self.nodegraph.graph_scene.create_node("Source", inputs=[], outputs=["Translate X", "Translate Y", "Translate Z"], width=200, height=260)
        cam.setPos(-200, 0)
        model = self.nodegraph.graph_scene.create_node(
            "Target",
            inputs=["Translate X", "Translate Y", "Translate Z", "Rotate X", "Rotate Y"],
            outputs=[],
            width = 200,
            height = 260)
        model.setPos(150, 0)
        # edge = self.nodegraph.graph_scene.create_edge(
           # cam._outputs[0],
           # model._inputs[0])



class NodeGraphWidget(QtWidgets.QWidget):

    """
    Handles node graph view
    """

    def __init__(self, name, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.name = name
        self.parent = parent

        self.graph_scene = Scene(parent=self.parent,
                                 nodegraph_widget=self)
        self.graph_view = View(self.graph_scene, parent=self.parent)
        self.horizontal_layout = QtWidgets.QHBoxLayout(self)
        self.horizontal_layout.addWidget(self.graph_view)


if __name__ == "__main__":
    dialog = NodeGraphDialog()
    dialog.show()

