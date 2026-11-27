"""
MÔ PHỎNG ĐÀN BAY TỰ DO (BOIDS) — CÁCH 3: SỬ DỤNG THƯ VIỆN MESA 3.x

Mục tiêu bài học:
  Thấy rõ lợi ích khi dùng thư viện Mesa so với lập trình thủ tục (`boids_no_oop.py`)
  và OOP thuần (`boids_oop.py`), đồng thời làm quen với KHÔNG GIAN LIÊN TỤC của Mesa:
    1. Không gian liên tục 2D: `mesa.space.ContinuousSpace` tự quản lý tọa độ
       `agent.pos = (x, y)` và cung cấp sẵn hàm `get_neighbors(pos, radius=...)`
       để tìm nhanh hàng xóm trong tầm nhìn (không cần tự tính công thức Pytago).
    2. Cập nhật đồng bộ 2 pha gọn nhẹ bằng `self.agents.do(...)`:
       - Pha 1: `self.agents.do("tinh_van_toc_moi")`
       - Pha 2: `self.agents.do("di_chuyen")`
    3. Thu thập chỉ số nổi lên (Độ đồng hướng / Polarization) tự động bằng
       `mesa.DataCollector` để vẽ đồ thị song song với hoạt ảnh đàn chim bay.

Kịch bản (Craig Reynolds, 1987 — cùng bộ tham số với 2 bản trước):
  Mỗi con chim chỉ quan sát các con chim trong tầm nhìn và tuân theo 3 quy tắc cục bộ:
    1. Tách nhau (Separation): tránh bay quá sát hàng xóm (< BAN_KINH_TRANH).
    2. Đồng hướng (Alignment): chỉnh hướng bay theo hướng trung bình của hàng xóm.
    3. Tụ đàn (Cohesion)     : bay hướng về vị trí trung tâm của nhóm hàng xóm.

Yêu cầu: mesa>=3, matplotlib.
Cách chạy: python boids_mesa.py
"""
import math
import mesa
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation


# ==============================================================================
# PHẦN 1: CÁC THAM SỐ MÔ PHỎNG (HẰNG SỐ)
# ==============================================================================

SO_CHIM = 40            # Số lượng chim trong đàn
CHIEU_RONG = 100.0      # Chiều rộng không gian bay (trục x: 0 -> 100)
CHIEU_CAO = 100.0       # Chiều cao không gian bay  (trục y: 0 -> 100)

BAN_KINH_NHIN = 15.0    # Tầm nhìn: chim chỉ thấy hàng xóm trong bán kính này
BAN_KINH_TRANH = 5.0    # Khoảng cách an toàn tối thiểu giữa 2 con chim

HE_SO_TACH_NHAU = 0.08  # Độ mạnh của luật 1 (Tách nhau)
HE_SO_DONG_HUONG = 0.05 # Độ mạnh của luật 2 (Đồng hướng)
HE_SO_TU_DAN = 0.008    # Độ mạnh của luật 3 (Tụ đàn)

TOC_DO_TOI_THIEU = 1.0  # Tốc độ tối thiểu (chim không đứng yên)
TOC_DO_TOI_DA = 2.2     # Tốc độ tối đa

LE_BIEN = 15.0          # Khi cách mép khung < LE_BIEN, chim bắt đầu rẽ nhẹ
LUC_QUAY_DAU = 0.35     # Lực rẽ khi lại gần 4 mép khung

SEED = 42               # Cố định số ngẫu nhiên để tái lập kết quả


# ==============================================================================
# PHẦN 2: HÀM THỐNG KÊ CHO `DataCollector`
# (Viết hàm bình thường thay vì lambda để sinh viên dễ đọc.)
# ==============================================================================

def tinh_do_dong_huong(model):
    """
    Đo mức độ đồng bộ hướng bay của cả đàn (Polarization), giá trị từ 0 đến 1:
      - Gần 0: cả đàn bay tán loạn nhiều hướng.
      - Gần 1: cả đàn tự tổ chức bay cùng một hướng (trật tự nổi lên).
    """
    tong_ux = 0.0
    tong_uy = 0.0
    so_chim = len(model.agents)

    if so_chim == 0:
        return 0.0

    for chim in model.agents:
        ux, uy = chim.huong_don_vi()
        tong_ux = tong_ux + ux
        tong_uy = tong_uy + uy

    return math.sqrt(tong_ux * tong_ux + tong_uy * tong_uy) / so_chim


# ==============================================================================
# PHẦN 3: ĐỊNH NGHĨA TÁC NHÂN `Boid` KẾ THỪA `mesa.Agent`
# ==============================================================================

class Boid(mesa.Agent):
    """Đại diện cho một con chim bay trong không gian liên tục của Mesa."""

    def __init__(self, model, vx, vy):
        # Bắt buộc gọi super().__init__(model) trong Mesa 3.x:
        # -> Tự cấp mã unique_id và tự đăng ký vào model.agents
        super().__init__(model)

        # Vận tốc hiện tại (tọa độ self.pos sẽ do model.space quản lý)
        self.vx = vx
        self.vy = vy

        # Biến tạm lưu vận tốc cho bước tiếp theo (phục vụ cập nhật đồng bộ 2 pha)
        self.vx_moi = vx
        self.vy_moi = vy

    def luat_tach_nhau(self):
        """
        LUẬT 1 — TÁCH NHAU (Separation):
        Dùng `space.get_neighbors` tìm các con chim ở quá gần (< BAN_KINH_TRANH)
        và tạo lực đẩy ra xa để tránh va chạm.
        """
        chim_qua_gan = self.model.space.get_neighbors(
            self.pos, radius=BAN_KINH_TRANH, include_center=False
        )
        luc_x = 0.0
        luc_y = 0.0
        x, y = self.pos

        for chim_khac in chim_qua_gan:
            if chim_khac is self:
                continue
            x_khac, y_khac = chim_khac.pos
            luc_x = luc_x + (x - x_khac)
            luc_y = luc_y + (y - y_khac)

        return luc_x * HE_SO_TACH_NHAU, luc_y * HE_SO_TACH_NHAU

    def luat_dong_huong(self, hang_xom):
        """
        LUẬT 2 — ĐỒNG HƯỚNG (Alignment):
        Lái vận tốc của con chim dần về vận tốc trung bình của các hàng xóm.
        """
        tong_vx = 0.0
        tong_vy = 0.0
        dem = 0

        for chim_khac in hang_xom:
            if chim_khac is self:
                continue
            tong_vx = tong_vx + chim_khac.vx
            tong_vy = tong_vy + chim_khac.vy
            dem = dem + 1

        if dem == 0:
            return 0.0, 0.0

        vx_trung_binh = tong_vx / dem
        vy_trung_binh = tong_vy / dem

        luc_x = (vx_trung_binh - self.vx) * HE_SO_DONG_HUONG
        luc_y = (vy_trung_binh - self.vy) * HE_SO_DONG_HUONG
        return luc_x, luc_y

    def luat_tu_dan(self, hang_xom):
        """
        LUẬT 3 — TỤ ĐÀN (Cohesion):
        Kéo con chim bay hướng về vị trí trung tâm (tâm đàn) của các hàng xóm.
        """
        tong_x = 0.0
        tong_y = 0.0
        dem = 0

        for chim_khac in hang_xom:
            if chim_khac is self:
                continue
            x_khac, y_khac = chim_khac.pos
            tong_x = tong_x + x_khac
            tong_y = tong_y + y_khac
            dem = dem + 1

        if dem == 0:
            return 0.0, 0.0

        x, y = self.pos
        tam_x = tong_x / dem
        tam_y = tong_y / dem

        luc_x = (tam_x - x) * HE_SO_TU_DAN
        luc_y = (tam_y - y) * HE_SO_TU_DAN
        return luc_x, luc_y

    def tinh_van_toc_moi(self):
        """
        PHA 1: Tính vận tốc mới dựa trên trạng thái hiện tại của cả đàn
        (chưa thay đổi self.vx, self.vy hay self.pos để đảm bảo cập nhật đồng bộ).
        """
        # Mesa ContinuousSpace tìm sẵn tất cả hàng xóm trong bán kính BAN_KINH_NHIN
        hang_xom = self.model.space.get_neighbors(
            self.pos, radius=BAN_KINH_NHIN, include_center=False
        )

        # Tổng hợp lực từ 3 quy tắc Boids
        tx, ty = self.luat_tach_nhau()
        dx, dy = self.luat_dong_huong(hang_xom)
        cx, cy = self.luat_tu_dan(hang_xom)

        vx_moi = self.vx + tx + dx + cx
        vy_moi = self.vy + ty + dy + cy

        # Rẽ nhẹ quay lại khi bay gần 4 mép khung
        x, y = self.pos
        if x < LE_BIEN:
            vx_moi = vx_moi + LUC_QUAY_DAU
        elif x > CHIEU_RONG - LE_BIEN:
            vx_moi = vx_moi - LUC_QUAY_DAU

        if y < LE_BIEN:
            vy_moi = vy_moi + LUC_QUAY_DAU
        elif y > CHIEU_CAO - LE_BIEN:
            vy_moi = vy_moi - LUC_QUAY_DAU

        # Giới hạn tốc độ trong khoảng [TOC_DO_TOI_THIEU, TOC_DO_TOI_DA]
        toc_do = math.sqrt(vx_moi * vx_moi + vy_moi * vy_moi)
        if toc_do == 0:
            vx_moi, vy_moi = TOC_DO_TOI_THIEU, 0.0
        elif toc_do > TOC_DO_TOI_DA:
            vx_moi = (vx_moi / toc_do) * TOC_DO_TOI_DA
            vy_moi = (vy_moi / toc_do) * TOC_DO_TOI_DA
        elif toc_do < TOC_DO_TOI_THIEU:
            vx_moi = (vx_moi / toc_do) * TOC_DO_TOI_THIEU
            vy_moi = (vy_moi / toc_do) * TOC_DO_TOI_THIEU

        self.vx_moi = vx_moi
        self.vy_moi = vy_moi

    def di_chuyen(self):
        """
        PHA 2: Áp dụng vận tốc mới và nhờ `model.space.move_agent` cập nhật tọa độ.
        """
        self.vx = self.vx_moi
        self.vy = self.vy_moi

        x, y = self.pos
        x_moi = x + self.vx
        y_moi = y + self.vy

        # Kẹp nhẹ trong phạm vi hợp lệ [0, CHIEU_RONG) x [0, CHIEU_CAO) của ContinuousSpace
        x_moi = max(0.0, min(CHIEU_RONG - 0.01, x_moi))
        y_moi = max(0.0, min(CHIEU_CAO - 0.01, y_moi))

        self.model.space.move_agent(self, (x_moi, y_moi))

    def huong_don_vi(self):
        """Trả về vector hướng có độ dài 1 (dùng để vẽ mũi tên đều nhau)."""
        toc_do = math.sqrt(self.vx * self.vx + self.vy * self.vy)
        if toc_do == 0:
            return 1.0, 0.0
        return self.vx / toc_do, self.vy / toc_do


# ==============================================================================
# PHẦN 4: ĐỊNH NGHĨA MÔ HÌNH `DanChimMesa` KẾ THỪA `mesa.Model`
# ==============================================================================

class DanChimMesa(mesa.Model):
    """Mô hình đàn bay tự do Boids xây dựng bằng thư viện Mesa."""

    def __init__(self, so_chim=SO_CHIM, seed=SEED):
        # Khởi tạo mô hình Mesa và cố định bộ sinh số ngẫu nhiên
        super().__init__(rng=seed)

        # Tạo không gian liên tục 2D (torus=False vì chim quay đầu nhẹ ở mép khung)
        self.space = mesa.space.ContinuousSpace(
            x_max=CHIEU_RONG, y_max=CHIEU_CAO, torus=False
        )

        # Tạo các con chim và đặt ngẫu nhiên vào không gian liên tục
        for i in range(so_chim):
            x = self.random.uniform(LE_BIEN, CHIEU_RONG - LE_BIEN)
            y = self.random.uniform(LE_BIEN, CHIEU_CAO - LE_BIEN)

            goc = self.random.uniform(0, 2 * math.pi)
            toc_do = self.random.uniform(TOC_DO_TOI_THIEU, TOC_DO_TOI_DA)
            vx = math.cos(goc) * toc_do
            vy = math.sin(goc) * toc_do

            chim = Boid(self, vx, vy)
            self.space.place_agent(chim, (x, y))

        # Khai báo DataCollector để tự động ghi lại Độ đồng hướng theo từng bước
        self.datacollector = mesa.DataCollector(
            model_reporters={
                "DoDongHuong": tinh_do_dong_huong,
            }
        )

        # Ghi nhận trạng thái ban đầu (bước 0)
        self.datacollector.collect(self)

    def step(self):
        """
        Thực hiện 1 bước mô phỏng đồng bộ (2 pha):
          1. Mọi con chim cùng tính vận tốc mới dựa trên vị trí/vận tốc hiện tại.
          2. Mọi con chim đồng loạt di chuyển sang vị trí mới.
          3. Thu thập dữ liệu thống kê vào DataCollector.
        """
        self.agents.do("tinh_van_toc_moi")
        self.agents.do("di_chuyen")
        self.datacollector.collect(self)

    def lay_du_lieu_ve(self):
        """Trích xuất tọa độ và vector hướng đơn vị của toàn bộ đàn chim để vẽ."""
        xs = []
        ys = []
        uxs = []
        uys = []

        for chim in self.agents:
            x, y = chim.pos
            ux, uy = chim.huong_don_vi()
            xs.append(x)
            ys.append(y)
            uxs.append(ux)
            uys.append(uy)

        return xs, ys, uxs, uys


# ==============================================================================
# PHẦN 5: TRỰC QUAN HÓA CHUYỂN ĐỘNG + ĐỒ THỊ ĐỘ ĐỒNG HƯỚNG BẰNG MATPLOTLIB
# ==============================================================================

def chay_mo_phong(so_buoc=350):
    """Chạy hoạt ảnh đàn chim bay tự do (Mesa) kèm đồ thị Độ đồng hướng."""
    model = DanChimMesa(so_chim=SO_CHIM, seed=SEED)

    # Hai khung hình cạnh nhau: Trái = Không gian bay 2D, Phải = Đồ thị Độ đồng hướng
    fig, (ax_bay, ax_do_thi) = plt.subplots(1, 2, figsize=(12, 5.5))

    # --- Khung trái: Không gian bay 2D ---
    ax_bay.set_xlim(0, CHIEU_RONG)
    ax_bay.set_ylim(0, CHIEU_CAO)
    ax_bay.set_aspect("equal")
    ax_bay.grid(alpha=0.25)

    xs, ys, uxs, uys = model.lay_du_lieu_ve()
    mui_ten = ax_bay.quiver(
        xs, ys, uxs, uys,
        angles="xy", scale_units="xy", scale=0.35,
        width=0.008, headwidth=4, headlength=5,
        color="teal",
    )
    tieu_de_bay = ax_bay.set_title("Boids (Mesa 3.x) — Bước 0")

    # --- Khung phải: Đồ thị Độ đồng hướng lấy từ DataCollector ---
    df = model.datacollector.get_model_vars_dataframe()
    duong_dong_huong, = ax_do_thi.plot(
        df.index, df["DoDongHuong"], color="teal", lw=2, label="Độ đồng hướng"
    )
    ax_do_thi.set_xlim(0, so_buoc)
    ax_do_thi.set_ylim(0, 1.05)
    ax_do_thi.set_xlabel("Bước thời gian")
    ax_do_thi.set_ylabel("Độ đồng hướng (0 -> 1)")
    ax_do_thi.set_title("Tính đồng bộ hướng bay (từ Mesa DataCollector)")
    ax_do_thi.grid(alpha=0.3)
    ax_do_thi.legend(loc="lower right")

    def cap_nhat_khung_hinh(buoc):
        # Chạy 1 bước mô phỏng của Mesa
        model.step()

        # Cập nhật vị trí và hướng mũi tên trên khung trái
        xs_moi, ys_moi, uxs_moi, uys_moi = model.lay_du_lieu_ve()
        mui_ten.set_offsets(list(zip(xs_moi, ys_moi)))
        mui_ten.set_UVC(uxs_moi, uys_moi)

        # Lấy dữ liệu mới nhất từ DataCollector để cập nhật khung phải
        df_moi = model.datacollector.get_model_vars_dataframe()
        do_dong_huong = df_moi["DoDongHuong"].iloc[-1]

        tieu_de_bay.set_text(
            f"Boids (Mesa 3.x) — Bước {buoc + 1} | Độ đồng hướng: {do_dong_huong:.2f}"
        )
        duong_dong_huong.set_data(df_moi.index, df_moi["DoDongHuong"])

        return mui_ten, tieu_de_bay, duong_dong_huong

    anim = FuncAnimation(fig, cap_nhat_khung_hinh, frames=so_buoc, interval=40, repeat=False, blit=False)
    plt.tight_layout()
    plt.show()
    return anim


if __name__ == "__main__":
    chay_mo_phong()
