# =============================================================================
# Nodegraph-pyqt
#
# Everyone is permitted to copy and distribute verbatim copies of this
# document, but changing it is not allowed without permissions.
#
# For any questions, please contact: dsideb@gmail.com
#
# GNU LESSER GENERAL PUBLIC LICENSE (Version 3, 29 June 2007)
# =============================================================================

"""Node graph scene manager based on QGraphicsScene

"""
from Qt import QtCore, QtGui, QtWidgets
import PySide2
from .node import Node, NodeSlot
from .edge import Edge, InteractiveEdge
from .rubberband import RubberBand

from .constant import SCENE_WIDTH, SCENE_HEIGHT


class Scene(QtWidgets.QGraphicsScene):

    """
    Provides custom implementation of QGraphicsScene

    """

    def __init__(self, parent=None, nodegraph_widget=None, multiple_input_allowed=False, convert=None, output_template=None, attributes=None):
        """Create an instance of this class

        """
        QtWidgets.QGraphicsScene.__init__(self, parent)
        self.parent = parent
        self.convert = convert
        self.output_template = output_template
        self.attributes = attributes

        self.invert_new_edges = False

        # if a class is passed in, initialize an instance
        # if self.output_template:
        #     self.output_template = self.output_template()

        self._nodegraph_widget = nodegraph_widget
        self._nodes = []
        self._edges_by_hash = {}
        self._is_interactive_edge = False
        self._is_refresh_edges = False
        self._interactive_edge = None
        self._refresh_edges = {"move": [], "refresh": []}
        self._rubber_band = None
        self.multiple_input_allowed = multiple_input_allowed

        self.connections_dict = {}

        self.source_node = None
        self.target_node = None

        # Registars
        self._is_rubber_band = False
        self._is_shift_key = False
        self._is_ctrl_key = False
        self._is_alt_key = False
        self._is_left_mouse = False
        self._is_mid_mouse = False
        self._is_right_mouse = False

        # Redefine palette
        self.setBackgroundBrush(QtGui.QColor(60, 60, 60))
        palette = self.palette()
        palette.setColor(QtGui.QPalette.Text, QtGui.QColor(210, 210, 210))
        palette.setColor(QtGui.QPalette.HighlightedText,
                         QtGui.QColor(255, 255, 255))
        palette.setColor(QtGui.QPalette.BrightText,
                         QtGui.QColor(80, 180, 255))
        palette.setColor(QtGui.QPalette.Button, QtGui.QColor(5, 5, 5))
        palette.setColor(QtGui.QPalette.ButtonText, QtGui.QColor(20, 20, 20))
        self.setPalette(palette)

        self.selectionChanged.connect(self._onSelectionChanged)

        self.only_allowed_connections = []

    @property
    def nodes(self):
        """Return all nodes

        """
        return self._nodes

    @property
    def is_interactive_edge(self):
        """Return status of interactive edge mode

        """
        return self._is_interactive_edge

    @property
    def edges_by_hash(self):
        """Return a list of edges as hash

        """
        return self._edges_by_hash

    def create_node(self, name, inputs=["in"], outputs=["out"], parent=None, width=160, height=130, selectable=True, movable=True):
        """Create a new node

        """
        node = Node(name, self, inputs=inputs, outputs=outputs, parent=parent, width=width, height=height, selectable=selectable, movable=movable)
        self._nodes.append(node)
        return node

    def update_node_name(self, node, name):
        node.update_name(name)

    def store_target_node(self, node):
        self.target_node = node

    def store_source_node(self, node):
        self.source_node = node


    def create_edge(self, source, target):
        """Create a new edge

        """
        edge = Edge(source, target, self, arrow=Edge.ARROW_STANDARD)
        if self.invert_new_edges:
            edge.double_click = True
        self._edges_by_hash[edge.hash] = edge
        self.connections_dict = self.get_connections(target)
        return edge

    def remove_edge(self, edge):
        del self._edges_by_hash[edge.hash]

    def add_exclusive_connection(self, source, target):
        self.only_allowed_connections.append((source,target))

    def start_interactive_edge(self, source_slot, mouse_pos):
        """Create an edge between source slot and mouse position

        """
        self._is_interactive_edge = True

        if not self._interactive_edge:
            # Create interactive edge
            self._interactive_edge = InteractiveEdge(
                source_slot,
                mouse_pos,
                scene=self,
                arrow=Edge.ARROW_STANDARD)

            # INVERT HERE
            if self.invert_new_edges:
                self._interactive_edge.double_click = True
        else:
            # Re-use existing interactive edge
            self._interactive_edge.refresh(mouse_pos, source_slot)

    def stop_interactive_edge(self, connect_to=None):
        """Hide the interactive and create an edge between the source slot
        and the slot given by connect_to

        """

        self._is_interactive_edge = False
        if connect_to:
            eh = self._edges_by_hash  # shortcut
            source = self._interactive_edge._source_slot

            found = True
            if isinstance(connect_to, Node):
                found = False
                # Try to find most likely slot
                if source.family == NodeSlot.OUTPUT:
                    for slot in connect_to._inputs:
                        li = [h for h in eh if eh[h]._source_slot == slot or
                              eh[h]._target_slot == slot]
                        if not li:
                            connect_to = slot
                            found = True
                            break
                        for h in eh:
                            if eh[h]._source_slot == slot:
                                connect_to = eh[h]
                else:
                    connect_to = connect_to._outputs[0]
                    found = True

            # Resolve direction
            target = connect_to

            if source.family == NodeSlot.OUTPUT:
                source = connect_to
                target = self._interactive_edge._source_slot

            # Validate the connection

            if (found and
                    source.family != target.family and
                    source.parent != target.parent and
                    not [h for h in eh if eh[h]._target_slot == source]):

                if source.family == NodeSlot.OUTPUT:
                    for aninput in source.parent._inputs:
                        pass
                else:
                    for anoutput in source.parent._outputs:
                        pass

                escape = False

                for slot in self.only_allowed_connections:
                    if (source._name, target._name) == slot:
                        escape = False
                        self.delete_all_edges(source)
                    elif slot[0] == source._name or slot[1] == target._name:
                        escape = True

                # allows multiple output nodes to connect to an input node
                if not escape:
                    active_edge_connections = []
                    edge = self.create_edge(target, source)
                    # if self.invert_new_edges:
                    #     edge.double_click = True
                    active_slots = source.parent.active_inputs

                    for slots in active_slots:
                        for edge in slots.edge:
                            edge_obj = self.get_edge_by_hash(edge)
                            if edge_obj:

                                # if self.invert_new_edges:
                                #     edge_obj.double_click = True


                                edge_nodes = edge_obj.slots
                                edge_node_names = (edge_nodes[0].name, edge_nodes[1].name)
                                active_edge_connections.append(edge_nodes)

                    for connection in active_edge_connections:
                        for pair in self.only_allowed_connections:
                            if connection[0].name in pair or connection[1].name in pair:
                                if len(active_edge_connections) > 1: # IF IT IS THE ONLY CONNECTION, LEAVE IT BE. OTHERWISE DELETE!
                                    edge_to_delete = self.get_edge_by_hash(connection[1].edge[0])
                                    res = edge_to_delete.slots
                                    self.delete_edges([edge_to_delete])

            else:
                source_hashes = list(source._edge)
                if self.multiple_input_allowed:
                    edge = self.create_edge(target, source)
                    if self.invert_new_edges:
                        edge.double_click = True

            # Delete item (to be sure it's not taken into account by any function
        # including but not limited to fitInView)


            # why is this not working?????
            # print("run 2")
            self.connections_dict = self.get_connections(target)

        self.removeItem(self._interactive_edge)
        self._interactive_edge = None

    def get_all_edges(self, target_node):
        hash_list = [hash for hash in target_node.parent.edges if hash in self._edges_by_hash]
        edge_list = []
        for node_hash in hash_list:
            edge_list.append(self._edges_by_hash[node_hash])
        return edge_list

    def delete_all_edges(self, target_node):
        to_delete = self.get_all_edges(target_node)
        self.delete_edges(to_delete)

    def get_edge_by_hash(self, hash):
        try:
            res = self._edges_by_hash[hash]
        except KeyError:
            res = None

        return res

    def toggle_invert_all_edges(self, target_node, toggle):

        to_invert = self.get_all_edges(target_node)
        for edge in to_invert:
            edge.double_click = toggle
            if self.output_template:
                source_name = edge._source_slot._name
                target_name = edge._target_slot._name

                # check if type of input is dict or list

                if self.attributes:
                    source = self.attributes[source_name]
                    target = self.attributes[target_name]
                elif self.convert:
                    # converts Translate X to tx
                    source = self.convert(source_name)
                    target = self.convert(target_name)

                self.output_template.set_invert(source, target, toggle)

            edge.refresh()


    def invert_single_edge(self, edge, toggle):
        if self.output_template:
            source_name = edge._source_slot._name
            target_name = edge._target_slot._name

            if self.attributes:
                source = self.attributes[source_name]
                target = self.attributes[target_name]
            elif self.convert:
                # converts Translate X to tx
                source = self.convert(source_name)
                target = self.convert(target_name)

            self.output_template.set_invert(source, target, toggle)

        edge.refresh()


    def connect_all_slots(self, source_node, target_node, create):
        if create:
            if len(source_node.outputs) == len(target_node.inputs):
                for ind in range(0,len(source_node.outputs)):
                    if source_node.outputs[ind]._name != "":
                        self.create_edge(source_node.outputs[ind], target_node.inputs[ind])
            else:
                ind = 0
                while ind < len(source_node.outputs)-1:
                    if source_node.outputs[ind]._name != "":
                        self.create_edge(source_node.outputs[ind], target_node.inputs[ind])
                    ind +=1
        else:
            self.delete_all_edges(target_node.inputs[0])

        self.connections_dict = self.get_connections(target_node.inputs[0])



    def get_connections(self, target_node):
        connection_dict = {}
        hash_list = [hash for hash in target_node.parent.edges if hash in self._edges_by_hash]
        if self.output_template is None:
            for node_hash in hash_list:

                source_name = self._edges_by_hash[node_hash]._source_slot._name
                target_name = self._edges_by_hash[node_hash]._target_slot._name

                if self.attributes:
                    source = self.attributes[source_name]
                    target = self.attributes[target_name]
                elif self.convert:
                    # converts Translate X to tx
                    source = self.convert(source_name)
                    target = self.convert(target_name)

                else:
                    source = source_name
                    target = target_name

                if source in connection_dict:
                    if target not in connection_dict[source]:
                        connection_dict[source].append(target)

                else:
                    connection_dict[source] = [target]

        else:
            for node_hash in hash_list:

                source_name = self._edges_by_hash[node_hash]._source_slot._name

                invert_source = self._edges_by_hash[node_hash].double_click

                target_name = self._edges_by_hash[node_hash]._target_slot._name


                if self.attributes:
                    source = self.attributes[source_name]
                    target = self.attributes[target_name]
                elif self.convert:
                    # converts Translate X to tx
                    source = self.convert(source_name)
                    target = self.convert(target_name)

                else:
                    source = source_name
                    target = target_name

                newObj = self.output_template.add(source, target, invert_source)
                # print("INVERT", newObj.invert)
                #
                # print(self.output_template.connection_dict)
                # for key, item in self.output_template.connection_dict.items():
                #     print(key, item[0].invert)


            connection_dict = self.output_template.connection_dict


        return connection_dict



    def start_rubber_band(self, init_pos, col=None):
        """Create/Enable custom rubber band

        :param init_pos: Top left corner of the custom rubber band
        :type init_pos: :class:`QtCore.QPosF`

        """
        self._is_rubber_band = True
        if not self._rubber_band:
            # Create custom rubber band
            self._rubber_band = RubberBand(init_pos, scene=self, color=col)
        else:
            # Re-use existing rubber band
            self._rubber_band.refresh(mouse_pos=init_pos, init_pos=init_pos)

    def stop_rubber_band(self, intersect=None):
        """Hide the custom rubber band and if it contains node/edges select
        them

        """
        self._is_rubber_band = False

        # Select nodes and edges inside the rubber band
        if self._is_shift_key and self._is_ctrl_key:
            self._rubber_band.update_scene_selection(
                self._rubber_band.TOGGLE_SELECTION)
        elif self._is_shift_key:
            self._rubber_band.update_scene_selection(
                self._rubber_band.ADD_SELECTION)
        elif self._is_ctrl_key:
            self._rubber_band.update_scene_selection(
                self._rubber_band.MINUS_SELECTION)
        else:
            self._rubber_band.update_scene_selection(intersect)

        self.removeItem(self._rubber_band)
        self._rubber_band = None


    def delete_edges(self, edges_to_delete):
        for edge in edges_to_delete:
            self.removeItem(edge)
            self.remove_edge(edge)
            if self.attributes:
                remove_source_name = self.attributes[edge._source_slot._name]
                remove_target_name = self.attributes[edge._target_slot._name]
            elif self.convert:
                remove_source_name = self.convert(edge._source_slot._name)
                remove_target_name = self.convert(edge._target_slot._name)

            if self.output_template is None:
                if remove_source_name in self.connections_dict:
                    output_list = self.connections_dict[remove_source_name]
                    if len(output_list) < 2:
                        self.connections_dict.pop(remove_source_name)
                    else:
                        output_list.remove(remove_target_name)
                else:
                    continue
            else:
                self.output_template.remove(remove_source_name, remove_target_name)


    def delete_node(self, node):
        self.removeItem(node)
        index = self._nodes.index(node)
        self._nodes.pop(index)

        self.redraw_scene()

    def redraw_scene(self):
        self.invalidate()

    def delete_selected(self):
        """Delete selected nodes and edges

        """
        nodes = []
        edges = []
        for i in self.selectedItems():
            if isinstance(i, Node):
                nodes.append(i)
            if isinstance(i, Edge):
                edges.append(i)

        for node in nodes:
            # TODO: Collect all edges for deletion or reconnection

            # Delete node(s)
            self.removeItem(node)
            index = self._nodes.index(node)
            self._nodes.pop(index)

        for edge in edges:
            self.removeItem(edge)
            self.remove_edge(edge)
            if self.attributes:
                remove_source_name = self.attributes[edge._source_slot._name]
                remove_target_name = self.attributes[edge._target_slot._name]
            elif self.convert:
                remove_source_name = self.convert(edge._source_slot._name)
                remove_target_name = self.convert(edge._target_slot._name)
            output_list = self.connections_dict[remove_source_name]

            if self.output_template is None:
                if len(output_list) < 2:
                    self.connections_dict.pop(remove_source_name)
                else:
                    output_list.remove(remove_target_name)

            else:
                self.output_template.remove(remove_source_name, remove_target_name)


            # if self.connections_dict[self.convert(edge._source_slot)._name]
            # self.connections_dict.pop(self.convert(edge._source_slot._name))
            # print(edge._source_slot._name, edge._target_slot._name)

    def mousePressEvent(self, event):
        """Re-implements mouse press event

        :param event: Mouse event
        :type event: :class:`QtWidgets.QMouseEvent`

        """
        if not self._is_interactive_edge:

            if not self.items(event.scenePos()):
                buttons = event.buttons()

                if buttons == QtCore.Qt.LeftButton:
                    self.start_rubber_band(event.scenePos())
                else:
                    self.start_rubber_band(event.scenePos(), QtGui.QColor(255,0,0))

                if self._is_shift_key or self._is_ctrl_key:
                    event.accept()
                return
            else:
                if self._is_shift_key or self._is_ctrl_key:
                    # Mouse is above scene items and single click with modfiers
                    event.accept()

                    if self._is_shift_key and self._is_ctrl_key:
                        for item in self.items(event.scenePos()):
                            item.setSelected(not item.isSelected())
                    elif self._is_shift_key:
                        for item in self.items(event.scenePos()):
                            item.setSelected(True)
                    elif self._is_ctrl_key:
                        for item in self.items(event.scenePos()):
                            item.setSelected(False)

                    return
        else:
            # Items under mouse during edge creation, We may have to start an
            # interactive edge
            pass

        QtWidgets.QGraphicsScene.mousePressEvent(self, event)

    def mouseMoveEvent(self, event):
        """Re-implements mouse move event

        :param event: Mouse event
        :type event: :class:`QtWidgets.QMouseEvent`

        """
        buttons = event.buttons()


        # THIS SECTION IS FOR CLICK AND CLICK.
        # if self.source_node:
        #     # print(self.source_node._name)
        #     QtWidgets.QGraphicsScene.mouseMoveEvent(self, event)
        #     sceneMouse = event.scenePos() + QtCore.QPointF(-150, 0)
        #
        #     if self._is_interactive_edge:
        #         self._interactive_edge.refresh(event.scenePos())
        # el
        if buttons == QtCore.Qt.LeftButton:
            # for item in self.items(event.scenePos()):
            #     print(item._name, type(item))

            QtWidgets.QGraphicsScene.mouseMoveEvent(self, event)
            sceneMouse = event.scenePos() + QtCore.QPointF(-150, 0)
            # print("Scene MOUSE", sceneMouse)
            node = None
            # Edge creation mode?
            if self._is_interactive_edge:
                # node = None
                slot = None

                for item in self.items(event.scenePos()):
                    if isinstance(item, Node):
                        node = item
                        slot = node._hover_slot
                        # print(node, slot)
                        break

                if node:
                    left_margin = PySide2.QtCore.QMarginsF((node.label_rect_size[0]*1.7) , 0, 0, 0)

                    right_margin = PySide2.QtCore.QMarginsF(0, 0, node.label_rect_size[0] / 2, 0)

                    his = [i for i in node._inputs if (i._rect + right_margin).contains(sceneMouse)]
                    hos = [i for i in node._outputs if (i._rect + left_margin).contains(event.scenePos())]

                    if hos:
                        node._update_hover_slot(hos[0])
                    elif his:
                        node._update_hover_slot(his[0])
                    else:
                        node._update_hover_slot(False)


                else:
                    for node in self._nodes:
                        node._update_hover_slot(False)


                self._interactive_edge.refresh(event.scenePos())

            # Selection mode?
            elif self._is_rubber_band:
                self._rubber_band.refresh(event.scenePos())
            elif self.selectedItems():
                if not self._is_refresh_edges:
                    self._is_refresh_edges = True
                    self._refresh_edges = self._get_refresh_edges()
                for ahash in self._refresh_edges["move"]:
                    if ahash in self._edges_by_hash:
                        self._edges_by_hash[ahash].refresh_position()
                for ahash in self._refresh_edges["refresh"]:
                    if ahash in self._edges_by_hash:
                        self._edges_by_hash[ahash].refresh()
        elif buttons == QtCore.Qt.RightButton:
            QtWidgets.QGraphicsScene.mouseMoveEvent(self, event)
            sceneMouse = event.scenePos() + QtCore.QPointF(-150, 0)
            # print("Scene MOUSE", sceneMouse)

            # Edge creation mode?
            if self._is_interactive_edge:
                self._interactive_edge.refresh(event.scenePos())
            # Selection mode?
            elif self._is_rubber_band:
                self._rubber_band.refresh(event.scenePos())
        else:
            return QtWidgets.QGraphicsScene.mouseMoveEvent(self, event)

    def mouseReleaseEvent(self, event):
        """Re-implements mouse release event

        :param event: Mouse event
        :type event: :class:`QtWidgets.QMouseEvent`

        """
        # if self.target_node:
        #     print("hello there")
        #     return
        # buttons = event.buttons()

        connect_to = None

        # Edge creation mode?
        if self._is_interactive_edge:

            slot = None
            node = None
            for item in self.items(event.scenePos()):
                if isinstance(item, Node):
                    node = item
                    slot = node._hover_slot
                    break
            connect_to = node
            if not connect_to:
                for node in self._nodes:
                    node._update_hover_slot(False)
                self.stop_interactive_edge()
                return

            target_node = None
            if hasattr(connect_to,'_inputs'):
                for input in connect_to._inputs:
                    sceneMouse = event.scenePos() - connect_to.mapToScene(event.pos())
                    label_size = connect_to.label_rect_size[0]
                    right_margin = PySide2.QtCore.QMarginsF(0, 0, label_size, 0)
                    end_zone = input._rect + right_margin
                    if end_zone.contains(sceneMouse):
                        target_node = input
            if hasattr(connect_to,'_outputs'):
                left_margin = PySide2.QtCore.QMarginsF(connect_to.label_rect_size[0] / 2, 0, 0, 0)
                for output in connect_to._outputs:
                    sceneMouse = event.scenePos() - connect_to.mapToScene(event.pos())
                    label_size = connect_to.label_rect_size[0]
                    end_zone = output._rect + left_margin
                    if end_zone.contains(sceneMouse):
                        target_node = output
            else:
                pass
                # for node in self._nodes:
                #     node._update_hover_slot(False)
                # else:
                #     print("NO")
            #     print(input.name, input._rect)
            #     print(input.name, input._rect.contains(sceneMouse))
            # print("location", event.pos())
            # print("mouse", connect_to.mapToScene(event.pos()))
            # selected = [i for i in connect_to._inputs if i._rect.contains(connect_to.mapToScene(event.scenePos()))]
            # print(selected)

            # LEAVE OFF HERE!!!!! THIS IS KEY RIGHT HERE. If it clicks and source is set then it should STOP
            # if self.target_node is not None:
            self.stop_interactive_edge(connect_to=target_node)

        # Edge refresh mode?
        if self._is_refresh_edges:
            self._is_refresh_edges = False
            self._refresh_edges = {"move": [], "refresh": []}

        # Rubber band mode?
        if self._is_rubber_band:
            self.stop_rubber_band()

        QtWidgets.QGraphicsScene.mouseReleaseEvent(self, event)

    def mouseDoubleClickEvent(self, event):
        """Re-implements doube click event

        :param event: Mouse event
        :type event: :class:`QtWidgets.QMouseEvent`

        """
        selected = self.items(event.scenePos())

        if len(selected) == 1:
            selected[0].set_double_click(not selected[0].double_click)
            if self.output_template:
                source_name = selected[0]._source_slot._name
                target_name = selected[0]._target_slot._name

                if self.attributes:
                    source = self.attributes[source_name]
                    target = self.attributes[target_name]
                elif self.convert:
                    # converts Translate X to tx
                    source = self.convert(source_name)
                    target = self.convert(target_name)

                self.output_template.toggle_invert(source, target)


            # print(self.get_connections(selected[0]._target_slot))
            # print("Edit Node %s" % selected[0]._name)

    def _onSelectionChanged(self):
        """Re-inplements selection changed event

        """
        if self._is_refresh_edges:
            self._refresh_edges = self._get_refresh_edges()

    def _get_refresh_edges(self):
        """Return all edges of selected items

        """
        edges = set()
        nodes = set()
        edges_to_move = []
        edges_to_refresh = []

        for item in self.selectedItems():
            if isinstance(item, Node):
                edges |= item.edges
                nodes.add(item.name)

        # Distinghish edges where both ends are selected from the rest
        for edge in edges:
            # check if edge is in edges by hash. If it's not do not proceed!
            if edge in self._edges_by_hash and self._edges_by_hash[edge].is_connected_to(nodes):
                edges_to_move.append(edge)
            else:
                edges_to_refresh.append(edge)

        r = {"move": edges_to_move, "refresh": edges_to_refresh}
        # print("move: %r\nrefresh: %r" % (edges_to_move, edges_to_refresh))
        return r

    def get_nodes_bbox(self, visible_only=True):
        """Return bounding box of all nodes in scene

        ..todo :
            This function could be refactored

        :param visible_only: If true, only evaluate visible NodeSlot
        :type visible_only: bool

        :returns: A bounding rectangle
        :rtype: :class:`QtCore.QrectF`

        """
        if not self._nodes:
            return QtCore.QRectF()

        min_x = SCENE_WIDTH / 2
        min_y = SCENE_HEIGHT / 2
        max_x = - min_x
        max_y = - min_y
        min_x_node = None
        min_y_node = None
        max_x_node = None
        max_y_node = None

        for node in self._nodes:
            if visible_only and not node.isVisible():
                continue

            if node.x() < min_x:
                min_x = node.x()
                min_x_node = node
            if node.y() < min_y:
                min_y = node.y()
                min_y_node = node
            if node.x() > max_x:
                max_x = node.x()
                max_x_node = node
            if node.y() > max_y:
                max_y = node.y()
                max_y_node = node

        top_left = QtCore.QPointF(
            min_x + min_x_node.boundingRect().topLeft().x(),
            min_y + min_y_node.boundingRect().topLeft().y())
        bottom_right = QtCore.QPointF(
            max_x + max_x_node.boundingRect().bottomRight().x(),
            max_y + max_y_node.boundingRect().bottomRight().y())
        return QtCore.QRectF(top_left, bottom_right)
