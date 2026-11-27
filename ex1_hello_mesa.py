"""
VÍ DỤ MESA — BƯỚC 1: "Hello Mesa" (khung tối giản nhất)
Học: một mô hình Mesa gồm 3 mảnh — Agent, Model, và VÒNG KÍCH HOẠT tác nhân.

API Mesa 3.x cần nhớ:
  - class con của mesa.Agent, gọi super().__init__(model)  -> unique_id TỰ cấp,
    và tác nhân TỰ đăng ký vào model.agents.
  - class con của mesa.Model, gọi super().__init__(rng=seed) để tái lập kết quả.
  - kích hoạt tất cả tác nhân bằng model.agents.shuffle_do("step")  (không dùng
    "scheduler" như các phiên bản Mesa cũ).

Chạy: python ex1_hello_mesa.py
"""
import mesa


class Counter(mesa.Agent):
    def __init__(self, model):
        super().__init__(model)      # bắt buộc: tự cấp unique_id, tự vào model.agents
        self.count = 0

    def step(self):                  # điều tác nhân làm trong 1 bước
        self.count += 1


class MiniModel(mesa.Model):
    def __init__(self, n=5, seed=1):
        super().__init__(rng=seed)   # bắt buộc: khởi tạo sổ đăng ký tác nhân + RNG
        for _ in range(n):
            Counter(self)            # tạo n tác nhân

    def step(self):                  # điều hệ làm trong 1 bước
        self.agents.shuffle_do("step")   # gọi step() của mọi tác nhân theo thứ tự ngẫu nhiên


if __name__ == "__main__":
    model = MiniModel(n=5, seed=1)
    print("unique_id các tác nhân (tự cấp):", [a.unique_id for a in model.agents])
    for _ in range(3):
        model.step()
    print("count sau 3 bước:", [a.count for a in model.agents])
    print("=> Mọi tác nhân đếm tới 3. Đây là toàn bộ 'bộ xương' của một mô hình Mesa.")
