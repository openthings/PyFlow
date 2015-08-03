from PySide import QtCore
from PySide import QtGui
import math
from Settings import Colors
from AbstractGraph import *
from Edge import Edge
from os import listdir, path
import sys
nodes_path = path.abspath('.')+'\\Nodes'
if nodes_path not in sys.path:
    sys.path.append(nodes_path)
import Nodes


class SceneClass(QtGui.QGraphicsScene):
    def __init__(self, parent):
        super(SceneClass, self).__init__(parent)
        self.Type = 'SCENE'
        self.setItemIndexMethod(self.NoIndex)
        self.setParent(parent)
        self.pressed_port = None

    def dragEnterEvent(self, event):
        data = event.mimeData().data('application/x-qabstractitemmodeldatalist')
        if event.mimeData().hasText():
            print 'Enter event accepted'
            print data
            even.accept()
        else:
            print 'Enter event ignored'
            event.ignore()

    def dragMoveEvent(self, event):

        super(GraphWidget, self).dragMoveEvent(event)

    def dropEvent(self, event):
        print 'DROP'
        print event.mimeData()


class NodesBoxListWidget(QtGui.QListWidget):
    def __init__(self, parent, events=True):
        super(NodesBoxListWidget, self).__init__(parent)
        self.parent_item = parent
        self._events = events
        style = "background-color: rgb(80, 80, 80);" +\
                "selection-background-color: rgb(150, 150, 150);" +\
                "selection-color: yellow;" +\
                "border-radius: 2px;" +\
                "font-size: 14px;" +\
                "border-color: black; border-style: outset; border-width: 1px;"
        self.setStyleSheet(style)
        self.setParent(parent)
        self.setFrameShape(QtGui.QFrame.NoFrame)
        self.setFrameShadow(QtGui.QFrame.Sunken)
        self.setObjectName("lw_nodes")
        self.setSortingEnabled(True)
        # self.setDragEnabled(True)
        # self.setDragDropMode(QtGui.QAbstractItemView.DragOnly)

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Return:
            self.parent_item.create_node()
        if self._events:
            if event.key() == QtCore.Qt.Key_Escape:
                self.parent_item.close()
                self.clear()
        super(NodesBoxListWidget, self).keyPressEvent(event)


class NodeBoxLineEdit(QtGui.QLineEdit):
    def __init__(self, parent, events=True):
        super(NodeBoxLineEdit, self).__init__(parent)
        self.setParent(parent)
        self._events = events
        self.parent = parent
        self.setLocale(QtCore.QLocale(QtCore.QLocale.English,
                       QtCore.QLocale.UnitedStates))
        self.setObjectName("le_nodes")
        style = "background-color: rgb(80, 80, 80);" +\
                "border-radius: 2px;" +\
                "font-size: 14px;" +\
                "border-color: black; border-style: outset; border-width: 1px;"
        self.setStyleSheet(style)

    def keyPressEvent(self, event):
        if self._events:
            if event.key() == QtCore.Qt.Key_Escape:
                self.parent.close()
                self.parent.listWidget.clear()
        super(NodeBoxLineEdit, self).keyPressEvent(event)


class NodesBox(QtGui.QWidget):
    def __init__(self, graph):
        super(NodesBox, self).__init__()
        self.graph = graph
        self.setObjectName("nodes_box_form")
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.resize(100, 200)
        self.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Minimum)
        self.name = 'NODE_BOX'
        self.verticalLayout = QtGui.QVBoxLayout(self)
        self.verticalLayout.setSpacing(1)
        self.verticalLayout.setContentsMargins(1, 1, 1, 1)
        self.verticalLayout.setObjectName("verticalLayout")
        self.le_nodes = NodeBoxLineEdit(self)
        self.le_nodes.textChanged.connect(self.le_text_changed)
        self.verticalLayout.addWidget(self.le_nodes)
        self.listWidget = NodesBoxListWidget(self)
        self.verticalLayout.addWidget(self.listWidget)
        self.setVisible(False)
        self.refresh_list('')

    def get_node(self, module, name):

        if hasattr(module, name):
            try:
                mod = getattr(module, name)
                mod = mod(name, self.graph)
                return mod
            except Exception, e:
                print e
                return

    def refresh_list(self, pattern):

        self.listWidget.clear()
        words = [i[:-3] for i in listdir(path.abspath('.')+'\\Nodes') if i.endswith('.py') and '__init__' not in i]
        self.listWidget.addItems([i for i in words if pattern.lower() in i.lower()])
        item = self.listWidget.itemAt(0, 0)
        if item and not item.isSelected():
            item.setSelected(True)

    def create_node(self):
        items = self.listWidget.selectedItems()
        if not len(items) == 0:
            name = items[0].text()
            node = self.get_node(Nodes, name)
            self.graph.add_node(node, self.graph.current_cursor_pose.x(),
                                       self.graph.current_cursor_pose.y())
            if self.listWidget._events:
                self.close()
                self.listWidget.clear()

    def le_text_changed(self):
        if self.le_nodes.text() == '':
            self.le_nodes.setPlaceholderText("enter node name..")
            self.refresh_list('')
            return
        self.refresh_list(self.le_nodes.text())


class RubberRect(QtGui.QGraphicsRectItem, Colors):
    def __init__(self, name):
        super(RubberRect, self).__init__()
        self.name = name
        self.setZValue(1)
        self.setPen(QtGui.QPen(self.kRubberRect, 0.5, QtCore.Qt.SolidLine))
        self.setBrush(QtGui.QBrush(self.kRubberRect))


class GraphWidget(QtGui.QGraphicsView, Colors, AGraph):

    def __init__(self, name):
        QtGui.QGraphicsView.__init__(self)
        AGraph.__init__(self, name)
        self.pressed_item = None
        self.released_item = None
        self._isPanning = False
        self._mousePressed = False
        self.scale(1.5, 1.5)
        self.setViewportUpdateMode(self.FullViewportUpdate)
        self.scene_widget = SceneClass(self)
        self.setScene(self.scene_widget)
        self.setCacheMode(QtGui.QGraphicsView.CacheBackground)
        self.setRenderHint(QtGui.QPainter.Antialiasing)
        self.setTransformationAnchor(QtGui.QGraphicsView.AnchorUnderMouse)
        self.setAcceptDrops(True)
        self.setResizeAnchor(QtGui.QGraphicsView.AnchorViewCenter)
        self.scene_widget.setSceneRect(QtCore.QRect(0, 0, 2000, 2000))
        self._grid_spacing = 50
        self.draw_grid()
        self.factor = 1
        self.scale(self.factor, self.factor)
        self.setWindowTitle(self.tr(name))
        self._alt_key = False
        self._ctrl_key = False
        self.rubber_rect = RubberRect('RubberRect')

        self.real_time_line = QtGui.QGraphicsLineItem(0, 0, 0, 0)
        self.real_time_line.name = 'RealTimeLine'
        self.real_time_line.setZValue(-1)
        self.real_time_line.setPen(QtGui.QPen(self.kWhite,
                                              0.5,
                                              QtCore.Qt.DotLine))

        self.cursor_pressed_pos = QtCore.QPoint(0, 0)
        self.current_cursor_pose = QtCore.QPoint(0, 0)
        self._right_button = False
        self._is_rubber_band_selection = False
        self._draw_real_time_line = False
        self._update_items = False
        self.node_box = NodesBox(self)

    def draw_grid(self):
        rect = self.scene().sceneRect()
        # draw hirizontal
        for i in xrange(int(rect.x()), int(rect.width()), self._grid_spacing):
            self.scene().addLine(rect.x(), rect.y()+i,
                                 rect.width(), rect.y()+i,
                                 QtGui.QPen(self.kGridColor, 0.5,
                                            QtCore.Qt.DotLine))
        # draw vertical
        for i in xrange(int(rect.y()), int(rect.height()), self._grid_spacing):
            self.scene().addLine(rect.x()+i, rect.y(),
                                 rect.x()+i, rect.height(),
                                 QtGui.QPen(self.kGridColor, 0.5,
                                            QtCore.Qt.DotLine))

    def kill_selected_nodes(self):

        for i in self.nodes:
            if i.isSelected() and i in self.nodes and i in self.scene().items():
                for p in i.inputs + i.outputs:
                    for e in p.edge_list:
                        self.remove_edge(e)
                i.prepareGeometryChange()
                self.scene().removeItem(i)
                self.nodes = self.get_nodes()
                # self.nodes.remove(i)

    def get_nodes(self):
        ls = []
        for n in self.scene_widget.items():
            if hasattr(n, 'object_type'):
                if n.object_type == AGObjectTypes.tNode:
                    ls.append(n)
        return ls

    def keyPressEvent(self, event):

        if event.key() == QtCore.Qt.Key_Alt:
            self._alt_key = True
        if event.key() == QtCore.Qt.Key_Delete:
            self.kill_selected_nodes()
        if event.key() == QtCore.Qt.Key_Control:
            self._ctrl_key = True
        if self.node_box.listWidget._events:
            if event.key() == QtCore.Qt.Key_Tab:
                pos = self.mapToGlobal(self.current_cursor_pose.toPoint())
                self.node_box.move(pos.x(), pos.y())
                self.node_box.le_nodes.clear()
                self.node_box.show()
        QtGui.QGraphicsView.keyPressEvent(self, event)

    def keyReleaseEvent(self, event):
        if event.key() == QtCore.Qt.Key_Alt:
            self._alt_key = False
        if event.key() == QtCore.Qt.Key_Control:
            self._ctrl_key = False
        QtGui.QGraphicsView.keyReleaseEvent(self, event)

    def mousePressEvent(self,  event):

        self.pressed_item = self.itemAt(event.pos())
        if not self.pressed_item:
            self.node_box.close()
            self.node_box.le_nodes.clear()
        if self.pressed_item:
            if hasattr(self.pressed_item, 'object_type'):
                if self.pressed_item.object_type == AGObjectTypes.tPort:
                    self.pressed_item.parent.setFlag(QtGui.QGraphicsItem.ItemIsMovable, False)
            else:
                self.pressed_item.setSelected(True)
        self.cursor_pressed_pos = self.mapToScene(event.pos())
        if self.pressed_item and event.button() == QtCore.Qt.LeftButton:
            if hasattr(self.pressed_item, 'object_type'):
                if self.pressed_item.object_type == AGObjectTypes.tPort:
                    self._draw_real_time_line = True
        if event.button() == QtCore.Qt.RightButton:
            self._right_button = True
        if all([event.button() == QtCore.Qt.LeftButton, self._alt_key]):
            self.setDragMode(self.ScrollHandDrag)
        if all([event.button() == QtCore.Qt.LeftButton, not self.pressed_item, not self._alt_key]):
            self._is_rubber_band_selection = True
        super(GraphWidget, self).mousePressEvent(event)

    def mouseMoveEvent(self, event):
        self.current_cursor_pose = self.mapToScene(event.pos())
        if self._draw_real_time_line:
            if self.real_time_line not in self.scene().items():
                self.scene().addItem(self.real_time_line)
            self.real_time_line.setLine(self.cursor_pressed_pos.x(),
                                        self.cursor_pressed_pos.y(),
                                        self.current_cursor_pose.x(),
                                        self.current_cursor_pose.y())
        if self._is_rubber_band_selection:
            if self.rubber_rect not in self.scene().items():
                self.scene().addItem(self.rubber_rect)
            if not self.rubber_rect.isVisible():
                self.rubber_rect.setVisible(True)
            r = QtCore.QRectF(self.cursor_pressed_pos.x(),
                              self.cursor_pressed_pos.y(),
                              self.current_cursor_pose.x()-self.cursor_pressed_pos.x(),
                              self.current_cursor_pose.y()-self.cursor_pressed_pos.y())
            self.rubber_rect.setRect(r.normalized())
        super(GraphWidget, self).mouseMoveEvent(event)

    def remove_item_by_name(self, name):

        # [self.scene().removeItem(i) for i in self.scene().items() if hasattr(i, 'name') and i.name == name]
        [self.scene_widget.removeItem(i) for i in self.scene().items() if hasattr(i, 'name') and i.name == name]

    def mouseReleaseEvent(self, event):

        self.setDragMode(self.NoDrag)
        for n in self.nodes:
            n.setFlag(QtGui.QGraphicsItem.ItemIsMovable)
        if event.button() == QtCore.Qt.RightButton:
            self._right_button = False
        if self._draw_real_time_line:
            self._draw_real_time_line = False
            if self.real_time_line in self.scene().items():
                self.remove_item_by_name('RealTimeLine')
        if self._is_rubber_band_selection:
            self._is_rubber_band_selection = False
            [i.setSelected(True) for i in self.rubber_rect.collidingItems()]
            self.remove_item_by_name(self.rubber_rect.name)
        if event.button() == QtCore.Qt.RightButton:
            self._right_button = False
        self.released_item = self.itemAt(event.pos())
        p_itm = self.pressed_item
        r_itm = self.released_item
        do_connect = True
        for i in [p_itm, r_itm]:
            if not i:
                do_connect = False
                break
            if not hasattr(i, 'object_type'):
                do_connect = False
                break
            if not i.object_type == AGObjectTypes.tPort:
                do_connect = False
                break
        if do_connect:
            self.add_edge(p_itm, r_itm)
        super(GraphWidget, self).mouseReleaseEvent(event)

    def wheelEvent(self, event):

        self.scale_view(math.pow(2.0, event.delta() / 240.0))

    def drawBackground(self, painter, rect):

        # Shadow.
        scene_rect = self.sceneRect()
        # Fill.
        painter.fillRect(rect.intersect(scene_rect), QtGui.QBrush(self.kSceneBackground))
        painter.setPen(QtGui.QPen())
        painter.drawRect(scene_rect)

    def add_node(self, node, x, y):

        AGraph.add_node(self, node, x, y)
        node.label.setPlainText(node.name)
        self.scene_widget.addItem(node)
        node.setPos(QtCore.QPointF(x, y))

    def add_edge(self, src, dst):

        result = AGraph.add_edge(self, src, dst)
        if result:
            if src.type == AGPortTypes.kInput:
                src, dst = dst, src
            edge = Edge(src, dst)
            src.edge_list.append(edge)
            dst.edge_list.append(edge)
            # self.scene().addItem(edge)
            self.scene_widget.addItem(edge)
            self.edges.append(edge)
            return edge

    def remove_edge(self, edge):

        AGraph.remove_edge(self, edge)
        self.edges.remove(edge)
        edge.prepareGeometryChange()
        self.scene_widget.removeItem(edge)

    def scale_view(self, scale_factor):

        self.factor = self.matrix().scale(scale_factor, scale_factor).mapRect(QtCore.QRectF(0, 0, 1, 1)).width()
        if self.factor < 0.5 or self.factor > 5:
            return
        self.scale(scale_factor, scale_factor)