from PyQt5.QtWidgets import QAction, QToolBar, QMainWindow, QGraphicsLineItem, QApplication, QGraphicsScene, QGraphicsView, QGraphicsRectItem, QGraphicsTextItem, QLabel
from PyQt5.QtGui import QBrush, QPen, QFont, QColor, QPainter
from PyQt5.QtCore import Qt, QTimer
import buildings
import sys


NODE_WIDTH = 50
NODE_HEIGHT = 30
NODE_DISTANCE = 5
GROUP_WIDTH = 400
GROUP_HEIGHT = 600


# Example building object (make sure produces and requires exist)
b1 = buildings.PowerPlant("PP0001", resources={"water": 5})
b2 = buildings.WaterPlant("WP0002", resources={"electricity": 5})

class BuildingNode:
    def __init__(self, scene, view, x, y, w, h, building):
        self.building = building
        self.view = view

        # Rectangle node
        self.rect = QGraphicsRectItem(0, 0, w, h)
        self.rect.setBrush(QBrush(Qt.green if self.building.status == "active" else Qt.red))
        self.rect.setPen(QPen(Qt.black, 1))
        self.rect.setPos(x, y)
        self.rect.setAcceptHoverEvents(True)
        self.rect.setEnabled(True)
        self.rect.hoverEnterEvent = self.hoverEnterEvent
        self.rect.hoverLeaveEvent = self.hoverLeaveEvent
        scene.addItem(self.rect)

        # Separate label for building ID
        self.label = QGraphicsTextItem(f"{building.id}", parent=None)
        self.label.setFont(QFont("Arial", 8))
        self.label.setDefaultTextColor(Qt.black)
        self.label.setPos(x + 2, y + 2)
        scene.addItem(self.label)

        # Floating QLabel for tooltip
        self.tooltip = QLabel(view)
        self.tooltip.setStyleSheet("background-color: grey; border: 1px solid black; padding: 2px;")
        self.tooltip.setWindowFlags(Qt.ToolTip)
        self.tooltip.hide()

    def hoverEnterEvent(self, event):
        resource_str = {item: amount for item, amount in self.building.resources.items() if item in self.building.requires}
        produces_str = {item: amount for item, amount in self.building.produces.items()}
        requires_str = {item: amount for item, amount in self.building.requires.items()}
        text = f"Resources: {resource_str}\nProduces: {produces_str}\nRequires: {requires_str}\n Status: {self.building.status}"
        self.tooltip.setText(text)
        self.tooltip.adjustSize()

        scene_pos = self.rect.scenePos()

        view_pos = self.view.mapFromScene(scene_pos)
        global_pos = self.view.viewport().mapToGlobal(view_pos)

        # Move tooltip in screen coords
        self.tooltip.move(global_pos.x(), global_pos.y() - self.tooltip.height() - 5)
        self.tooltip.show()

    def hoverLeaveEvent(self, event):
        self.tooltip.hide()

    def updateNode(self):
        self.rect.setBrush(QBrush(Qt.green if self.building.status == "active" else Qt.red))


class BuildingGroup(QGraphicsRectItem):
    nodes = []
    def __init__(self, x, y, w, h, name, scene, r, g, b, a):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        super().__init__(0, 0, w, h)
        self.setPos(x, y)
        green_transparent = QBrush(QColor(r, g, b, a))
        # Styling
        self.setBrush(QBrush(green_transparent))  # see-through


        # Group label
        label = QGraphicsTextItem(name, self)
        font = QFont("Arial", 10, QFont.Bold)
        label.setFont(font)
        label.setDefaultTextColor(Qt.darkBlue)
        label.setPos(5, 5)

        # Add to scene
        scene.addItem(self)

    def add_node(self, node):
        n = len(self.nodes)
        if n % 2 == 0:
            rel_x = 0
        else:
            rel_x = self.w - NODE_WIDTH

        rel_y = self.h - (1+(n//2)) * (NODE_HEIGHT + NODE_DISTANCE) if self.y > 0 else (n//2) * (NODE_HEIGHT + NODE_DISTANCE)

        node.rect.setParentItem(self)
        node.label.setParentItem(self)
        node.rect.setPos(rel_x, rel_y)
        node.label.setPos(rel_x + 2, rel_y + 2)
        self.nodes.append(node)


class GeneralEdgeSegment(QGraphicsLineItem):
    edges = []
    def __init__(self, x1, y1, x2, y2, info, scene, view):
        super().__init__(x1, y1, x2, y2)
        pen = QPen(Qt.black, 9)
        pen.setCosmetic(True)
        self.setPen(pen)
        self.setAcceptHoverEvents(True)

        self.info = info
        self.view = view

        # floating QLabel tooltip
        self.tooltip = QLabel(view)
        self.tooltip.setStyleSheet("background-color: grey; border: 1px solid black; padding: 2px;")
        self.tooltip.setWindowFlags(Qt.ToolTip)
        self.tooltip.hide()

        scene.addItem(self)

    def hoverEnterEvent(self, event):
        # highlight line
        self.setPen(QPen(Qt.red, 9))

        # show tooltip
        self.tooltip.setText(self.info)
        self.tooltip.adjustSize()

        # position tooltip above start point
        view_pos = self.view.mapFromScene(self.line().p1())
        global_pos = self.view.viewport().mapToGlobal(view_pos)
        self.tooltip.move(global_pos.x(), global_pos.y() - self.tooltip.height() - 5)
        self.tooltip.show()

    def hoverLeaveEvent(self, event):
        # reset line
        self.tooltip.hide()
        self.setPen(QPen(Qt.black, 9))


class GeneralEdge:
    def __init__(self, from_group, to_group, scene, view):
        self.from_group = from_group
        self.to_group = to_group
        self.from_group_middle_axis = from_group.x + from_group.w / 2
        self.to_group_middle_axis = to_group.x + to_group.w / 2

        self.origin_segment = GeneralEdgeSegment(self.from_group_middle_axis,
                                            from_group.y + from_group.h - NODE_HEIGHT if from_group.y > 0 else from_group.y + NODE_HEIGHT,
                                            self.from_group_middle_axis,
                                            0,
                                            "jol",
                                            scene, view)

        self.middle_segment = GeneralEdgeSegment(self.from_group_middle_axis, 0, self.to_group_middle_axis, 0, "jol", scene, view)

        self.finish_segment = GeneralEdgeSegment(self.to_group_middle_axis,
                                            to_group.y + to_group.h - NODE_HEIGHT if to_group.y > 0 else to_group.y  + NODE_HEIGHT,
                                            self.to_group_middle_axis,
                                            0,
                                            "jol",
                                            scene, view)


    def toggle_visibility(self, visible):
        self.origin_segment.setVisible(visible)
        self.middle_segment.setVisible(visible)
        self.finish_segment.setVisible(visible)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Scene + View
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.setCentralWidget(self.view)

        self.node1 = BuildingNode(self.scene, self.view, 0, 0, NODE_WIDTH, NODE_HEIGHT, b1)
        self.node2 = BuildingNode(self.scene, self.view, 0, 0, NODE_WIDTH, NODE_HEIGHT, b2)
        self.power_group = BuildingGroup(0,400, GROUP_WIDTH, GROUP_HEIGHT, "pg", self.scene, 110, 255, 145, 20)
        self.power_group.add_node(self.node1)
        self.water_group = BuildingGroup(700, -1000, GROUP_WIDTH, GROUP_HEIGHT, "pg", self.scene, 110, 255, 245, 20)
        self.water_group.add_node(self.node2)
        self.data_group = BuildingGroup(0, -1000, GROUP_WIDTH, GROUP_HEIGHT, "pg", self.scene, 110, 255, 245, 20)
        self.ge1 = GeneralEdge(self.power_group, self.water_group, self.scene, self.view)
        self.ge2 = GeneralEdge(self.power_group, self.data_group, self.scene, self.view)
        self.ge2.toggle_visibility(True)
        self.ge1.toggle_visibility(True)
        self.tick_count = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.tick)
        self.timer.start(1000)
        self.layers = {
            "electricity": [self.ge1, self.ge2],
            "water": [],
            "roads": []
        }

        toolbar = QToolBar("Layers")
        toolbar.setFloatable(True)
        self.addToolBar(toolbar)
        for layer in self.layers.keys():
            action = QAction(layer.capitalize(), self)
            action.setCheckable(True)
            action.setChecked(True)
            action.toggled.connect(lambda checked, l=layer: self.toggle_layer(l, checked))
            toolbar.addAction(action)

    def toggle_layer(self, layer, visible):
        for edge in self.layers[layer]:
            edge.toggle_visibility(visible)


    def tick(self):
        self.tick_count += 1
        if self.tick_count == 10:
            b1.status = "offline"
        self.node1.updateNode()




app = QApplication(sys.argv)
w1 = MainWindow()
w1.show()
sys.exit(app.exec_())