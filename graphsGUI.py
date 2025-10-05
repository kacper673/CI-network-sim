from PyQt5.QtWidgets import QAction, QToolBar, QMainWindow, QGraphicsLineItem, QApplication, QGraphicsScene, QGraphicsView, QGraphicsRectItem, QGraphicsTextItem, QLabel
from PyQt5.QtGui import QBrush, QPen, QFont, QColor
from PyQt5.QtCore import Qt, QTimer
import buildings
import sys
from csv_world_import import World, create_world_from_csv
from models import Edge, Layer

NODE_WIDTH = 50
NODE_HEIGHT = 30
NODE_DISTANCE = 5
GROUP_WIDTH = 400
GROUP_HEIGHT = 600


class BuildingNode:
    def __init__(self, scene, view, x, y, w, h, building, group):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.building = building
        self.view = view
        self.group = group
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
        self.nodes = []
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
        print(node.building.id, rel_x, rel_y, self.y, n//2)
        node.x = rel_x + self.x
        node.y = rel_y + self.y
        node.rect.setParentItem(self)
        node.label.setParentItem(self)
        node.rect.setPos(rel_x, rel_y)
        node.label.setPos(rel_x + 2, rel_y + 2)
        self.nodes.append(node)


class GeneralEdgeSegment(QGraphicsLineItem):
    edges = []
    def __init__(self, x1, y1, x2, y2, info, scene, view):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
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


class GuiEdge:
    def __init__(self, from_node, to_node, scene, view, layer, attributes=None):
        self.view = view
        self.scene = scene
        self.from_node = from_node
        self.to_node = to_node
        self.attributes = attributes
        self.layer = layer
        self.group1 = from_node.group
        self.group2 = to_node.group
        self.from_group = from_node.group
        self.to_group = to_node.group

        self.general_edge = self.does_general_edge_exist(self.group1, self.group2, self.layer)
        atr_str = str(attributes)
        self.general_edge.origin_segment.info += f"From: {from_node.building.id}, To: {to_node.building.id}, {atr_str}\n"
        self.general_edge.finish_segment.info += f"From: {from_node.building.id}, To: {to_node.building.id}, {atr_str}\n"

        from_line_y = self.from_node.y + NODE_HEIGHT / 2
        from_line_x1 = self.general_edge.origin_segment.x1
        from_line_x2 = self.from_node.x + NODE_WIDTH if from_node.x < from_line_x1 else self.from_node.x
        to_line_y = self.to_node.y + NODE_HEIGHT / 2
        to_line_x1 = self.general_edge.finish_segment.x1
        to_line_x2 = self.to_node.x + NODE_WIDTH if to_node.x < to_line_x1 else self.to_node.x

        self.line1 = QGraphicsLineItem(from_line_x1, from_line_y, from_line_x2, from_line_y)
        self.line1.setPen(QPen(Qt.black, 3))
        self.scene.addItem(self.line1)
        self.line1.view = view
        self.line2 = QGraphicsLineItem(to_line_x1, to_line_y, to_line_x2, to_line_y)
        self.line2.setPen(QPen(Qt.black, 3))
        self.scene.addItem(self.line2)
        self.line2.view = view
    def toggle_visibility(self, visible):
        self.line1.setVisible(visible)
        self.line2.setVisible(visible)


    def does_general_edge_exist(self, from_group, to_group, layer):
        for gedge in layer:
            if gedge.from_group == from_group and gedge.to_group == to_group:
                return gedge
        new_general_edge = GeneralEdge(self.group1, self.group2, self.scene, self.view)
        self.layer.append(new_general_edge)
        return new_general_edge


class MainWindow(QMainWindow):
    def __init__(self, world):
        super().__init__()

        # Scene + View
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.setCentralWidget(self.view)

        self.world = world
        self.nodes = {}
        self.power_group = BuildingGroup(0,400, GROUP_WIDTH, GROUP_HEIGHT, "pg", self.scene, 110, 255, 145, 20)
        self.water_group = BuildingGroup(1200, -1000, GROUP_WIDTH, GROUP_HEIGHT, "pg", self.scene, 110, 255, 245, 20)
        self.data_group = BuildingGroup(0, -1000, GROUP_WIDTH, GROUP_HEIGHT, "pg", self.scene, 110, 255, 245, 20)
        self.hospital_group = BuildingGroup(1200, 400, GROUP_WIDTH, GROUP_HEIGHT, "pg", self.scene, 110, 255, 245, 20)
        self.magazine_group = BuildingGroup(600, 400, GROUP_WIDTH, GROUP_HEIGHT, "pg", self.scene, 110, 255, 245, 20)
        for ID, building in self.world.buildings.items():
            first_two = ID[0:2]
            group = None
            match first_two:
                case "PO":
                    group = self.power_group
                case "WA":
                    group = self.water_group
                case "MA":
                    group = self.magazine_group
                case "HO":
                    group = self.hospital_group
                case "DA":
                    group = self.data_group
                case _:
                    continue
            node = BuildingNode(self.scene, self.view, 0, 0, NODE_HEIGHT, NODE_WIDTH, building, group)
            self.nodes[node.building.id] = node
            group.add_node(node)


        self.tick_count = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.tick)
        self.timer.start(1000)
        self.layers = {

            "electricity":[],
            "water":[],
            "road":[],
            "railway":[],
            "data":[]
        }
        for edge in self.world.energy_grid.edges:
            node_from = self.nodes[edge.from_node.id]
            node_to = self.nodes[edge.to_node.id]
            new_edge_gui = GuiEdge(node_from, node_to, self.scene,self.view, self.layers["electricity"], edge.attributes)
            self.layers["electricity"].append(new_edge_gui)

        for edge in self.world.water_network.edges:
            node_from = self.nodes[edge.from_node.id]
            node_to = self.nodes[edge.to_node.id]
            new_edge_gui = GuiEdge(node_from, node_to, self.scene, self.view, self.layers["water"], edge.attributes)
            self.layers["water"].append(new_edge_gui)

        for edge in self.world.road_network.edges:
            node_from = self.nodes[edge.from_node.id]
            node_to = self.nodes[edge.to_node.id]
            new_edge_gui = GuiEdge(node_from, node_to, self.scene, self.view, self.layers["road"], edge.attributes)
            self.layers["road"].append(new_edge_gui)

        for edge in self.world.railway_network.edges:
            node_from = self.nodes[edge.from_node.id]
            node_to = self.nodes[edge.to_node.id]
            new_edge_gui = GuiEdge(node_from, node_to, self.scene, self.view, self.layers["railway"], edge.attributes)
            self.layers["railway"].append(new_edge_gui)

        for edge in self.world.telecom_network.edges:
            node_from = self.nodes[edge.from_node.id]
            node_to = self.nodes[edge.to_node.id]
            new_edge_gui = GuiEdge(node_from, node_to, self.scene, self.view, self.layers["data"], edge.attributes)
            self.layers["data"].append(new_edge_gui)

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
        self.world.tick()
        for id, node in self.nodes.items():
            node.updateNode()
        self.tick_count += 1


w1 = create_world_from_csv("big_nodes.csv", "big_edges.csv")
app = QApplication(sys.argv)
w1 = MainWindow(w1)
w1.show()
sys.exit(app.exec_())