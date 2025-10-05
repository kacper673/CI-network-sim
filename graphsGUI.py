from PyQt5.QtWidgets import QApplication, QGraphicsScene, QGraphicsView, QGraphicsRectItem, QGraphicsTextItem, QLabel
from PyQt5.QtGui import QBrush, QPen, QFont, QColor
from PyQt5.QtCore import Qt, QTimer
import buildings
import sys

app = QApplication([])

scene = QGraphicsScene()
view = QGraphicsView(scene)
view.setMouseTracking(True)
view.viewport().setAttribute(Qt.WA_Hover, True)
view.show()

# Example building object (make sure produces and requires exist)
b1 = buildings.PowerPlant("PP0001", resources={"water": 5})


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
    def __init__(self, x, y, w, h, name, scene, r, g, b, a):
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

    def add_node(self, node, rel_x, rel_y):
        node.rect.setParentItem(self)
        node.label.setParentItem(self)
        node.rect.setPos(rel_x, rel_y)
        node.label.setPos(rel_x + 2, rel_y + 2)

node1 = BuildingNode(scene, view, 0, 0, 30, 30, b1)
power_group = BuildingGroup(0,300, 200, 300, "pg", scene, 110, 255, 145, 20)
power_group.add_node(node1, 0, 0)
water_group = BuildingGroup(700, -300, 200, 300, "pg", scene, 110, 255, 245, 20)
tick_count = 0


def tick():
    global tick_count
    tick_count += 1
    if tick_count == 4:
        b1.status = "offline"
    node1.updateNode()


timer = QTimer()
timer.timeout.connect(tick)
timer.start(1000)
sys.exit(app.exec_())
