"""
VÍ DỤ MESA — QUẢN TRỊ PHI TẬP TRUNG (2): SO SÁNH LUẬT BỎ PHIẾU
Cùng một dân số holder và cùng lá phiếu mỗi vòng, ta kiểm phiếu theo BA luật và xem
kết quả & quyền lực cá voi khác nhau thế nào. Đây là góc nhìn THIẾT KẾ CƠ CHẾ /
social choice cho quản trị phi tập trung:

  (1) 1 người 1 phiếu (1p1v):        trọng số = 1            -> đa số đầu người (May's theorem)
  (2) Theo token (token-weighted):    trọng số = token        -> "plutocracy"
  (3) Bỏ phiếu bậc hai (quadratic):   trọng số = sqrt(token)  -> nén bớt quyền lực cá voi

Chỉ báo: tỉ lệ thông qua theo từng luật; tỉ lệ BA LUẬT CÙNG kết luận; và tỉ lệ vòng
mà CÁ VOI có tính quyết định theo từng luật.

Yêu cầu: mesa>=3, numpy. Chạy: python dao_compare_rules.py
"""
import mesa
import numpy as np


class Holder(mesa.Agent):
    def __init__(self, model, tokens):
        super().__init__(model)
        self.tokens = int(tokens)
        self.vote = 0

    def step(self):
        if self.model.rng.random() > self.model.turnout:
            self.vote = 0
            return
        v = self.model.current_mu + self.model.rng.normal(0, self.model.sigma)
        self.vote = 1 if v > 0 else -1


# ba hàm trọng số
RULES = {
    "1p1v":            lambda a: 1.0,
    "token-weighted":  lambda a: float(a.tokens),
    "quadratic (√tok)": lambda a: float(a.tokens) ** 0.5,
}


class DAOCompare(mesa.Model):
    def __init__(self, n=100, turnout=0.30, sigma=1.0, quorum=0.20, seed=1):
        super().__init__(rng=seed)
        raw = self.rng.lognormal(0.0, 1.3, size=n)
        tokens = np.maximum(1, np.round(raw / raw.sum() * (n * 100)))
        for t in tokens:
            Holder(self, t)
        self.turnout, self.sigma, self.quorum = turnout, sigma, quorum
        self.whale = max(self.agents, key=lambda a: a.tokens)
        self.records = []

    def _passes(self, weight):
        yes = sum(weight(a) for a in self.agents if a.vote == 1)
        no = sum(weight(a) for a in self.agents if a.vote == -1)
        part = sum(weight(a) for a in self.agents if a.vote != 0)
        total = sum(weight(a) for a in self.agents)
        return (part >= self.quorum * total) and (yes > no)

    def _whale_pivotal(self, weight, base):
        orig, piv = self.whale.vote, False
        for alt in (1, -1, 0):
            if alt == orig:
                continue
            self.whale.vote = alt
            if self._passes(weight) != base:
                piv = True
        self.whale.vote = orig
        return piv

    def step(self):
        self.current_mu = self.rng.uniform(-0.6, 0.6)
        self.agents.do("step")
        rec = {}
        for name, w in RULES.items():
            p = self._passes(w)
            rec[name] = p
            rec[name + "_pivotal"] = self._whale_pivotal(w, p)
        rec["all_agree"] = len({rec[n] for n in RULES}) == 1
        self.records.append(rec)


def demo():
    model = DAOCompare(n=100, turnout=0.30, sigma=1.0, quorum=0.20, seed=1)
    ROUNDS = 500
    for _ in range(ROUNDS):
        model.step()

    import pandas as pd
    df = pd.DataFrame(model.records)
    whale_share = model.whale.tokens / sum(a.tokens for a in model.agents)
    print("=" * 66)
    print("SO SÁNH LUẬT BỎ PHIẾU DAO (Mesa) — cá voi nắm "
          f"{whale_share*100:.1f}% token")
    print("=" * 66)
    print(f"{'Luật':>18} | {'Tỉ lệ thông qua':>16} | {'Cá voi quyết định':>18}")
    print("-" * 66)
    for name in RULES:
        print(f"{name:>18} | {df[name].mean()*100:>15.1f}% | "
              f"{df[name+'_pivotal'].mean()*100:>17.1f}%")
    print("-" * 66)
    print(f"  Ba luật CÙNG kết luận: {df['all_agree'].mean()*100:.1f}% số vòng "
          f"(=> {100-df['all_agree'].mean()*100:.1f}% số vòng luật chơi làm ĐỔI kết quả)")
    print("\n  => Cùng một ý chí cử tri, LUẬT KIỂM PHIẾU thay đổi kết quả và quyền lực")
    print("     cá voi. Quadratic voting NÉN quyền lực cá voi (√token) so với token-")
    print("     weighted — một phản hồi 'mechanism design' cho vấn đề plutocracy.")


if __name__ == "__main__":
    demo()
