"""
VÍ DỤ MESA 3 — Lan truyền KHỐI trên mạng P2P (NetworkGrid của Mesa)
Mục tiêu: dùng KHÔNG GIAN MẠNG của Mesa để mô phỏng "gossip" — một khối mới phát
sinh tại một node và lan ra toàn mạng. Đo THỜI GIAN LAN TRUYỀN (proxy cho độ trễ
đạt đồng thuận) và so sánh ảnh hưởng của CẤU TRÚC MẠNG.

Cơ chế: mỗi bước, mỗi node đã-biết-khối truyền cho từng hàng xóm chưa biết với xác
suất p_relay (mô hình độ trễ/độ tin cậy đường truyền). Cập nhật HAI PHA (đề cử rồi
commit) để trong 1 bước khối chỉ lan tối đa 1 chặng — sát với đồng hồ mạng rời rạc.

So sánh: mạng ngẫu nhiên Erdős–Rényi vs mạng vô tỉ lệ Barabási–Albert (cùng ~bậc TB).

Yêu cầu: mesa>=3, networkx, matplotlib. Chạy: python vd_mesa3_gossip_network.py
"""
import mesa
import networkx as nx
import matplotlib.pyplot as plt
from mesa.space import NetworkGrid


class Node(mesa.Agent):
    def __init__(self, model):
        super().__init__(model)
        self.informed = False
        self.informed_at = None

    def step(self):
        if not self.informed:
            return
        # get_neighbors trả về danh sách AGENT ở các node kề (self.pos = id node)
        for nb in self.model.grid.get_neighbors(self.pos, include_center=False):
            if (not nb.informed) and self.model.rng.random() < self.model.p_relay:
                self.model.newly_informed.add(nb)   # đề cử (chưa commit)


class GossipModel(mesa.Model):
    def __init__(self, graph, p_relay=0.4, origin=0, seed=1):
        super().__init__(rng=seed)
        self.G = graph
        self.grid = NetworkGrid(self.G)
        self.p_relay = p_relay
        self.t = 0
        for node_id in self.G.nodes():
            Node(self)                              # unique_id tự cấp
        # gán agent vào từng node theo thứ tự
        for agent, node_id in zip(self.agents, self.G.nodes()):
            self.grid.place_agent(agent, node_id)
        # node nguồn biết khối ngay tại t=0
        origin_agent = self.grid.get_cell_list_contents([origin])[0]
        origin_agent.informed = True
        origin_agent.informed_at = 0
        self.datacollector = mesa.DataCollector(model_reporters={
            "frac_informed": lambda m: sum(a.informed for a in m.agents) / len(m.agents)
        })

    def all_informed(self):
        return all(a.informed for a in self.agents)

    def step(self):
        self.datacollector.collect(self)
        self.newly_informed = set()
        self.agents.do("step")                      # pha đề cử
        self.t += 1
        for a in self.newly_informed:               # pha commit
            a.informed = True
            a.informed_at = self.t


def run(graph, label, p_relay=0.4, seed=1, max_steps=60):
    m = GossipModel(graph, p_relay=p_relay, seed=seed)
    for _ in range(max_steps):
        m.step()
        if m.all_informed():
            m.datacollector.collect(m)              # ghi mốc 100%
            break
    df = m.datacollector.get_model_vars_dataframe()
    full_t = m.t if m.all_informed() else None
    return df, full_t, m


def demo():
    N, seed = 200, 1
    # hai topo cùng số node và ~cùng bậc trung bình (~6)
    g_er = nx.erdos_renyi_graph(N, p=6 / (N - 1), seed=seed)
    g_ba = nx.barabasi_albert_graph(N, m=3, seed=seed)

    print("=" * 62)
    print("LAN TRUYỀN KHỐI trên mạng P2P (Mesa NetworkGrid)")
    print("=" * 62)
    results = {}
    for g, label in [(g_er, "Erdős–Rényi (ngẫu nhiên)"),
                     (g_ba, "Barabási–Albert (vô tỉ lệ)")]:
        avg_deg = sum(dict(g.degree()).values()) / g.number_of_nodes()
        df, full_t, _ = run(g, label, p_relay=0.4, seed=seed)
        results[label] = df
        # số bước để đạt >=50% và >=99%
        t50 = int((df["frac_informed"] >= 0.50).idxmax())
        t99 = int((df["frac_informed"] >= 0.99).idxmax())
        print(f"\n[{label}]  N={N}, bậc TB={avg_deg:.1f}")
        print(f"  Bước đạt 50% mạng: {t50} | đạt 99%: {t99} | "
              f"lan hết mạng: {full_t} bước")

    print("\n  => Cấu trúc mạng quyết định tốc độ đồng thuận. Mạng vô tỉ lệ có các HUB")
    print("     bậc cao giúp lan nhanh hơn (nhưng cũng là điểm yếu tập trung).")

    plt.figure(figsize=(8.5, 4.5))
    for label, df in results.items():
        plt.plot(df.index, df["frac_informed"] * 100, marker="o", ms=3, label=label)
    plt.axhline(50, color="gray", ls="--", lw=0.8)
    plt.title("Đường lan truyền khối theo bước (gossip)")
    plt.xlabel("Bước (chặng mạng)"); plt.ylabel("% node đã nhận khối")
    plt.legend(fontsize=8); plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig("vd_mesa3_gossip.png", dpi=120)
    print("\n[Đã lưu hình: vd_mesa3_gossip.png]")


if __name__ == "__main__":
    demo()
