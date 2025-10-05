import csv
import json
from unittest import case
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import pandas as pd
import numpy as np
import buildings, models, infrastructure

class World:
    def __init__(self):
        self.road_network = infrastructure.RoadNetwork()
        self.energy_grid = infrastructure.EnergyGrid()
        self.water_network = infrastructure.WaterNetwork()
        self.railway_network = infrastructure.RailwayNetwork()
        self.telecom_network = infrastructure.TelecomNetwork()
        self.infrastructure_networks = {
            self.road_network.name: self.road_network,
            self.energy_grid.name: self.energy_grid,
            self.water_network.name: self.water_network,
            self.railway_network.name: self.railway_network,
            self.telecom_network.name: self.telecom_network,       
            }
        self.buildings = {}
        self.edges = []
        self.current_tick = 0    
        self.snapshots = []  
        self.history = []  

    def add_building(self, building):
        self.buildings[building.id] = building
        return building

    def connect_buildings(self, infrastructure_layer, from_building, to_building, custom_attributes=None):
        edge = infrastructure_layer.connect_buildings(from_building, to_building, custom_attributes)
        self.edges.append(edge)
        return edge   

    def tick(self):
        self.current_tick += 1

        for building in sorted([b for b in self.buildings.values() if b.produces and b.status == "active"], key=lambda b: b.priority):
            if building.tick():
                print(f"{building.id} produced resources")
                self.distribute_resources(building)

        for edge in self.edges:
            if edge.attributes.get("status", "active") != "destroyed":
                edge.tick()

        for building in sorted([b for b in self.buildings.values() if not b.produces and b.status == "active"], key=lambda b: b.priority):
            success = building.tick()
            print(f"{building.id} operational: {success}")

        return self.current_tick    

    def distribute_resources(self, building):
        outgoing_edges = [e for e in self.edges if e.from_node.id == building.id and e.attributes.get("status", "active") != "destroyed"]

        if not outgoing_edges:
            return

        for resource, amount in building.produces.items():
            avalible = building.resources.get(resource, 0)
            if avalible <= 0:
                continue

            amount_per_edge = min(avalible, amount) / len(outgoing_edges)
            
            for edge in outgoing_edges:
                if amount_per_edge <= 0: #min(avalible, amount)
                    break

                if resource in edge.to_node.requires:
                    send_amount = min(amount_per_edge, edge.to_node.requires[resource])
                else:
                    send_amount = amount_per_edge

                building.resources[resource] -= send_amount
                edge.send_resource(resource, send_amount)
                print(f"Sent {send_amount} {resource} from {building.id} to {edge.to_node.id}")


    def _is_operational(self, b) -> bool:
    # aktywny, gdy każdy wymagany zasób >= wymaganej ilości
        for r, amt in b.requires.items():
            if b.resources.get(r, 0) < amt:
                return False
        return True

    def update_all_statuses(self):
    # proste reguły active/UPS/offline (jeśli masz UPS, możesz je tu dodać)
        for b in self.buildings.values():
            b.status = "active" if self._is_operational(b) else "offline"



    def _resource_totals(self):
        totals = {}
        for b in self.buildings.values():
            for r, v in (b.resources or {}).items():
                totals[r] = totals.get(r, 0) + v
        return totals

    def status_summary(self):        
        active_buildings = sum(1 for b in self.buildings.values() if b.status == "active")
        active_edges = sum(1 for e in self.edges if e.attributes.get("status", "active") == "active")
        
        resources = {}
        for resource in set(r for b in self.buildings.values() for r in b.resources if b.resources[r] > 0):
            resources[resource] = sum(b.resources.get(resource, 0) for b in self.buildings.values())
        
        return {
            "tick": self.current_tick,
            "buildings": f"{active_buildings}/{len(self.buildings)}",
            "buildings_active": active_buildings,
            "buildings_total": len(self.buildings),
            "infrastructure": f"{active_edges}/{len(self.edges)}",
            "edges_active": active_edges,
            "edges_total": len(self.edges),
            "resources": resources
        }       

    G_snapshots = []

    def log_status(self):
        self.history.append(self.status_summary())

    def execute_attack(self, target_id=None, severity=0.5):
        attacked_something = False
        if target_id in self.buildings:
            building = self.buildings[target_id]
            old_status = building.status

            if severity > 0.8:
                building.status = "destroyed"
                building.efficiency = 0.0
            elif severity > 0.5:
                building.status = "offline"
                building.efficiency = 0.2
            else:
                building.status = "degraded"
                building.efficiency = 1.0 - severity

                for resource in building.resources:
                    building.resources[resource] *= int((1 - severity))

            print(f"Attack on {building.id}: {old_status} -> {building.status}")  
            attacked_sth = True
            for edge in self.edges:
        # Match by layer name, or if edge connects to/from target
                if (edge.attributes.get("layer") == target_id or 
                    edge.from_node.id == target_id or 
                    edge.to_node.id == target_id):

                    old_status = edge.attributes.get("status", "active")

                    if severity > 0.8:
                        edge.attributes["status"] = "destroyed"
                    elif severity > 0.5:
                        edge.attributes["status"] = "damaged"
                        # Store original capacity if not already stored
                        if "original_capacity" not in edge.attributes and "capacity" in edge.attributes:
                            edge.attributes["original_capacity"] = edge.attributes["capacity"]
                        # Reduce capacity
                        if "capacity" in edge.attributes:
                            edge.attributes["capacity"] = int(edge.attributes["capacity"] * (1 - severity))
                    else:
                        # Just reduce capacity
                        if "original_capacity" not in edge.attributes and "capacity" in edge.attributes:
                            edge.attributes["original_capacity"] = edge.attributes["capacity"]
                        if "capacity" in edge.attributes:
                            edge.attributes["capacity"] = int(edge.attributes["capacity"] * (1 - severity))

                    print(f"Attack on {edge.attributes.get('layer', 'unknown')} connection {edge.from_node.id}->{edge.to_node.id}: {old_status} -> {edge.attributes.get('status', 'active')}")
                    attacked_something = True

        if not attacked_something and "-" in target_id:
            parts = target_id.split("-")
            if len(parts) == 2:
                from_id, to_id = parts
                for edge in self.edges:
                    if edge.from_node.id == from_id and edge.to_node.id == to_id:
                        old_status = edge.attributes.get("status", "active")

                        if severity > 0.8:
                            edge.attributes["status"] = "destroyed"
                        elif severity > 0.5:
                            edge.attributes["status"] = "damaged"
                            # Store original capacity if not already stored
                            if "original_capacity" not in edge.attributes and "capacity" in edge.attributes:
                                edge.attributes["original_capacity"] = edge.attributes["capacity"]
                            # Reduce capacity
                            if "capacity" in edge.attributes:
                                edge.attributes["capacity"] = int(edge.attributes["capacity"] * (1 - severity))
                        else:
                            # Just reduce capacity
                            if "original_capacity" not in edge.attributes and "capacity" in edge.attributes:
                                edge.attributes["original_capacity"] = edge.attributes["capacity"]
                            if "capacity" in edge.attributes:
                                edge.attributes["capacity"] = int(edge.attributes["capacity"] * (1 - severity))

                        print(f"Attack on connection {edge.from_node.id}->{edge.to_node.id}: {old_status} -> {edge.attributes.get('status', 'active')}")
                        attacked_something = True

        if not attacked_something:
            print(f"No valid target found for attack")

        return attacked_something
    

    def execute_recovery(self, target_id=None, repair_level=0.8):
        recovered_something = False

        # Recover a specific building
        if target_id in self.buildings:
            building = self.buildings[target_id]
            old_status = building.status

            # Can't recover destroyed buildings
            if building.status != "destroyed":
                if repair_level > 0.8:
                    building.status = "active"
                    building.efficiency = 1.0
                else:
                    building.status = "degraded"
                    building.efficiency = repair_level
                print(f"Recovery of {building.id}: {old_status} -> {building.status}")
                recovered_something = True
            else:
                print(f"Cannot recover destroyed building {building.id}")

        # Recover infrastructure connection
        for edge in self.edges:
            # Match by layer name, or if edge connects to/from target
            if (edge.attributes.get("layer") == target_id or 
                edge.from_node.id == target_id or 
                edge.to_node.id == target_id):

                old_status = edge.attributes.get("status", "active")

                # Can't recover destroyed infrastructure
                if old_status != "destroyed":
                    if repair_level > 0.8:
                        edge.attributes["status"] = "active"
                        # Restore original capacity if available
                        if "original_capacity" in edge.attributes:
                            edge.attributes["capacity"] = edge.attributes["original_capacity"]
                    else:
                        # Improve but not fully recover
                        if old_status == "damaged":
                            if "original_capacity" in edge.attributes:
                                edge.attributes["capacity"] = int(edge.attributes["original_capacity"] * repair_level)

                    print(f"Recovery of {edge.attributes.get('layer', 'unknown')} connection {edge.from_node.id}->{edge.to_node.id}: {old_status} -> {edge.attributes.get('status', 'active')}")
                    recovered_something = True
                else:
                    print(f"Cannot recover destroyed connection {edge.from_node.id}->{edge.to_node.id}")  

         # Check for specific edge format "from-to"
        if not recovered_something and "-" in target_id:
            parts = target_id.split("-")
            if len(parts) == 2:
                from_id, to_id = parts
                for edge in self.edges:
                    if edge.from_node.id == from_id and edge.to_node.id == to_id:
                        old_status = edge.attributes.get("status", "active")

                        # Can't recover destroyed infrastructure
                        if old_status != "destroyed":
                            if repair_level > 0.8:
                                edge.attributes["status"] = "active"
                                # Restore original capacity if available
                                if "original_capacity" in edge.attributes:
                                    edge.attributes["capacity"] = edge.attributes["original_capacity"]
                            else:
                                # Improve but not fully recover
                                if old_status == "damaged":
                                    if "original_capacity" in edge.attributes:
                                        edge.attributes["capacity"] = int(edge.attributes["original_capacity"] * repair_level)

                            print(f"Recovery of connection {edge.from_node.id}->{edge.to_node.id}: {old_status} -> {edge.attributes.get('status', 'active')}")
                            recovered_something = True
                        else:
                            print(f"Cannot recover destroyed connection {edge.from_node.id}->{edge.to_node.id}")

        if not recovered_something:
            print(f"No valid target found for recovery: {target_id}")

        return recovered_something

    
    def build_graph(self):
        G = nx.DiGraph()
        for b in self.buildings.values():
            group = b.__class__.__name__   # np. PowerPlant, WaterPlant, Hospital, ...
            G.add_node(
                b.id,
                status=b.status,
                group=group,   # <-- do layoutu warstwowego
                requires=b.requires,
                produces=b.produces,
            )
        for e in self.edges:
            G.add_edge(
                e.from_node.id,
                e.to_node.id,
                layer=e.attributes.get("layer", "generic"),
                capacity=e.attributes.get("capacity", 1.0),
                travel_time=e.attributes.get("travel_time", 1),
                status=e.attributes.get("status", "active"),
            )
        return G


    def compute_positions(self, G,
                      order=None,
                      base_x_gap=5.0,
                      base_y_gap=0.25,
                      jitter=0.15,
                      min_distance=0.9,
                      repel_iter=300):

        # 1) Zbierz grupy/kolumny
        groups = list({d.get("group", "Other") for _, d in G.nodes(data=True)})
        groups = order if order else sorted(groups)
        per_group = {g: [] for g in groups}
        for n, d in G.nodes(data=True):
            per_group[d.get("group", "Other")].append(n)

        # 2) Auto-skalowanie pionowe: im więcej węzłów w najgęstszej kolumnie,
        #    tym większe odstępy. (gęsta kolumna -> większy y_gap)
        max_in_col = max((len(v) for v in per_group.values()), default=1)
        y_gap = base_y_gap * (1.0 + 0.6*np.log1p(max_in_col))         # „rozciągnij” w pionie
        x_gap = base_x_gap * (1.0 + 0.2*np.log1p(len(groups)))        # trochę szerzej, gdy dużo kolumn

        x_of_group = {g: i * x_gap for i, g in enumerate(groups)}

    # 3) Wstępne pozycje: kolumny + równy rozkład pionowy
        pos = {}
        rng = np.random.default_rng(42)
        for g in groups:
            nodes = per_group[g]
            if not nodes:
                continue
            k = len(nodes)
            ys = (np.arange(k) - (k - 1)/2.0) * y_gap
            for i, n in enumerate(nodes):
                x = x_of_group[g] + jitter * rng.normal()
                y = ys[i] + jitter * rng.normal()
                pos[n] = np.array([x, y], dtype=float)

        # 4) Globalne odpychanie: zapewnij min_distance między wszystkimi parami
        nodes = list(pos.keys())
        md = float(min_distance)
        for _ in range(repel_iter):
            moved = False
            for i in range(len(nodes)):
                pi = pos[nodes[i]]
                for j in range(i+1, len(nodes)):
                    pj = pos[nodes[j]]
                    d = pi - pj
                    dist = np.linalg.norm(d)
                    if dist < md and dist > 1e-9:
                        # odepchnij obie strony w przeciwnych kierunkach
                        dirv = d / dist
                        shift = 0.5 * (md - dist) * dirv
                        pos[nodes[i]] = pi + shift
                        pos[nodes[j]] = pj - shift
                        moved = True
            if not moved:
                break

        # 5) Konwersja dla networkx
        return {n: (float(p[0]), float(p[1])) for n, p in pos.items()}

    

    def capture_snapshot(self):
        """Zapisz migawkę grafu po bieżącym ticku."""
        if not hasattr(self, "_snapshots"):
            self._snapshots = []
        self._snapshots.append(self.build_graph())

    def animate(self, interval_ms=800, seed=42):
        """Pokaż animację z zebranych migawek."""
        snaps = getattr(self, "_snapshots", [])
        if not snaps:
            print("Brak migawek do animacji - uruchom najpierw run()/capture_snapshot().")
            return

        fig, ax = plt.subplots(figsize=(8, 6))
        

        G0 = snaps[0]
        pos = self.compute_positions(G0)

        def update(frame):
            ax.clear()
            G = snaps[frame]

            # kolory węzłów wg statusu
            color_map = {"active": "green", "UPS": "yellow", "offline": "red"}
            node_colors = [color_map.get(G.nodes[n].get("status","active"), "gray") for n in G.nodes()]

            # krawędzie wg warstwy
            edge_colors = []
            for u,v,d in G.edges(data=True):
                layer = d.get("layer","generic")
                edge_colors.append({
                    "Energy Grid":"dimgray",
                    "Road Network":"cornflowerblue",
                    "Water Network":"teal",
                    "Railway Network":"saddlebrown",
                    "Telecom Network":"purple"
                }.get(layer, "lightgray"))

            nx.draw(G, pos, ax=ax,
                    node_color=node_colors, with_labels=False, arrows=True,
                    edge_color=edge_colors,node_size=120,width=0.6)
            ax.set_title(f"Tick {frame+1}")

        anim = FuncAnimation(fig, update, frames=len(snaps), interval=interval_ms, repeat=False)
        return anim


    def animate_with_kpi(self, interval_ms=800, seed=42, max_resources=3, smooth=False):
        snaps = getattr(self, "_snapshots", [])
        hist  = getattr(self, "history", [])
        if not snaps or not hist:
            print("Brak migawek lub historii – uruchom run_with_viz().")
            return

        frames_count = min(len(snaps), len(hist))
        snaps = snaps[:frames_count]
        hist  = hist[:frames_count]

        ticks = [h["tick"] for h in hist]
        b_pct = [ (h["buildings_active"]/h["buildings_total"]*100.0 if h["buildings_total"] else 100.0) for h in hist ]
        e_pct = [ (h["edges_active"]/h["edges_total"]*100.0 if h["edges_total"] else 100.0) for h in hist ]

        res0 = hist[0].get("resources", {})
        top_res = sorted(res0.keys(), key=lambda k: res0[k], reverse=True)[:max_resources]
        res_series = {r: [h["resources"].get(r, 0) for h in hist] for r in top_res}

        # opcjonalne lekkie wygładzanie rolling window
        # if smooth and len(ticks) >= 3:
        #     import numpy as np
        #     def roll(y):
        #         y = np.asarray(y, float)
        #         k = 3
        #         return np.convolve(y, np.ones(k)/k, mode="same")
        #     b_pct = roll(b_pct)
        #     e_pct = roll(e_pct)
        #     for r in top_res:
        #         res_series[r] = roll(res_series[r])

        # --- FIGURA ---
        import matplotlib.pyplot as plt
        import networkx as nx
        fig = plt.figure(figsize=(11, 8), constrained_layout=True)  # 👈
        gs = fig.add_gridspec(2, 1, height_ratios=[2, 1])
        ax_graph = fig.add_subplot(gs[0, 0])
        ax_kpi   = fig.add_subplot(gs[1, 0])

        G0 = snaps[0]
        pos = self.compute_positions(G0,order=["DataCenter", "Hospital", "Magazine", "Depot", "PowerPlant", "WaterPlant"],
    x_gap=6.0,
    y_gap=3.25,
    jitter=0.8,
    min_distance=20, )

        def draw_graph(ax, G):
            ax.clear()
            color_map = {"active": "green", "UPS": "yellow", "offline": "red"}
            node_colors = [color_map.get(G.nodes[n].get("status","active"), "gray") for n in G.nodes()]
            edge_colors = []
            for _,_,d in G.edges(data=True):
                layer = d.get("layer","generic")
                edge_colors.append({
                    "Energy Grid":"dimgray",
                    "Road Network":"cornflowerblue",
                    "Water Network":"teal",
                    "Railway Network":"saddlebrown",
                    "Telecom Network":"purple"
                }.get(layer, "lightgray"))
            nx.draw(G, pos, ax=ax, node_color=node_colors, edge_color=edge_colors,
                    with_labels=True, arrows=True,node_size=120,)
            ax.set_title("Network state")

        def draw_kpi(ax, upto):
            ax.clear()
            # lewa oś – procenty
            l1, = ax.plot(ticks[:upto], b_pct[:upto], label="Buildings active %", linewidth=2)
            l2, = ax.plot(ticks[:upto], e_pct[:upto], label="Edges active %", linewidth=2)
            ax.set_ylim(0, 105)
            ax.set_xlabel("Tick")
            ax.set_ylabel("% active")
            ax.grid(True, alpha=0.25)

            # prawa oś – zasoby
            ax2 = ax.twinx()
            r_lines = []
            for r in top_res:
                ln, = ax2.plot(ticks[:upto], res_series[r][:upto],
                            linestyle="--", linewidth=1.4, label=f"Resource {r}")
                r_lines.append(ln)

            # ładna skala prawej osi
            ax2.margins(y=0.15)
            ax2.tick_params(axis='y', labelsize=9)
            ax2.set_ylabel("resources (sum)")

            # wspólna legenda u góry, bez nakładania
            lines = [l1, l2] + r_lines
            labels = [ln.get_label() for ln in lines]
            ax.legend(lines, labels, loc="upper left", ncol=2, fontsize=9, framealpha=0.8)

            ax.set_title("KPI dashboard")

        def update(frame):
            draw_graph(ax_graph, snaps[frame])
            draw_kpi(ax_kpi, frame+1)
            fig.suptitle(f"Tick {ticks[frame]}", fontsize=12)

        anim = FuncAnimation(fig, update, frames=frames_count, interval=800, repeat=False)
        return anim


    def animate_graph(self, interval_ms=800):
        snaps = getattr(self, "_snapshots", [])
        if not snaps:
            return None

        fig, ax = plt.subplots(figsize=(16, 9))  

        G0 = snaps[0]
        pos = self.compute_positions(
            G0,
            order=["DataCenter", "Hospital", "Magazine", "Depot", "PowerPlant", "WaterPlant"],
            base_x_gap=6.0,
            base_y_gap=0.35,
            jitter=0.2,
            min_distance=1.1,     # większy minimalny odstęp
            repel_iter=500        # więcej iteracji odpychania
        )

        def update(frame):
            ax.clear()
            G = snaps[frame]
            color_map = {"active": "green", "UPS": "yellow", "offline": "red"}
            node_colors = [color_map.get(G.nodes[n].get("status","active"), "gray") for n in G.nodes()]
            edge_colors = []
            for _,_,d in G.edges(data=True):
                layer = d.get("layer","generic")
                edge_colors.append({
                    "Energy Grid":"dimgray",
                    "Road Network":"cornflowerblue",
                    "Water Network":"teal",
                    "Railway Network":"saddlebrown",
                    "Telecom Network":"purple"
                }.get(layer, "lightgray"))

            nx.draw(
                G, pos, ax=ax,
                node_size=160, width=0.6,
                node_color=node_colors, edge_color=edge_colors,
                with_labels=False, arrows=True, 
            )
           
            labels = {n: n for k, n in enumerate(G.nodes()) if k % 1 == 0}
            nx.draw_networkx_labels(G, pos, labels=labels, font_size=7, ax=ax,
                # bbox=dict(facecolor="white", edgecolor="none", alpha=0.6)
            )

            # --- podpisy warstw (nad kolumnami) ---
            groups = sorted({d.get("group", "Other") for _, d in G.nodes(data=True)})
            group_x_positions = {}  

            # średni X dla każdego typu obiektu
            for g in groups:
                xs = [pos[n][0] for n, d in G.nodes(data=True) if d.get("group") == g]
                if xs:
                    group_x_positions[g] = np.mean(xs)

            # znajdź najwyższy punkt Y (żeby napisy były nad węzłami)
            max_y = max(y for (_, y) in pos.values())

            for g, x in group_x_positions.items():
                ax.text(x, max_y + 2, g, ha="center", va="bottom",
                        fontsize=9, fontweight="bold", color="black")
    # ````````    

            ax.set_title(f"Network state • frame {frame+1}")
            ax.margins(0.08)     # oddech od krawędzi

        return FuncAnimation(fig, update, frames=len(snaps), interval=interval_ms, repeat=False)






    def animate_kpi(self, interval_ms=800, max_resources=3):
        hist = getattr(self, "history", [])
        if not hist: return None

        ticks = [h["tick"] for h in hist]
        b_pct = [h["buildings_active"]/h["buildings_total"]*100 for h in hist]
        e_pct = [h["edges_active"]/h["edges_total"]*100 for h in hist]

        res0 = hist[0].get("resources", {})
        top_res = sorted(res0, key=lambda k: res0[k], reverse=True)[:max_resources]
        res_series = {r:[h["resources"].get(r,0) for h in hist] for r in top_res}

        fig, ax = plt.subplots(figsize=(12, 4))
        ax2 = ax.twinx()

        def update(frame):
            ax.clear(); ax2.cla()
            ax.plot(ticks[:frame+1], b_pct[:frame+1], label="Buildings active %", lw=2)
            ax.plot(ticks[:frame+1], e_pct[:frame+1], label="Edges active %", lw=2)
            for r in top_res:
                ax2.plot(ticks[:frame+1], res_series[r][:frame+1], ls="--", lw=1.4, label=f"Resource {r}")
            ax.set_ylim(0, 105)
            ax.set_xlabel("Tick"); ax.set_ylabel("% active"); ax.grid(True, alpha=0.25)
            ax2.set_ylabel("resources (sum)")
            # wspólna legenda
            l1, lab1 = ax.get_legend_handles_labels()
            l2, lab2 = ax2.get_legend_handles_labels()
            ax.legend(l1+l2, lab1+lab2, loc="upper left", ncol=2, fontsize=9)
            ax.set_title("KPI dashboard")

        return FuncAnimation(fig, update, frames=len(ticks), interval=interval_ms, repeat=False)





    def run_with_viz(self, ticks=10, capture_every_tick=True):
        """Uruchom symulację i zbieraj migawki do animacji."""
        
        print("Starting simulation")
        
        self._snapshots = []
        self.history = []

        self.update_all_statuses()
        self.capture_snapshot()
        self.log_status()

        for _ in range(ticks):
            self.update_all_statuses()
            self.tick()
            self.update_all_statuses()

            if capture_every_tick:
                self.capture_snapshot()
            self.log_status()
            print(f"STATUS: {self.status_summary()}")
        print("Simulation complete")
    

    def run(self, ticks=10):
        print("Starting simulation")
        for tick in range(ticks):
            if(tick > 3):
                w = self.buildings["WATER_001"]
                w.status = "offline"
                for resource in w.produces:
                    w.resources[resource] = 0  # wyzerowanie produkcji
            self.tick()
            print(f"STATUS: {self.status_summary()}")
        print("Simulation complete")         



def create_world_from_csv(csv_path_buildings, csv_path_edges):
    world = World()

    rows = []

    with open(csv_path_buildings, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            match row["type"]:
                case "PowerPlant": new_building = buildings.PowerPlant(row["id"])
                case "Magazine": new_building = buildings.Magazine(row["id"])
                case "Hospital": new_building = buildings.Hospital(row["id"])
                case "WaterPlant": new_building = buildings.WaterPlant(row["id"])
                case "DataCenter": new_building = buildings.DataCenter(row["id"])

            new_building.resources = json.loads(row["resources"])
            new_building.requires = json.loads(row["requires"])
            new_building.produces = json.loads(row["produces"])
            new_building.priority = int(row["priority"])

            
            for rt in infrastructure.RESOURCE_TYPES if hasattr(infrastructure, "RESOURCE_TYPES") else [
            "electricity","water","basic_resources","critical_resources",
            "heavy_resources","personnel","data"
            ]:
                new_building.resources.setdefault(rt, 0)



            world.add_building(new_building)


    with open(csv_path_edges, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            from_id = row["from"]
            to_id = row["to"]
            custom_attributes = json.loads(row["attributes_json"])
            
            infrastructure_layer = world.infrastructure_networks.get(row["layer"])
            if infrastructure_layer:
                world.connect_buildings(infrastructure_layer, world.buildings[from_id], world.buildings[to_id], custom_attributes)

            # match row["layer"]:
                # case "Road Network": world.road_network.connect_buildings(world.buildings[from_id], world.buildings[to_id], custom_attributes)
                # case "Energy Grid": world.energy_grid.connect_buildings(world.buildings[from_id], world.buildings[to_id], custom_attributes)
                # case "Water Network": world.water_network.connect_buildings(world.buildings[from_id], world.buildings[to_id], custom_attributes)
                # case "Railway Network": world.railway_network.connect_buildings(world.buildings[from_id], world.buildings[to_id], custom_attributes)

    return world

if __name__ == "__main__":
    w = create_world_from_csv("big_nodes.csv", "big_edges.csv")
    w.run_with_viz(ticks=200)
    anim_graph = w.animate_graph(interval_ms=500)
    anim_kpi   = w.animate_kpi(interval_ms=500)
    if anim_graph:
        plt.show()
    
