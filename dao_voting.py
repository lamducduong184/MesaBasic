"""
VÍ DỤ MESA — QUẢN TRỊ PHI TẬP TRUNG (1): Bỏ phiếu DAO theo TRỌNG SỐ TOKEN
Học: áp Mesa vào một hệ QUẢN TRỊ. Mỗi BƯỚC = một VÒNG BỎ PHIẾU (proposal).
Quan sát các hiện tượng thật của DAO: tỉ lệ tham gia (turnout) thấp, và "cá voi"
(whale) nắm nhiều token có thể quyết định kết quả.

Mô hình một vòng:
  - Đề xuất có "độ hấp dẫn" mu ~ U(-0.6, 0.6).
  - Mỗi holder tham gia với xác suất `turnout`; nếu tham gia, có giá trị riêng
    v_i = mu + nhiễu_i ; bỏ phiếu YES nếu v_i>0, ngược lại NO.
  - Kiểm phiếu theo TRỌNG SỐ TOKEN: yes_w = Σ token của người bỏ YES, v.v.
  - THÔNG QUA nếu đạt quorum (Σ token tham gia ≥ quorum·tổng cung) VÀ yes_w > no_w.

Chỉ báo sau K vòng: tỉ lệ thông qua, turnout trung bình, và TỈ LỆ CÁ VOI CÓ TÍNH
QUYẾT ĐỊNH (pivotal) — số vòng mà nếu cá voi đổi phiếu/không bỏ thì kết quả đảo.

Yêu cầu: mesa>=3, numpy. Chạy: python dao_voting.py
"""
import mesa
import numpy as np


class Holder(mesa.Agent):
    def __init__(self, model, tokens):
        super().__init__(model)
        self.tokens = int(tokens)
        self.vote = 0                 # +1 YES, -1 NO, 0 vắng mặt (abstain)

    def step(self):
        if self.model.rng.random() > self.model.turnout:
            self.vote = 0             # không tham gia vòng này
            return
        v = self.model.current_mu + self.model.rng.normal(0, self.model.sigma)
        self.vote = 1 if v > 0 else -1


class DAO(mesa.Model):
    def __init__(self, n=100, turnout=0.30, sigma=1.0, quorum=0.20, seed=1):
        super().__init__(rng=seed)
        # phân phối token LỆCH (log-normal) -> có cá voi vừa phải, giống DAO thực tế
        raw = self.rng.lognormal(0.0, 1.3, size=n)
        tokens = np.maximum(1, np.round(raw / raw.sum() * (n * 100)))
        for t in tokens:
            Holder(self, t)
        self.turnout, self.sigma, self.quorum = turnout, sigma, quorum
        self.total_supply = sum(a.tokens for a in self.agents)
        self.whale = max(self.agents, key=lambda a: a.tokens)
        self.records = []

    def _passes(self, weight):
        yes = sum(weight(a) for a in self.agents if a.vote == 1)
        no = sum(weight(a) for a in self.agents if a.vote == -1)
        part = sum(weight(a) for a in self.agents if a.vote != 0)
        total = sum(weight(a) for a in self.agents)
        return (part >= self.quorum * total) and (yes > no)

    def step(self):
        self.current_mu = self.rng.uniform(-0.6, 0.6)
        self.agents.do("step")                    # mọi holder bỏ phiếu cho vòng này
        w = lambda a: a.tokens                     # trọng số = token
        passed = self._passes(w)
        # cá voi có tính quyết định? thử mọi lựa chọn khác của cá voi
        orig, pivotal = self.whale.vote, False
        for alt in (1, -1, 0):
            if alt == orig:
                continue
            self.whale.vote = alt
            if self._passes(w) != passed:
                pivotal = True
        self.whale.vote = orig
        head_major = self._passes(lambda a: 1)     # kết quả nếu 1-người-1-phiếu
        turnout_tok = sum(a.tokens for a in self.agents if a.vote != 0) / self.total_supply
        self.records.append({"passed": passed, "pivotal": pivotal,
                             "same_as_1p1v": passed == head_major,
                             "turnout_tok": turnout_tok})


def demo():
    model = DAO(n=100, turnout=0.30, sigma=1.0, quorum=0.20, seed=1)
    ROUNDS = 500
    for _ in range(ROUNDS):
        model.step()

    import pandas as pd
    df = pd.DataFrame(model.records)
    whale_share = model.whale.tokens / model.total_supply
    print("=" * 62)
    print("BỎ PHIẾU DAO THEO TRỌNG SỐ TOKEN (Mesa)")
    print("=" * 62)
    print(f"  Số holder: 100 | tổng cung: {model.total_supply:,} token")
    print(f"  Cá voi lớn nhất nắm: {model.whale.tokens:,} token "
          f"({whale_share*100:.1f}% tổng cung)")
    print(f"  Turnout theo token (trung bình): {df['turnout_tok'].mean()*100:.1f}%")
    print(f"  Tỉ lệ đề xuất được THÔNG QUA   : {df['passed'].mean()*100:.1f}%")
    print(f"  Số vòng CÁ VOI có tính quyết định (pivotal): "
          f"{df['pivotal'].mean()*100:.1f}%")
    print(f"  Số vòng kết quả GIỐNG '1 người 1 phiếu'     : "
          f"{df['same_as_1p1v'].mean()*100:.1f}%")
    print("\n  => Với turnout thấp và phân phối token lệch, MỘT cá voi có thể là người")
    print("     quyết định trong một tỉ lệ đáng kể các vòng; kết quả theo token có thể")
    print("     LỆCH khỏi ý chí đa số đầu người. Đây là bài toán 'plutocracy' của DAO.")


if __name__ == "__main__":
    demo()
