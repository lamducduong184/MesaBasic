"""
VÍ DỤ MESA 2 — Thị trường AMM DỰA TRÊN TÁC NHÂN: trader nhiễu + arbitrageur
Mục tiêu: cho thấy hiện tượng NỔI LÊN — arbitrageur giữ giá pool BÁM giá tham chiếu
bên ngoài, và nhà cung cấp thanh khoản (LP) TÍCH LUỸ PHÍ. Đây là "phiên bản mô phỏng"
của kết quả lý thuyết CFMM:套利 (arbitrage) neo giá pool vào giá thị trường.

Tác nhân:
  - NoiseTrader: mỗi bước giao dịch ngẫu nhiên nhỏ (mua/bán) -> đẩy giá đi lệch.
  - Arbitrageur: nếu |giá_pool - giá_ref|/giá_ref > phí thì swap kéo giá pool về giá_ref.
Giá tham chiếu đi bước ngẫu nhiên (GBM). Pool là AMM tích không đổi x*y=k, phí 0.3%.

Yêu cầu: mesa>=3, numpy, matplotlib. Chạy: python vd_mesa2_amm_market.py
"""
import mesa
import numpy as np
import matplotlib.pyplot as plt


class CPMMPool:
    """AMM tích không đổi x*y=k. Theo dõi phí tích luỹ (quy về token Y)."""
    def __init__(self, x, y, fee=0.003):
        self.x, self.y, self.fee = float(x), float(y), float(fee)
        self.cum_fee_Y = 0.0

    @property
    def price(self):                       # giá X theo Y
        return self.y / self.x

    def swap_x_for_y(self, dx):            # bán X -> giá giảm
        phi = 1 - self.fee
        dy = self.y * phi * dx / (self.x + phi * dx)
        self.x += dx
        self.y -= dy
        self.cum_fee_Y += (1 - phi) * dx * self.price   # phí (X) quy ra Y
        return dy

    def swap_y_for_x(self, dy_in):        # mua X -> giá tăng
        phi = 1 - self.fee
        dx = self.x * phi * dy_in / (self.y + phi * dy_in)
        self.y += dy_in
        self.x -= dx
        self.cum_fee_Y += (1 - phi) * dy_in             # phí (Y)
        return dx

    def swap_to_price(self, target):
        """Swap để đưa giá pool về 'target' (bỏ qua vi chỉnh do phí). Phí vẫn tính."""
        k = self.x * self.y
        xT, yT = np.sqrt(k / target), np.sqrt(k * target)
        if yT > self.y:                    # cần thêm Y (mua X) -> giá tăng
            self.swap_y_for_x((yT - self.y) / (1 - self.fee))
        elif yT < self.y:                  # cần bớt Y (bán X) -> giá giảm
            self.swap_x_for_y((xT - self.x) / (1 - self.fee))


class NoiseTrader(mesa.Agent):
    def __init__(self, model, size=3.0):
        super().__init__(model)
        self.size = size

    def step(self):
        q = self.model.rng.uniform(0.2, 1.0) * self.size
        if self.model.rng.random() < 0.5:
            self.model.pool.swap_x_for_y(q)             # bán X
        else:
            self.model.pool.swap_y_for_x(q * self.model.pool.price)  # mua X


class Arbitrageur(mesa.Agent):
    def step(self):
        pool, P = self.model.pool, self.model.ref_price
        if abs(pool.price - P) / P > pool.fee:          # ngoài dải "không套利"
            pool.swap_to_price(P)                        # kéo giá pool về giá ref


class AMMMarket(mesa.Model):
    def __init__(self, n_noise=15, n_arb=5, sigma=0.01, seed=7):
        super().__init__(rng=seed)
        self.pool = CPMMPool(x=10_000, y=10_000, fee=0.003)
        self.ref_price = self.pool.price
        self.sigma = sigma
        for _ in range(n_noise):
            NoiseTrader(self)
        for _ in range(n_arb):
            Arbitrageur(self)
        self.datacollector = mesa.DataCollector(model_reporters={
            "ref_price": lambda m: m.ref_price,
            "pool_price": lambda m: m.pool.price,
            "tracking_err_%": lambda m: abs(m.pool.price - m.ref_price) / m.ref_price * 100,
            "cum_fee_Y": lambda m: m.pool.cum_fee_Y,
        })

    def step(self):
        # giá tham chiếu đi bước ngẫu nhiên (GBM)
        z = self.rng.normal()
        self.ref_price *= float(np.exp(self.sigma * z - 0.5 * self.sigma ** 2))
        self.agents.shuffle_do("step")     # trader + arbitrageur hành động xen kẽ
        self.datacollector.collect(self)


def demo():
    model = AMMMarket(n_noise=15, n_arb=5, sigma=0.01, seed=7)
    STEPS = 300
    for _ in range(STEPS):
        model.step()

    df = model.datacollector.get_model_vars_dataframe()
    print("=" * 62)
    print("THỊ TRƯỜNG AMM (Mesa): giá pool có bám giá tham chiếu không?")
    print("=" * 62)
    print(f"  Sai số bám giá trung bình : {df['tracking_err_%'].mean():.3f}%")
    print(f"  Sai số bám giá lớn nhất   : {df['tracking_err_%'].max():.3f}%")
    print(f"  Giá ref cuối / giá pool cuối: "
          f"{df['ref_price'].iloc[-1]:.4f} / {df['pool_price'].iloc[-1]:.4f}")
    print(f"  Tổng phí LP thu được (theo Y): {df['cum_fee_Y'].iloc[-1]:,.1f} "
          f"(~{df['cum_fee_Y'].iloc[-1]/10_000*100:.2f}% giá trị 1 phía pool)")
    print("\n  => Dù trader nhiễu liên tục đẩy giá lệch, arbitrageur kéo pool bám ref;")
    print("     LP kiếm phí từ chính dòng giao dịch đó (đánh đổi với IL ở Ví dụ 1).")

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
    axes[0].plot(df.index, df["ref_price"], lw=1.5, label="Giá tham chiếu")
    axes[0].plot(df.index, df["pool_price"], lw=1.0, ls="--", label="Giá pool AMM")
    axes[0].set_title("Giá pool bám giá tham chiếu"); axes[0].legend(fontsize=8)
    axes[0].set_xlabel("Bước"); axes[0].set_ylabel("Giá"); axes[0].grid(alpha=0.3)
    axes[1].plot(df.index, df["cum_fee_Y"], lw=2, color="C2")
    axes[1].set_title("Phí LP tích luỹ (theo Y)")
    axes[1].set_xlabel("Bước"); axes[1].set_ylabel("Phí"); axes[1].grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig("vd_mesa2_amm.png", dpi=120)
    print("\n[Đã lưu hình: vd_mesa2_amm.png]")


if __name__ == "__main__":
    demo()
