"""
MÔ PHỎNG ĐÀN BAY TỰ DO (BOIDS) — CÁCH 2: SỬ DỤNG OOP (Lập trình hướng đối tượng)

Kịch bản (Craig Reynolds, 1987):
  Không có "chim đầu đàn" chỉ huy. Mỗi con chim chỉ quan sát các con chim ở gần
  và tuân theo đúng 3 quy tắc cục bộ đơn giản:
    1. Tách nhau (Separation): tránh bay quá sát hàng xóm để không va chạm.
    2. Đồng hướng (Alignment): chỉnh hướng bay giống hướng trung bình của hàng xóm.
    3. Tụ đàn (Cohesion)     : bay hướng về vị trí trung tâm của nhóm hàng xóm.

Cách tổ chức SỬ DỤNG OOP (Object-Oriented):
  - Class `Boid`: đóng gói cả DỮ LIỆU (x, y, vx, vy) và HÀNH VI (tách nhau,
    đồng hướng, tụ đàn, di chuyển) của MỘT con chim vào chung một đối tượng.
  - Class `DanChim`: quản lý danh sách các đối tượng `Boid`, điều phối từng bước
    cập nhật đồng bộ và tính toán chỉ số chung của cả đàn.

So sánh trực tiếp với file `boids_no_oop.py` (cùng tham số, cùng seed -> cùng kết quả).
Cách chạy: python boids_oop.py
"""
import math
import random
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

LE_BIEN = 15.0          # Khi vào vùng cách mép khung < LE_BIEN, chim bắt đầu rẽ
LUC_QUAY_DAU = 0.35     # Lực rẽ nhẹ khi lại gần mép khung

SEED = 42               # Cố định số ngẫu nhiên để đối chiếu với bản không OOP


# ==============================================================================
# PHẦN 2: LỚP `Boid` — ĐẠI DIỆN CHO MỘT CON CHIM
# Đóng gói cả trạng thái (thuộc tính) lẫn quy tắc bay (phương thức).
# ==============================================================================

class Boid:
    """Đại diện cho một con chim (tác nhân) trong đàn."""

    def __init__(self, x, y, vx, vy):
        # Trạng thái của riêng con chim này: tọa độ và vận tốc
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy

    def khoang_cach_den(self, chim_khac):
        """Tính khoảng cách Euclid từ con chim này tới một con chim khác."""
        dx = self.x - chim_khac.x
        dy = self.y - chim_khac.y
        return math.sqrt(dx * dx + dy * dy)

    def luat_tach_nhau(self, danh_sach_chim):
        """
        LUẬT 1 — TÁCH NHAU (Separation):
        Tránh va chạm với các con chim ở quá gần (< BAN_KINH_TRANH).
        """
        luc_x = 0.0
        luc_y = 0.0

        for chim_khac in danh_sach_chim:
            if chim_khac is self:
                continue  # Bỏ qua chính mình

            kc = self.khoang_cach_den(chim_khac)
            if 0 < kc < BAN_KINH_TRANH:
                # Vector hướng từ chim_khac đẩy ra phía mình
                luc_x = luc_x + (self.x - chim_khac.x)
                luc_y = luc_y + (self.y - chim_khac.y)

        return luc_x * HE_SO_TACH_NHAU, luc_y * HE_SO_TACH_NHAU

    def luat_dong_huong(self, danh_sach_chim):
        """
        LUẬT 2 — ĐỒNG HƯỚNG (Alignment):
        Điều chỉnh hướng bay gần giống hướng trung bình của hàng xóm trong tầm nhìn.
        """
        tong_vx = 0.0
        tong_vy = 0.0
        dem_hang_xom = 0

        for chim_khac in danh_sach_chim:
            if chim_khac is self:
                continue

            kc = self.khoang_cach_den(chim_khac)
            if kc < BAN_KINH_NHIN:
                tong_vx = tong_vx + chim_khac.vx
                tong_vy = tong_vy + chim_khac.vy
                dem_hang_xom = dem_hang_xom + 1

        if dem_hang_xom == 0:
            return 0.0, 0.0

        vx_trung_binh = tong_vx / dem_hang_xom
        vy_trung_binh = tong_vy / dem_hang_xom

        luc_x = (vx_trung_binh - self.vx) * HE_SO_DONG_HUONG
        luc_y = (vy_trung_binh - self.vy) * HE_SO_DONG_HUONG
        return luc_x, luc_y

    def luat_tu_dan(self, danh_sach_chim):
        """
        LUẬT 3 — TỤ ĐÀN (Cohesion):
        Hướng về vị trí trung tâm (tâm đàn) của nhóm hàng xóm trong tầm nhìn.
        """
        tong_x = 0.0
        tong_y = 0.0
        dem_hang_xom = 0

        for chim_khac in danh_sach_chim:
            if chim_khac is self:
                continue

            kc = self.khoang_cach_den(chim_khac)
            if kc < BAN_KINH_NHIN:
                tong_x = tong_x + chim_khac.x
                tong_y = tong_y + chim_khac.y
                dem_hang_xom = dem_hang_xom + 1

        if dem_hang_xom == 0:
            return 0.0, 0.0

        tam_x = tong_x / dem_hang_xom
        tam_y = tong_y / dem_hang_xom

        luc_x = (tam_x - self.x) * HE_SO_TU_DAN
        luc_y = (tam_y - self.y) * HE_SO_TU_DAN
        return luc_x, luc_y

    def tinh_van_toc_moi(self, danh_sach_chim):
        """
        Tổng hợp cả 3 luật Boids, lực rẽ gần biên và giới hạn tốc độ
        để tính ra vận tốc mới (vx_moi, vy_moi) cho bước tiếp theo.
        """
        tx, ty = self.luat_tach_nhau(danh_sach_chim)
        dx, dy = self.luat_dong_huong(danh_sach_chim)
        cx, cy = self.luat_tu_dan(danh_sach_chim)

        vx_moi = self.vx + tx + dx + cx
        vy_moi = self.vy + ty + dy + cy

        # Quay đầu nhẹ khi bay lại gần 4 mép khung
        if self.x < LE_BIEN:
            vx_moi = vx_moi + LUC_QUAY_DAU
        elif self.x > CHIEU_RONG - LE_BIEN:
            vx_moi = vx_moi - LUC_QUAY_DAU

        if self.y < LE_BIEN:
            vy_moi = vy_moi + LUC_QUAY_DAU
        elif self.y > CHIEU_CAO - LE_BIEN:
            vy_moi = vy_moi - LUC_QUAY_DAU

        # Giới hạn tốc độ trong khoảng [TOC_DO_TOI_THIEU, TOC_DO_TOI_DA]
        toc_do = math.sqrt(vx_moi * vx_moi + vy_moi * vy_moi)
        if toc_do == 0:
            return TOC_DO_TOI_THIEU, 0.0

        if toc_do > TOC_DO_TOI_DA:
            vx_moi = (vx_moi / toc_do) * TOC_DO_TOI_DA
            vy_moi = (vy_moi / toc_do) * TOC_DO_TOI_DA
        elif toc_do < TOC_DO_TOI_THIEU:
            vx_moi = (vx_moi / toc_do) * TOC_DO_TOI_THIEU
            vy_moi = (vy_moi / toc_do) * TOC_DO_TOI_THIEU

        return vx_moi, vy_moi

    def di_chuyen(self, vx_moi, vy_moi):
        """Áp dụng vận tốc mới và cập nhật vị trí mới của con chim."""
        self.vx = vx_moi
        self.vy = vy_moi
        self.x = self.x + self.vx
        self.y = self.y + self.vy

    def huong_don_vi(self):
        """Trả về vector hướng có độ dài 1 (dùng để vẽ mũi tên đều nhau)."""
        toc_do = math.sqrt(self.vx * self.vx + self.vy * self.vy)
        if toc_do == 0:
            return 1.0, 0.0
        return self.vx / toc_do, self.vy / toc_do


# ==============================================================================
# PHẦN 3: LỚP `DanChim` — QUẢN LÝ TOÀN BỘ ĐÀN CHIM
# ==============================================================================

class DanChim:
    """Quản lý tập hợp các đối tượng Boid và điều phối mô phỏng theo từng bước."""

    def __init__(self, so_chim=SO_CHIM, seed=SEED):
        rng = random.Random(seed)
        self.danh_sach_chim = []

        for i in range(so_chim):
            x = rng.uniform(LE_BIEN, CHIEU_RONG - LE_BIEN)
            y = rng.uniform(LE_BIEN, CHIEU_CAO - LE_BIEN)

            goc = rng.uniform(0, 2 * math.pi)
            toc_do = rng.uniform(TOC_DO_TOI_THIEU, TOC_DO_TOI_DA)
            vx = math.cos(goc) * toc_do
            vy = math.sin(goc) * toc_do

            # Tạo một đối tượng Boid hoàn chỉnh và thêm vào đàn
            chim = Boid(x, y, vx, vy)
            self.danh_sach_chim.append(chim)

    def cap_nhat(self):
        """
        Cập nhật đồng bộ toàn bộ đàn chim sau 1 bước thời gian.
        Bước 1: Mỗi con chim tính vận tốc mới dựa trên trạng thái hiện tại.
        Bước 2: Tất cả các con chim cùng di chuyển theo vận tốc mới.
        """
        van_toc_moi = []
        for chim in self.danh_sach_chim:
            vx_moi, vy_moi = chim.tinh_van_toc_moi(self.danh_sach_chim)
            van_toc_moi.append((vx_moi, vy_moi))

        for i in range(len(self.danh_sach_chim)):
            vx_moi, vy_moi = van_toc_moi[i]
            self.danh_sach_chim[i].di_chuyen(vx_moi, vy_moi)

    def tinh_do_dong_huong(self):
        """
        Đo mức độ đồng bộ hướng bay của cả đàn (Polarization), giá trị từ 0 đến 1:
          - Gần 0: cả đàn bay tán loạn nhiều hướng.
          - Gần 1: cả đàn tự tổ chức bay cùng một hướng.
        """
        tong_ux = 0.0
        tong_uy = 0.0

        for chim in self.danh_sach_chim:
            ux, uy = chim.huong_don_vi()
            tong_ux = tong_ux + ux
            tong_uy = tong_uy + uy

        so_chim = len(self.danh_sach_chim)
        return math.sqrt(tong_ux * tong_ux + tong_uy * tong_uy) / so_chim

    def lay_du_lieu_ve(self):
        """Trích xuất tọa độ và vector hướng đơn vị của tất cả chim để vẽ."""
        xs = []
        ys = []
        uxs = []
        uys = []

        for chim in self.danh_sach_chim:
            ux, uy = chim.huong_don_vi()
            xs.append(chim.x)
            ys.append(chim.y)
            uxs.append(ux)
            uys.append(uy)

        return xs, ys, uxs, uys


# ==============================================================================
# PHẦN 4: TRỰC QUAN HÓA CHUYỂN ĐỘNG BẰNG MATPLOTLIB
# ==============================================================================

def chay_mo_phong():
    """Chạy hoạt ảnh đàn chim bay tự do (phiên bản OOP)."""
    dan_chim = DanChim(so_chim=SO_CHIM, seed=SEED)

    fig, ax = plt.subplots(figsize=(7, 7))
    ax.set_xlim(0, CHIEU_RONG)
    ax.set_ylim(0, CHIEU_CAO)
    ax.set_aspect("equal")
    ax.grid(alpha=0.25)

    xs, ys, uxs, uys = dan_chim.lay_du_lieu_ve()
    # quiver vẽ mỗi con chim là một mũi tên chỉ hướng bay
    mui_ten = ax.quiver(
        xs, ys, uxs, uys,
        angles="xy", scale_units="xy", scale=0.35,
        width=0.008, headwidth=4, headlength=5,
        color="darkorange",
    )
    tieu_de = ax.set_title("Boids (OOP) — Bước 0")

    def cap_nhat_khung_hinh(buoc):
        dan_chim.cap_nhat()

        xs_moi, ys_moi, uxs_moi, uys_moi = dan_chim.lay_du_lieu_ve()
        mui_ten.set_offsets(list(zip(xs_moi, ys_moi)))
        mui_ten.set_UVC(uxs_moi, uys_moi)

        do_dong_huong = dan_chim.tinh_do_dong_huong()
        tieu_de.set_text(
            f"Boids (OOP) — Bước {buoc + 1} | Độ đồng hướng: {do_dong_huong:.2f}"
        )
        return mui_ten, tieu_de

    # Giữ biến `anim` để Python không tự hủy bộ chạy hoạt ảnh
    anim = FuncAnimation(fig, cap_nhat_khung_hinh, frames=400, interval=40, blit=False)
    plt.tight_layout()
    plt.show()
    return anim


if __name__ == "__main__":
    chay_mo_phong()
