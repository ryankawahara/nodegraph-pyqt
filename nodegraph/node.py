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

"""
Base node definition including:

    * Node
    * NodeSlot

"""
# import sha
from Qt import QtCore, QtGui, QtWidgets

# from constant import DEBUG


class Node(QtWidgets.QGraphicsItem):

    """
    Base class for node graphic item

    As much as possible, everything is drawn in the node paint function for
    performance reasons

    """

    def __init__(self, name, scene, inputs=["in"], outputs=["out"], parent=None, width=160, height=130, selectable=True, movable=True):
        """Create an instance of this class

        """
        QtWidgets.QGraphicsItem.__init__(self, parent=parent)
        scene.addItem(self)
        self._name = name
        self._width = width
        self._height = height
        self._outline = 6
        self._slot_radius = 10
        self._label_height = 34
        self._bbox = None  # cache container
        self._round_slot = None
        self._rect_slot = None
        self._hover_slot = False
        self.update_title = None

        if selectable:
            self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable)

        if movable:
            self.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable)
        # self.setFlags(QtWidgets.QGraphicsItem.ItemIsMovable |
        #               QtWidgets.QGraphicsItem.ItemIsSelectable)

        self.setAcceptHoverEvents(False)

        # Build output slot
        self._outputs = []
        for slot_name in outputs:
            anoutput =  NodeSlot(slot_name, self, family=NodeSlot.OUTPUT)
            self._outputs.append(anoutput)

        # Build input slots
        self._inputs = []
        for slot_name in inputs:
            aninput = NodeSlot(slot_name, self)
            self._inputs.append(aninput)

        # Update internal containers
        self._update()

    @property
    def inputs(self):
        return self._inputs

    @property
    def outputs(self):
        return self._outputs

    @property
    def name(self):
        """Return the family of the slot

        """
        return self._name

    @property
    def active_inputs(self):
        return [inp for inp in self._inputs if inp.active == True]

    @property
    def active_inputs_by_name(self):
        return [inp.name for inp in self._inputs if inp.active == True]

    @property
    def edges(self):
        """Return all hashes of connected edges

        """
        # outputs = self._output.edge
        outputs = list(set([e for i in self._outputs for e in i.edge]))
        inputs = list(set([e for i in self._inputs for e in i.edge]))
        res = set(outputs+inputs)
        return res


    def _update(self):
        """Update slots internal properties

        """
        slot_height = self._slot_radius * 2 + self._outline
        base_y = self._height / 2 + self._label_height / 2 + self._outline / 2

        # Update base slot bounding box
        self._draw_slot = QtCore.QRectF(0,
                                        0,
                                        self._slot_radius * 2,
                                        self._slot_radius * 2)
        # Update output
        init_y = base_y - slot_height * len(self._outputs) / 2
        # self._output.rect = QtCore.QRectF(self._draw_slot).translated(
        #     self._width - self._slot_radius, init_y)
        print("out init y", init_y)

        for i, _input in enumerate(self._outputs):
            self._outputs[i].rect = QtCore.QRectF(self._draw_slot).translated(
                self._width - self._slot_radius, init_y + slot_height * i)

        # Update inputs
        init_y = base_y - slot_height * len(self._inputs) / 2
        print("in init y", init_y)
        for i, _input in enumerate(self._inputs):
            self._inputs[i].rect = QtCore.QRectF(self._draw_slot).translated(
                -self._slot_radius, init_y + slot_height * i)

        # Update bounding box
        self._bbox = QtCore.QRectF(
            -self._outline / 2 - self._slot_radius,
            -self._outline / 2,
            self._width + self._outline + self._slot_radius * 2,
            self._height + self._outline)

    def _update_hover_slot(self, slot):
        if slot == self._hover_slot:
            # No change
            return

        self._hover_slot = slot

        self.update()

    def _update_title(self, name):
        self.update_title = name
        self.refresh()

    def boundingRect(self):
        """Return a QRect that represents the bounding box of the node.
        Here that sould be the bounding box of the primary shape of the node.

        """
        return self._bbox

    def paint(self, painter, option, widget=None):
        """Re-implement paint method

        """
        lod = option.levelOfDetailFromTransform(painter.worldTransform())

        # Resolve fill, text and outlines brush
        fill_brush = self.scene().palette().button()
        text_brush = self.scene().palette().text()
        if option.state & QtWidgets.QStyle.State_Selected:
            fill_brush = self.scene().palette().highlight()
            text_brush = self.scene().palette().highlightedText()

        # Set brush and pen, then start drawing
        painter.setBrush(self.scene().palette().buttonText())
        painter.setPen(QtGui.QPen(fill_brush, self._outline))

        # Draw primary shape
        painter.drawRect(0, 0, self._width, self._height)

        # Draw label background
        # TODO: Color should be based on node type
        painter.setBrush(QtGui.QColor(90, 90, 140))
        painter.setPen(QtCore.Qt.NoPen)
        label_rect = QtCore.QRectF(self._outline / 2,
                                   self._outline / 2,
                                   self._width - self._outline,
                                   self._label_height - self._outline / 2)
        painter.drawRect(label_rect)

        # Draw text
        if lod >= 0.4:
            font = QtGui.QFont("Arial", 14)
            font.setStyleStrategy(QtGui.QFont.ForceOutline)
            painter.setFont(font)
            painter.setPen(QtGui.QPen(text_brush, 1))
            painter.scale(1, 1)
            if not self.update_title:
                painter.drawText(label_rect, QtCore.Qt.AlignCenter, self._name)
            else:
                painter.drawText(label_rect, QtCore.Qt.AlignCenter, self.update_title)


        # Draw slots
        if lod >= 0.15:
            # Should be driven by slot type
            hover_color = QtGui.QColor(90, 90, 140)
            hover_normal = self.scene().palette().text()
            self.setAcceptHoverEvents(True)
            painter.setBrush(hover_normal)
            painter.setPen(QtGui.QPen(fill_brush, self._outline))

            if lod >= 0.35:
                # Draw output (Ellipse)
                # if self._hover_slot == self._output:
                #     # Hover color should be driven by slot type
                #     painter.setBrush(hover_color)
                # painter.drawEllipse(self._output._rect)

                for anoutput in self._outputs:
                    if self._hover_slot == anoutput:
                        painter.setBrush(hover_color)
                    else:
                        painter.setBrush(hover_normal)
                    painter.drawEllipse(anoutput.rect)


                # Draw input (Ellipse)
                for aninput in self._inputs:
                    if self._hover_slot == aninput:
                        painter.setBrush(hover_color)
                    else:
                        painter.setBrush(hover_normal)
                    painter.drawEllipse(aninput.rect)
            else:
                # Draw output (Rectangle)
                # if self._hover_slot == self._output:
                #     painter.setBrush(hover_color)
                # painter.drawRect(self._output._rect)

                for anoutput in self._outputs:
                    if self._hover_slot == anoutput:
                        painter.setBrush(hover_color)
                    else:
                        painter.setBrush(hover_normal)
                    painter.drawRect(anoutput.rect)

                # Drae input (Rectangle)
                for aninput in self._inputs:
                    if self._hover_slot == aninput:
                        painter.setBrush(hover_color)
                    else:
                        painter.setBrush(hover_normal)
                    painter.drawRect(aninput.rect)
        else:
            self.setAcceptHoverEvents(False)

        # Draw slot labels
        if lod >= 0.5:
            font = QtGui.QFont("Arial", 11)
            font.setStyleStrategy(QtGui.QFont.ForceOutline)
            painter.setFont(font)
            painter.setPen(QtGui.QPen(self.scene().palette().text(), 1))

            width = self._width / 2 - self._slot_radius - self._outline
            height = self._slot_radius * 2

            # Output
            alignment = QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight
            # rect = QtCore.QRectF(self._width / 2,
            #                      self._output._rect.top(),
            #                      width,
            #                      height)
            # painter.drawText(rect, alignment, "out")
            # painter.setBrush(QtCore.Qt.NoBrush)
            # painter.drawRect(rect)

            for anoutput in self._outputs:
                rect = QtCore.QRectF(self._width / 2 + self._outline,
                                     anoutput._rect.top(),
                                     width,
                                     height)
                painter.drawText(rect, alignment, anoutput.name)

            # Input
            alignment = QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft
            for aninput in self._inputs:
                rect = QtCore.QRectF(self._slot_radius + self._outline,
                                     aninput._rect.top(),
                                     width,
                                     height)
                painter.drawText(rect, alignment, aninput.name)
                # painter.setBrush(QtCore.Qt.NoBrush)
                # painter.drawRect(rect)

        # # Draw debug
        # if DEBUG:
        #     painter.setBrush(QtGui.QBrush())
        #     painter.setPen(QtGui.QColor(255, 0, 0))
        #     painter.drawRect(self.boundingRect())

        return

    def hoverMoveEvent(self, event):
        """Re-implement Mouse hover move event

        :param event: Hover move event
        :type event: :class:`QtWidgets.QMouseEvent`

        """
        # print("NODE %s hover move" % self._name)
        his = [i for i in self._inputs if i._rect.contains(event.pos())]
        hos =  [i for i in self._outputs if i._rect.contains(event.pos())]
        # print("Node MOUSE", event.pos())
        if hos:
            # print("output", hos[0]._name)
            self._update_hover_slot(hos[0])
        elif his:
            # print("input", his[0]._rect)
            self._update_hover_slot(his[0])
        else:
            self._update_hover_slot(False)

        # Call normal behavior
        QtWidgets.QGraphicsItem.hoverMoveEvent(self, event)

        return

    def hoverLeaveEvent(self, event):
        """Re-implement Mouse hover move event

        :param event: Hover move event
        :type event: :class:`QtWidgets.QMouseEvent`

        """
        self._update_hover_slot(False)

        # Call normal behavior
        QtWidgets.QGraphicsItem.hoverLeaveEvent(self, event)

    def mousePressEvent(self, event):
        """Re-implement mousePressEvent from base class

        :param event: Mouse event
        :type event: :class:`QtWidgets.QMouseEvent`

        """
        print("MOUSE PRESS NODE!")

        buttons = event.buttons()
        # modifiers = event.modifiers()

        if buttons == QtCore.Qt.LeftButton:
            # if self._output._rect.contains(event.pos()):
            #     mouse_pos = self.mapToScene(event.pos())
            #     self.scene().start_interactive_edge(self._output, mouse_pos)
            #     event.accept()
            #     return
            for anoutput in self._outputs:
                if anoutput._rect.contains(event.pos()):
                    mouse_pos = self.mapToScene(event.pos())
                    self.scene().start_interactive_edge(anoutput, mouse_pos)
                    self.scene().store_source_node(anoutput)
                    # print(self.scene().source_node._name)
                    event.accept()
                    return
            for aninput in self._inputs:
                if aninput._rect.contains(event.pos()):
                    mouse_pos = self.mapToScene(event.pos())
                    self.scene().start_interactive_edge(aninput, mouse_pos)
                    event.accept()
                    return

        QtWidgets.QGraphicsItem.mousePressEvent(self, event)

    # def mouseReleaseEvent(self, event):
    #     """Re-implement mouseReleaseEvent from base class

    #     :param event: Mouse event
    #     :type event: :class:`QtWidgets.QGraphicsSceneMouseEvent`

    #     """
    #     buttons = event.button()

    #     if buttons == QtCore.Qt.LeftButton:
    #         # if self._output._rect.contains(event.pos()):
    #         print(self._output._rect.contains(event.pos()))
    #         print("DROP")
    #         print(event.pos())
    #         print(self._output._rect)

    #     QtWidgets.QGraphicsItem.mouseReleaseEvent(self, event)

    def mouseMoveEvent(self, event):
        """Re-implement mouseMoveEvent from base class

        :param event: Mouse event
        :type event: :class:`QtWidgets.QMouseEvent`

        """
        buttons = event.buttons()
        # modifiers = event.modifiers()

        # print("%s : mouse move event. Hover slot: %s" %(self._name, self._hover_slot))
        # print(self.scene().source_node is not None)

        if self.scene().source_node:
            if self.scene().is_interactive_edge:
                # Edge creation mode
                # print("Node Name: %s, pos: %s" % (self._name, event.pos()))
                event.accept()
                return

        elif buttons == QtCore.Qt.LeftButton:
            if self.scene().is_interactive_edge:

                # Edge creation mode

                # print("Node Name: %s, pos: %s" % (self._name, event.pos()))
                event.accept()
                return

        QtWidgets.QGraphicsItem.mouseMoveEvent(self, event)

    def refresh(self, refresh_edges=True):
        """Refreh node

        :param refresh_edges: If true, also connected edge
        :type refresh_edges: bool

        """
        self.prepareGeometryChange()
        self._update()
        if refresh_edges and self.edges:
            for ahash in self.edges:
                try:
                    self.scene().edges_by_hash[ahash].refresh()
                except KeyError:
                    pass
        self.update()


class NodeSlot(object):

    """
    Base class for edge slot

    """

    INPUT = 0
    OUTPUT = 1

    def __init__(self, name, parent, family=None):
        """Instance this class

        """
        # QtWidgets.QGraphicsItem.__init__(self, parent=parent, scene=scene)
        self._name = name
        self.parent = parent
        self._family = family or self.INPUT
        self._rect = None
        self._edge = set()

    @property
    def active(self):
        if len(self._edge) > 0:
            return True
        return False

    @property
    def name(self):
        """Return the family of the slot

        """
        return self._name

    @property
    def family(self):
        """Return the family of the slot

        """
        return self._family

    @property
    def rect(self):
        """Return bounding box of slot

        """
        return self._rect

    @rect.setter
    def rect(self, value):
        """ Set property rect

        :param value: Rectangle defintion of the slot
        :type value: class::`QtCore.QRectF`

        """
        self._rect = value

    @property
    def center(self):
        """Return center point of the slot in scene coordinates

        """
        return self.parent.mapToScene(self._rect.center())

    @property
    def edge(self):
        """Return hash id of connedcted edge or None

        :rtype: list

        """
        return list(self._edge)

    @edge.setter
    def edge(self, value):
        """Set property edge (replace)

        :type value: str or list

        """
        self._edge = set(value if isinstance(value, list) else [value])

    def add_edge(self, value):
        """Add edge hash(es) to set

        :type value: str or list

        """
        self._edge |= set(value if isinstance(value, list) else [value])

    def remove_edge(self, value):
        """Remove edge hash(es) from set

        :type value: str or list

        """
        self._edge -= set(value if isinstance(value, list) else [value])
