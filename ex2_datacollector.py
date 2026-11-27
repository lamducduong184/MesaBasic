"""
VÍ DỤ MESA — BƯỚC 2: Thu thập dữ liệu theo thời gian với DataCollector

Mục tiêu bài học:
  Biết cách GHI LẠI trạng thái của hệ thống qua từng bước mô phỏng
  để phục vụ phân tích số liệu và vẽ đồ thị ở các bài tiếp theo.

Kịch bản mô phỏng:
  - Hệ thống có 10 ví (Holder), mỗi ví ban đầu có 100 token.
  - Ở mỗi bước thời gian, mỗi ví nhận thêm một phần thưởng ngẫu nhiên
    từ 0 đến 5 token (giống phần thưởng staking).
  - Ta dùng DataCollector để tự động ghi lại TỔNG CUNG, SỐ DƯ TRUNG BÌNH
    của toàn hệ thống và SỐ DƯ RIÊNG của từng ví theo thời gian.

Kiến thức mới trong Mesa 3.x:
  1. Khai báo mesa.DataCollector(model_reporters=..., agent_reporters=...)
  2. Gọi self.datacollector.collect(self) ở mỗi bước để lưu dữ liệu
  3. Lấy bảng kết quả bằng:
     - get_model_vars_dataframe()  (dữ liệu toàn hệ thống)
     - get_agent_vars_dataframe()  (dữ liệu chi tiết từng tác nhân)

Cách chạy: python ex2_datacollector.py
"""
import mesa


# ==============================================================================
# PHẦN 1: CÁC HÀM THỐNG KÊ TOÀN HỆ THỐNG (dùng cho model_reporters)
# Mỗi hàm nhận vào tham số là `model` và trả về một con số muốn ghi lại.
# ==============================================================================

def tinh_tong_cung(model):
    """Tính tổng số token của tất cả các ví đang có trong hệ thống."""
    tong = 0
    # Duyệt qua từng ví (tác nhân) trong danh sách model.agents
    for vi in model.agents:
        tong = tong + vi.tokens
    return tong


def tinh_trung_binh(model):
    """Tính số token trung bình trên mỗi ví."""
    tong_token = tinh_tong_cung(model)
    so_luong_vi = len(model.agents)
    return tong_token / so_luong_vi


# ==============================================================================
# PHẦN 2: ĐỊNH NGHĨA TÁC NHÂN (AGENT) — ĐẠI DIỆN CHO MỖI VÍ
# ==============================================================================

class Holder(mesa.Agent):
    """Mỗi đối tượng Holder đại diện cho một ví nắm giữ token."""

    def __init__(self, model):
        # Bắt buộc gọi dòng này trong Mesa 3.x:
        #   - Tự động cấp mã số riêng (unique_id) cho ví
        #   - Tự động thêm ví vào danh sách quản lý chung `model.agents`
        super().__init__(model)

        # Trạng thái ban đầu: mỗi ví có 100 token
        self.tokens = 100

    def step(self):
        """Hành động của ví trong 1 bước thời gian: nhận thưởng ngẫu nhiên."""
        # Sinh một số nguyên ngẫu nhiên từ 0 đến 5.
        # Lưu ý: hàm integers(0, 6) lấy các số 0, 1, 2, 3, 4, 5 (KHÔNG gồm số 6).
        phan_thuong = int(self.model.rng.integers(0, 6))

        # Cộng phần thưởng vào số dư hiện có của ví
        self.tokens = self.tokens + phan_thuong


# ==============================================================================
# PHẦN 3: ĐỊNH NGHĨA MÔ HÌNH (MODEL) & BỘ THU THẬP DỮ LIỆU (DataCollector)
# ==============================================================================

class RewardModel(mesa.Model):
    """Mô hình hệ thống phát thưởng token cho các ví qua từng bước."""

    def __init__(self, so_luong_vi=10, seed=1):
        # Khởi tạo mô hình Mesa.
        # Tham số `rng=seed` cố định bộ sinh số ngẫu nhiên để mỗi lần chạy lại
        # chương trình đều cho ra cùng một kết quả (dễ kiểm tra và giảng dạy).
        super().__init__(rng=seed)

        # Bước 1: Tạo ra các ví (Holder).
        # Không cần tự thêm vào list, vì Holder(self) đã tự đăng ký vào self.agents.
        for i in range(so_luong_vi):
            Holder(self)

        # Bước 2: Khai báo DataCollector để tự động ghi chép dữ liệu ở mỗi bước.
        self.datacollector = mesa.DataCollector(
            # (a) Dữ liệu CẤP MÔ HÌNH: mỗi bước ghi 1 dòng cho toàn hệ thống.
            #     Cấu trúc: {"Tên cột trong bảng": tên_hàm_tính_toán}
            #     Lưu ý: chỉ truyền TÊN HÀM (không có dấu ngoặc ()),
            #     để Mesa tự động gọi hàm đó vào mỗi bước mô phỏng.
            model_reporters={
                "TongCung": tinh_tong_cung,
                "TrungBinh": tinh_trung_binh,
            },
            # (b) Dữ liệu CẤP TÁC NHÂN: mỗi bước ghi trạng thái của TỪNG ví riêng lẻ.
            #     Cấu trúc: {"Tên cột trong bảng": "tên_thuộc_tính_của_agent"}
            agent_reporters={
                "tokens": "tokens",
            },
        )

    def step(self):
        """Thực hiện 1 bước chạy của toàn bộ mô hình."""
        # 1. GHI LẠI trạng thái hiện tại TRƯỚC khi phát thưởng bước này
        #    (nhờ vậy dòng đầu tiên lưu đúng trạng thái ban đầu: 1000 token).
        self.datacollector.collect(self)

        # 2. Gọi hàm step() của tất cả các ví theo thứ tự ngẫu nhiên.
        self.agents.shuffle_do("step")


# ==============================================================================
# PHẦN 4: CHẠY MÔ PHỎNG VÀ IN KẾT QUẢ
# ==============================================================================

if __name__ == "__main__":
    # Thiết lập các tham số đầu vào
    so_vi = 10
    so_buoc = 20

    # Tạo mô hình và chạy mô phỏng qua 20 bước
    model = RewardModel(so_luong_vi=so_vi, seed=1)
    for buoc in range(so_buoc):
        model.step()

    # --- KẾT QUẢ 1: Dữ liệu cấp mô hình (toàn hệ thống) ---
    # Hàm trả về một bảng dữ liệu (DataFrame của thư viện pandas)
    bang_mo_hinh = model.datacollector.get_model_vars_dataframe()

    print("=== 1. TỔNG CUNG & SỐ DƯ TRUNG BÌNH (5 bước đầu tiên) ===")
    print(bang_mo_hinh.head())   # .head() hiển thị 5 dòng đầu của bảng

    print("\n=== 2. TỔNG CUNG & SỐ DƯ TRUNG BÌNH (5 bước cuối cùng) ===")
    print(bang_mo_hinh.tail())   # .tail() hiển thị 5 dòng cuối của bảng

    # Lấy giá trị cột "TongCung" tại dòng đầu tiên (iloc[0]) và dòng cuối (iloc[-1])
    tong_cung_dau = bang_mo_hinh["TongCung"].iloc[0]
    tong_cung_cuoi = bang_mo_hinh["TongCung"].iloc[-1]

    print(f"\n=> Tổng cung tăng từ {tong_cung_dau} lên {tong_cung_cuoi} token "
          f"sau {so_buoc} bước chạy.")

    # --- KẾT QUẢ 2: Dữ liệu cấp tác nhân (từng ví riêng lẻ) ---
    # Mỗi dòng cho biết tại bước nào (Step), ví số mấy (AgentID) đang có bao nhiêu token
    bang_tac_nhan = model.datacollector.get_agent_vars_dataframe()

    print("\n=== 3. SỐ DƯ CHI TIẾT CỦA TỪNG VÍ (5 dòng cuối cùng) ===")
    print(bang_tac_nhan.tail())

    print("\nNhận xét: DataCollector trả về các bảng dữ liệu (DataFrame) "
          "rất thuận tiện để phân tích và vẽ đồ thị.")
