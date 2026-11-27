"""
VÍ DỤ MESA 1 — "Hello Mesa": mô phỏng PHÂN PHỐI TOKEN & bất bình đẳng nổi lên
Mục tiêu: làm quen KHUNG của Mesa (Agent, Model, AgentSet, DataCollector).

Kịch bản: N ví (holder) ban đầu mỗi ví có 1 token. Mỗi bước, ví nào còn token
sẽ CHUYỂN 1 token cho một ví ngẫu nhiên khác (mô hình trao đổi ngẫu nhiên).
Quan sát: hệ số Gini (đo tập trung của cải) TĂNG DẦN dù luật hoàn toàn "công bằng".

Yêu cầu: mesa>=3, matplotlib. Chạy: python vd_mesa1_token_distribution.py
API Mesa 3.x: Agent(model) tự cấp unique_id & tự đăng ký vào model.agents;
kích hoạt bằng model.agents.shuffle_do("step") (KHÔNG dùng scheduler cũ).
"""
import mesa
import matplotlib.pyplot as plt


def gini(model) -> float:
    """Hệ số Gini của phân phối token: 0 = bình đẳng tuyệt đối, ->1 = tập trung."""
    w = sorted(a.tokens for a in model.agents)
    n = len(w)
    total = sum(w)
    if total == 0:
        return 0.0
    # công thức Gini gọn theo thứ tự tăng dần: (2*sum(i*w_i) )/(n*sum w) - (n+1)/n
    cum = sum((i + 1) * wi for i, wi in enumerate(w))
    return (2.0 * cum) / (n * total) - (n + 1.0) / n


class Wallet(mesa.Agent):
    def __init__(self, model):
        super().__init__(model)          # unique_id tự cấp, tự vào model.agents
        self.tokens = 1

    def step(self):
        if self.tokens > 0:
            # chọn một ví KHÁC ngẫu nhiên để nhận 1 token
            others = [a for a in self.model.agents if a is not self]
            recipient = self.model.random.choice(others)
            recipient.tokens += 1
            self.tokens -= 1


class TokenMarket(mesa.Model):
    def __init__(self, n=100, seed=42):
        super().__init__(rng=seed)       # rng= để tái lập (thay cho seed= đã deprecated)
        for _ in range(n):
            Wallet(self)
        self.datacollector = mesa.DataCollector(
            model_reporters={"Gini": gini},
            agent_reporters={"tokens": "tokens"},
        )

    def step(self):
        self.datacollector.collect(self)
        self.agents.shuffle_do("step")   # kích hoạt ngẫu nhiên tất cả tác nhân


def demo():
    model = TokenMarket(n=100, seed=42)
    STEPS = 200
    for _ in range(STEPS):
        model.step()

    df = model.datacollector.get_model_vars_dataframe()
    print("=" * 60)
    print("PHÂN PHỐI TOKEN — Gini theo thời gian (Mesa)")
    print("=" * 60)
    for t in [0, 10, 50, 100, 199]:
        print(f"  bước {t:>3} | Gini = {df['Gini'].iloc[t]:.3f}")

    # phân phối token cuối cùng
    final = sorted((a.tokens for a in model.agents), reverse=True)
    top10 = sum(final[:10])
    print(f"\n  Ban đầu ai cũng 1 token (Gini=0). Sau {STEPS} bước:")
    print(f"  - Ví giàu nhất giữ {final[0]} token; 10 ví top giữ {top10}/{sum(final)} "
          f"({top10/sum(final)*100:.0f}% tổng cung).")
    print(f"  - Gini cuối = {df['Gini'].iloc[-1]:.3f}  => bất bình đẳng NỔI LÊN "
          f"từ luật công bằng.")

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
    axes[0].plot(df.index, df["Gini"], lw=2)
    axes[0].set_title("Hệ số Gini theo bước"); axes[0].set_xlabel("Bước")
    axes[0].set_ylabel("Gini"); axes[0].grid(alpha=0.3)
    axes[1].bar(range(len(final)), final)
    axes[1].set_title("Phân phối token cuối (giảm dần)")
    axes[1].set_xlabel("Ví (xếp theo số dư)"); axes[1].set_ylabel("Token")
    axes[1].grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig("vd_mesa1_gini.png", dpi=120)
    print("\n[Đã lưu hình: vd_mesa1_gini.png]")


if __name__ == "__main__":
    demo()
