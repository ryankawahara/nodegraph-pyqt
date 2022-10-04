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
import os
import random

from Qt import QtCore, QtGui, QtWidgets
# from . import QtOpenGL

from .node import Node
from .constant import SCENE_WIDTH, SCENE_HEIGHT

RESOURCES = os.path.dirname(os.path.realpath(__file__))


class View(QtWidgets.QGraphicsView):

    """
    Provides custom implementation of QGraphicsView

    """

    def __init__(self, scene, parent=None, is_zoom=False, scale=1, movable=True):
        """Create an instance of this class

        :param scene: Scene reference
        :type scene: :class:`nodegraph.nodegraphScene.Scene`

        :param parent: Parent widget
        :type parent: mixed

        :returns: An instance of this class
        :rtype: :class:`nodegraph.nodegraphView.View`

        """
        QtWidgets.QGraphicsView.__init__(self, scene, parent)
        self._last_mouse_pos = QtCore.QPoint(0, 0)
        self._width = SCENE_WIDTH
        self._height = SCENE_HEIGHT
        self._scale = scale
        self._is_view_initialised = False
        self._is_pan = False
        self._is_zoom = is_zoom
        self._movable = movable

        # Custom mouse cursors
        img = QtGui.QPixmap(
            os.path.join(RESOURCES, "bitmap", "arrow_plus.png"))
        self.arrow_plus_cursor = QtGui.QCursor(img, hotX=0, hotY=0)
        img = QtGui.QPixmap(
            os.path.join(RESOURCES, "bitmap", "arrow_minus.png"))
        self.arrow_minus_cursor = QtGui.QCursor(img, hotX=0, hotY=0)
        img = QtGui.QPixmap(
            os.path.join(RESOURCES, "bitmap", "arrow_cross.png"))
        self.arrow_cross_cursor = QtGui.QCursor(img, hotX=0, hotY=0)

        # Set scene
        self.setScene(scene)

        # Set scene rectangle
        self.scene().setSceneRect(
            QtCore.QRectF(-self._width / 2, -self._height / 2,
                          self._width, self._height))

        # Enable OpenGL
        # GL_format = QtOpenGL.QGLFormat(QtOpenGL.QGL.SampleBuffers)
        # viewport = QtOpenGL.QGLWidget(GL_format)
        # self.setViewport(viewport)

        # Settings
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setResizeAnchor(QtWidgets.QGraphicsView.AnchorViewCenter)
        self.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        self.setRenderHint(QtGui.QPainter.Antialiasing)
        # self.setRenderHint(QtGui.QPainter.TextAntialiasing)
        # self.setRenderHint(QtGui.QPainter.HighQualityAntialiasing)
        self.setViewportUpdateMode(
            QtWidgets.QGraphicsView.BoundingRectViewportUpdate)
        # self.setDragMode(QtWidgets.QGraphicsView.RubberBandDrag)
        self.setDragMode(QtWidgets.QGraphicsView.NoDrag)
        self.setRubberBandSelectionMode(QtCore.Qt.ContainsItemBoundingRect)
        # self.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
        #                    QtWidgets.QSizePolicy.Expanding)

        # Init scene
        self.setInteractive(True)

    def fit_view(self, scale=1, selected=False, padding=50):
        """Set view transform in order to fit all/selected nodes in scene.

        :param selected: If enabled, fit only selected nodes
        :type selected: bool

        :param padding: Add padding around the target rectangle
        :type padding: int

        """
        # Resolve rectangle we want to zoom to
        selection = self.scene().selectedItems()
        if selected and selection:
            scene_rect = self._get_selection_bbox(selection)
        else:
            scene_rect = self.scene().itemsBoundingRect()
            # scene_rect = self.scene().get_nodes_bbox()

        # Add a bit of padding
        scene_rect.adjust(-padding, -padding, padding, padding)

        # Compare ratio, find resulting scale
        # view_ratio = float(self.size().width()) / float(self.size().height())
        # fit_ratio = scene_rect.width() / scene_rect.height()
        x_ratio = scene_rect.width() / float(self.size().width())
        y_ratio = scene_rect.height() / float(self.size().height())
        new_scale = 1 / max(x_ratio, y_ratio)

        if new_scale >= 1:
            # Maximum zoom limit reached.
            # Let's translate to center of rect with reset scale
            self._scale = 1
            self.resetTransform()
            self.centerOn(scene_rect.center())
        elif new_scale < 0.1:
            # Minimum zoom limit reached.
            # Let's translate to center of rect and set zoom to limit
            if (self._scale) != 0.1:
                self._scale = 1
                self.resetTransform()
                self.scale_view(0.1)
            self.centerOn(scene_rect.center())
        elif self._scale is 1:
            # Fit to rectangle while keeping aspect ratio
            self._scale = new_scale
            print("Fit en view")

            self.fitInView(scene_rect, QtCore.Qt.KeepAspectRatio)
        else:
            self.scale_view(self._scale)
            self.centerOn(scene_rect.center())

    def translate_view(self, offset):
        """Translate view by the given offset

        :param offset: Translate the view
        :type offset: :class:`QtCore.QPointF`

        """
        self.setInteractive(False)
        self.translate(offset.x(), offset.y())
        self.setInteractive(True)

    def scale_view(self, scale_factor, limits=True):
        """Scale the view with upper and lower limits if True

        :param scale_factor:
        :type scale_factor: number

        :param limits: If true, will limits scene scale
        :type limits: bool

        """

        new_scale = self._scale * scale_factor
        if limits and (new_scale >= 1.0 or new_scale < 0.1):
            # Respecting scaling limits
            if new_scale >= 1.0:
                self._scale = 1
                self.resetTransform()
                return False
            elif new_scale < 0.1:
                scale_factor = new_scale = 0.1
                self.resetTransform()

        # Update global scale
        self._scale = new_scale
        self.setInteractive(False)
        self.scale(scale_factor, scale_factor)
        self.setInteractive(True)
        return True

    def keyPressEvent(self, event):
        """Re-implement keyPressEvent from base class

        :param event: Key event
        :type event: :class:`QtWidgets.QKeyEvent`

        """
        modifiers = event.modifiers()

        if modifiers & QtCore.Qt.AltModifier:
            if self._movable:
                print("P# ALT ON")
                self.scene()._is_alt_key = True
                self._is_pan = True
                self.setRenderHint(QtGui.QPainter.Antialiasing, False)
                self.setCursor(QtCore.Qt.OpenHandCursor)

        if modifiers & QtCore.Qt.ControlModifier:
            print("P# CTRL ON")
            self.scene()._is_ctrl_key = True

            if not self._is_pan:
                self.setCursor(self.arrow_minus_cursor)

        if modifiers & QtCore.Qt.ShiftModifier:
            print("P# SHIFT ON")
            self.scene()._is_shift_key = True

            if not self._is_pan:
                if not self.scene()._is_ctrl_key:
                    self.setCursor(self.arrow_plus_cursor)
                else:
                    self.setCursor(self.arrow_cross_cursor)

        if event.key() in [QtCore.Qt.Key_Delete, QtCore.Qt.Key_Backspace]:
            self.scene().delete_selected()

        # TODO: Document these!
        if event.text() in ['-', '_']:
            self.scale_view(0.9)
        if event.text() in ['+', '=']:
            self.scale_view(1.1)
        if event.text() in ["f"]:
            self.fit_view(selected=True)
        if event.text() in ["a"]:
            self.fit_view(selected=False)
        # if event.text() in ['t']:
        #     items = self.scene().selectedItems()
        #     for item in items:
        #         item.setSelected(False)
        if event.text() in ['c']:
            n = self.scene().create_node("random%d"
                                         % random.randint(1, 1000000),
                                         inputs=["in", "in1", "in2"])
            n.setPos(self.mapToScene(self._last_mouse_pos) -
                     n.boundingRect().center())

        if event.text() in ['o']:
            for node in self.scene().selectedItems():
                if isinstance(node, Node):
                    node._height -= 10
                    node.refresh()
        if event.text() in ['p']:
            for node in self.scene().selectedItems():
                if isinstance(node, Node):
                    node._height += 10
                    node.refresh()
        if event.text() in ['s']:
            print(self._scale)
        else:
            return QtWidgets.QGraphicsView.keyPressEvent(self, event)

    def keyReleaseEvent(self, event):
        """Re-implement keyReleaseEvent from base class

        :param event: Key event
        :type event: :class:`QtWidgets.QKeyEvent`

        """
        modifiers = event.modifiers()

        if not modifiers & QtCore.Qt.ControlModifier:
            print("R### CTRL OFF")
            self.scene()._is_ctrl_key = False

        if not modifiers & QtCore.Qt.ShiftModifier:
            print("R### SHIFT OFF")
            self.scene()._is_shift_key = False

        if not modifiers & QtCore.Qt.AltModifier:
            print("R### ALT OFF")
            self.scene()._is_alt_key = False

            if not self.scene()._is_mid_mouse:
                self._is_pan = False
                self.setRenderHint(QtGui.QPainter.Antialiasing, True)
                self.setCursor(QtCore.Qt.ArrowCursor)

        if self.scene()._is_shift_key:
            self.setCursor(self.arrow_plus_cursor)
        elif self.scene()._is_ctrl_key:
            self.setCursor(self.arrow_minus_cursor)
        elif not self._is_pan:
            self.setCursor(QtCore.Qt.ArrowCursor)

        return QtWidgets.QGraphicsView.keyReleaseEvent(self, event)

    def mousePressEvent(self, event):
        """Re-implement mousePressEvent from base class

        :param event: Mouse event
        :type event: :class:`QtWidgets.QMouseEvent`

        """
        # print("MOUSE PRESS VIEW!")
        scene = self.scene()  # alias

        # Update registars
        self._last_mouse_pos = event.pos()
        if event.button() == QtCore.Qt.LeftButton:
            scene._is_left_mouse = True
        elif event.button() == QtCore.Qt.MidButton:
            scene._is_mid_mouse = True
        elif event.button() == QtCore.Qt.RightButton:
            scene._is_right_mouse = True

        # Update mode
        if scene._is_left_mouse and scene._is_alt_key:
            self._is_pan = True
            self.setCursor(QtCore.Qt.OpenHandCursor)
        elif scene._is_mid_mouse:
            self._is_pan = True
        else:
            return QtWidgets.QGraphicsView.mousePressEvent(self, event)

    def mouseMoveEvent(self, event):
        """Re-implement mouseMoveEvent from base class

        :param event: Mouse event
        :type event: :class:`QtWidgets.QMouseEvent`

        """
        if self._is_pan:
            delta = (self.mapToScene(self._last_mouse_pos) -
                     self.mapToScene(event.pos()))
            self.setCursor(QtCore.Qt.ClosedHandCursor)
            self.translate_view(delta)
            self._last_mouse_pos = event.pos()
        else:
            self._last_mouse_pos = event.pos()
            QtWidgets.QGraphicsView.mouseMoveEvent(self, event)


    def mouseReleaseEvent(self, event):
        """Re-implement mouseReleaseEvent from base class

        :param event: Mouse event
        :type event: :class:`QtWidgets.QMouseEvent`

        """
        # print("MOUSE RELEASE")
        scene = self.scene()  # alias

        # Update registars
        self._last_mouse_pos = event.pos()
        if event.button() == QtCore.Qt.LeftButton:
            scene._is_left_mouse = False
        elif event.button() == QtCore.Qt.MidButton:
            scene._is_mid_mouse = False
        elif event.button() == QtCore.Qt.RightButton:
            scene._is_right_mouse = False

        # Update mode
        if self._is_pan:
            self._is_pan = False

        # Update mouse icon
        if scene._is_alt_key:
            self.setCursor(QtCore.Qt.OpenHandCursor)
        elif scene._is_shift_key and scene._is_ctrl_key:
            self.setCursor(self.arrow_cross_cursor)
        elif scene._is_shift_key:
            self.setCursor(self.arrow_plus_cursor)
        elif scene._is_ctrl_key:
            self.setCursor(self.arrow_minus_cursor)
        else:
            self.setCursor(QtCore.Qt.ArrowCursor)

        QtWidgets.QGraphicsView.mouseReleaseEvent(self, event)

    def wheelEvent(self, event):
        """Re-implement wheelEvent from base class

        :param event: Wheel event
        :type event: :class:`QtWidgets.QWheelEvent`

        """
        if self._is_zoom:
            # print("WHEELLLLL")
            delta = event.delta()
            # p = event.pos()

            scale_factor = pow(1.25, delta / 240.0)
            self.scale_view(scale_factor)
            event.accept()

    def showEvent(self, event):
        """Re-implent showEvent from base class

        :param event: Show event
        :type event: :class:`QtWidgets.QShowEvent`

        """
        if not self._is_view_initialised:
            self._is_view_initialised = True
            self.fit_view(self._scale)
        QtWidgets.QGraphicsView.showEvent(self, event)

    def focusOutEvent(self, event):
        """Re-implement focusOutEvent from the base class

        Prevent pan mode to stay on when loosing focus to anything outside
        of view

        :param event: Focus event
        :type event: :class:`QtWidgets.QFocusEvent`

        """
        print("Mouse out!")
        # Stop dragging mode if needed
        self.scene()._is_alt_key = False
        self._is_pan = False
        self.setRenderHint(QtGui.QPainter.Antialiasing, True)
        self.setCursor(QtCore.Qt.ArrowCursor)

        QtWidgets.QGraphicsView.focusOutEvent(self, event)

    # def focusInEvent(self, event):
    #     """Re-implement focusInEvent from the base class

    #     :param event: Focus event
    #     :type event: :class:`QtWidgets.QFocusEvent`

    #     """
    #     print("Mouse in!")
    #     modifiers = QtWidgets.QApplication.keyboardModifiers()

    #     if modifiers & QtCore.Qt.AltModifier:
    #         print("P# ALT ON")
    #         self.scene()._is_alt_key = True
    #         self._is_pan = True
    #         self.setRenderHint(QtGui.QPainter.Antialiasing, False)
    #         self.setCursor(QtCore.Qt.OpenHandCursor)

    #     QtWidgets.QGraphicsView.focusOutEvent(self, event)

    def _get_selection_bbox(self, selection):
        """For a given selection of node return the bounding box

        :param selection: List of graphics item
        :type selection: List

        :returns: A Qt rectangle
        :rtype: :class:`QtCore.QRectF`

        """
        top_left = QtCore.QPointF(self._width, self._height)
        bottom_right = QtCore.QPointF(- self._width, - self._height)

        for node in [s for s in selection if isinstance(s, Node)]:
            bbox = node.boundingRect()
            top_left.setX(min(node.x() + bbox.left(), top_left.x()))
            top_left.setY(min(node.y() + bbox.top(), top_left.y()))
            bottom_right.setX(max(node.x() + bbox.right(),
                              bottom_right.x()))
            bottom_right.setY(max(node.y() + bbox.bottom(),
                              bottom_right.y()))
        return QtCore.QRectF(top_left, bottom_right)
