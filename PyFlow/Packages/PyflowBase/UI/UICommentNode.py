"""@file CommentNode.py
"""
from types import MethodType

from Qt.QtWidgets import QGraphicsTextItem
from Qt.QtWidgets import QGraphicsItem
from Qt.QtWidgets import QGraphicsWidget
from Qt.QtWidgets import QInputDialog
from Qt.QtWidgets import QGraphicsItemGroup
from Qt.QtWidgets import QGraphicsProxyWidget
from Qt.QtWidgets import QStyle
from Qt.QtWidgets import QLabel
from Qt.QtWidgets import QLineEdit
from Qt.QtWidgets import QTextBrowser
from Qt.QtWidgets import QPushButton
from Qt.QtWidgets import QMenu
from Qt import QtGui
from Qt import QtCore

from PyFlow.UI.Canvas.UICommon import *
from PyFlow.UI import RESOURCES_DIR
from PyFlow.UI.Canvas.Painters import NodePainter
from PyFlow.UI.Utils.Settings import (Spacings, Colors)
from PyFlow.UI.Canvas.UINodeBase import UINodeBase
from PyFlow.UI.Canvas.UINodeBase import NodeName
from PyFlow.UI.Canvas.UIPinBase import UICommentPinBase
from PyFlow.UI.Widgets.PropertiesFramework import CollapsibleFormWidget
from PyFlow.UI.Widgets.TextEditDialog import TextEditDialog
import weakref


class UICommentNode(UINodeBase):
    layer = 0

    def __init__(self, raw_node):
        super(UICommentNode, self).__init__(raw_node)
        self.color = Colors.AbsoluteBlack
        self.color.setAlpha(80)
        self.isCommentNode = True
        self.resizable = True
        self.owningNodes = set()
        UICommentNode.layer += 1
        self.setZValue(UICommentNode.layer)
        self.editMessageAction = self._menu.addAction("Edit message")
        self.editMessageAction.setData(NodeActionButtonInfo(RESOURCES_DIR + "/rename.svg"))
        self.editMessageAction.triggered.connect(self.onChangeMessage)
        self.partiallyIntersectedConnections = set()

    def serializationHook(self):
        original = super(UICommentNode, self).serializationHook()
        original["owningNodes"] = list(set([n.name for n in self.owningNodes]))
        return original

    def onChangeMessage(self):
        dialog = TextEditDialog(self.nodeNameWidget.getFont(), self.labelTextColor)
        dialog.move(QtGui.QCursor.pos())
        dialog.zoomIn(10)
        dialog.exec_()
        try:
            html, accepted = dialog.getResult()
            if accepted:
                self.nodeNameWidget.setHtml(html)
                self.updateNodeShape()
        except:
            pass
        self.setFocus()

    def kill(self, *args, **kwargs):
        # Do not forget to remove collapsed nodes!
        if self.collapsed:
            for node in self.owningNodes:
                node.kill()
        super(UICommentNode, self).kill(*args, **kwargs)

    def hideOwningNodes(self):
        for node in self.owningNodes:
            node.hide()
            # hide fully contained connections
            for pin in node.UIPins.values():
                for connection in pin.uiConnectionList:
                    if self.sceneBoundingRect().contains(connection.sceneBoundingRect()):
                        connection.hide()

    def onVisibilityChanged(self, bVisible):
        for node in self.owningNodes:
            if not self.collapsed:
                node.setVisible(bVisible)
                for pin in node.UIPins.values():
                    for connection in pin.uiConnectionList:
                        if bVisible:
                            connection.setVisible(bVisible)
                        else:
                            # Hide connection only if fully contained
                            if self.sceneBoundingRect().contains(connection.sceneBoundingRect()):
                                connection.setVisible(bVisible)
                            else:
                                print(connection)

    def updateOwningCommentNode(self):
        super(UICommentNode, self).updateOwningCommentNode()

        if self.owningCommentNode is not None:
            self.setZValue(self.owningCommentNode.zValue() + 1)

    def itemChange(self, change, value):
        return super(UICommentNode, self).itemChange(change, value)

    def mousePressEvent(self, event):
        self.mousePressPos = event.pos()
        super(UICommentNode, self).mousePressEvent(event)

        zValue = self.zValue()
        partiallyCollidedComments = set()
        for node in self.getCollidedNodes(False):
            if node.isCommentNode:
                partiallyCollidedComments.add(node)
                if self.zValue() <= node.zValue():
                    if self.sceneBoundingRect().contains(node.sceneBoundingRect()):
                        continue
                    zValue += 1
        if len(partiallyCollidedComments) == 0:
            zValue = 0
        self.setZValue(zValue)

    def mouseReleaseEvent(self, event):
        super(UICommentNode, self).mouseReleaseEvent(event)
        if not self.collapsed:
            collidingNodes = self.getCollidedNodes()
            for node in collidingNodes:
                node.updateOwningCommentNode()

    def getLeftSideEdgesPoint(self):
        frame = self.sceneBoundingRect()
        x = frame.topLeft().x()
        y = frame.topLeft().y() + self.labelHeight
        result = QtCore.QPointF(x, y)
        return result

    def getRightSideEdgesPoint(self):
        frame = self.sceneBoundingRect()
        x = frame.topRight().x()
        y = frame.topRight().y() + self.labelHeight
        result = QtCore.QPointF(x, y)
        return result

    def aboutToCollapse(self, futureCollapseState):
        if futureCollapseState:
            for node in self.owningNodes:
                if node.owningCommentNode is self:
                    node.hide()
                    for pin in node.UIPins.values():
                        fullyIntersectedConnections = set()
                        for connection in pin.uiConnectionList:
                            if self.sceneBoundingRect().contains(connection.sceneBoundingRect()):
                                fullyIntersectedConnections.add(connection)
                                connection.hide()
                            if self.sceneBoundingRect().intersects(connection.sceneBoundingRect()):
                                if connection not in fullyIntersectedConnections:
                                    self.partiallyIntersectedConnections.add(connection)
                        for con in fullyIntersectedConnections:
                            con.hide()
            # override endpoints getting methods
            for connection in self.partiallyIntersectedConnections:
                if not self.sceneBoundingRect().contains(connection.drawDestination.scenePos()):
                    connection.sourcePositionOverride = self.getRightSideEdgesPoint
                if not self.sceneBoundingRect().contains(connection.drawSource.scenePos()):
                    connection.destinationPositionOverride = self.getLeftSideEdgesPoint
        else:
            for node in self.owningNodes:
                node.show()
                for pin in node.UIPins.values():
                    for connection in pin.uiConnectionList:
                        connection.show()
            for connection in self.partiallyIntersectedConnections:
                connection.sourcePositionOverride = None
                connection.destinationPositionOverride = None
            self.partiallyIntersectedConnections.clear()

    def translate(self, x, y):
        for n in self.owningNodes:
            if not n.isSelected():
                n.translate(x, y)
        super(UICommentNode, self).translate(x, y)

    def paint(self, painter, option, widget):
        NodePainter.asCommentNode(self, painter, option, widget)

    def createPropertiesWidget(self, propertiesWidget):
        baseCategory = CollapsibleFormWidget(headName="Base")
        # name
        le_name = QLineEdit(self.getName())
        le_name.setReadOnly(True)
        # if self.isRenamable():
        le_name.setReadOnly(False)
        le_name.returnPressed.connect(lambda: self.setName(le_name.text()))
        baseCategory.addWidget("Name", le_name)

        # type
        leType = QLineEdit(self.__class__.__name__)
        leType.setReadOnly(True)
        baseCategory.addWidget("Type", leType)

        # pos
        le_pos = QLineEdit("{0} x {1}".format(self.pos().x(), self.pos().y()))
        baseCategory.addWidget("Pos", le_pos)
        propertiesWidget.addWidget(baseCategory)

        appearanceCategory = CollapsibleFormWidget(headName="Appearance")
        pb = QPushButton("...")
        pb.clicked.connect(lambda: self.onChangeColor(True))
        appearanceCategory.addWidget("Color", pb)
        propertiesWidget.addWidget(appearanceCategory)

        infoCategory = CollapsibleFormWidget(headName="Info")

        doc = QTextBrowser()
        doc.setOpenExternalLinks(True)
        doc.setHtml(self.description())
        infoCategory.addWidget("", doc)
        propertiesWidget.addWidget(infoCategory)
