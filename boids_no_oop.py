"""
MÔ PHỎNG ĐÀN BAY TỰ DO (BOIDS) — CÁCH 1: KHÔNG SỬ DỤNG OOP (Lập trình thủ tục)

Kịch bản (Craig Reynolds, 1987):
  Không có "chim đầu đàn" chỉ huy. Mỗi con chim chỉ quan sát các con chim ở gần
  và tuân theo đúng 3 quy tắc cục bộ đơn giản:
    1. Tách nhau (Separation): tránh bay quá sát hàng xóm để không va chạm.
    2. Đồng hướng (Alignment): chỉnh hướng bay giống hướng trung bình của hàng xóm.
    3. Tụ đàn (Cohesion)     : bay hướng về vị trí trung tâm của nhóm hàng xóm.

Cách tổ chức KHÔNG dùng OOP (Procedural):
  - Trạng thái của cả đàn được tách ra lưu trong 4 danh sách song song:
      xs[i], ys[i]   : tọa độ (x, y) của con chim thứ i
      vxs[i], vys[i] : vận tốc (vx, vy) của con chim thứ i
  - Các hàm xử lý tách rời khỏi dữ liệu, mỗi lần gọi phải truyền các danh sách
    (xs, ys, vxs, vys) và chỉ số i vào hàm.

So sánh trực tiếp với file `boids_oop.py` (cùng tham số, cùng seed -> cùng kết quả).
Cách chạy: python boids_no_oop.py
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

SEED = 42               # Cố định số ngẫu nhiên để đối chiếu với bản OOP


# ==============================================================================
# PHẦN 2: CÁC HÀM TOÁN HỌC & KHỞI TẠO DỮ LIỆU
# ==============================================================================

def tinh_khoang_cach(x1, y1, x2, y2):
    """Tính khoảng cách Euclid giữa hai điểm (x1, y1) và (x2, y2)."""
    dx = x1 - x2
    dy = y1 - y2
    return math.sqrt(dx * dx + dy * dy)


def khoi_tao_dan_chim(so_chim, seed=SEED):
    """
    Tạo vị trí và vận tốc ngẫu nhiên ban đầu cho cả đàn.
    Trả về 4 danh sách song song: xs, ys, vxs, vys.
    """
    rng = random.Random(seed)

    xs = []
    ys = []
    vxs = []
    vys = []

    for i in range(so_chim):
        # Đặt chim ngẫu nhiên bên trong vùng an toàn (tránh sát mép ngay lúc đầu)
        x = rng.uniform(LE_BIEN, CHIEU_RONG - LE_BIEN)
        y = rng.uniform(LE_BIEN, CHIEU_CAO - LE_BIEN)

        # Chọn hướng bay ngẫu nhiên (góc từ 0 đến 2*pi) và tốc độ ngẫu nhiên
        goc = rng.uniform(0, 2 * math.pi)
        toc_do = rng.uniform(TOC_DO_TOI_THIEU, TOC_DO_TOI_DA)
        vx = math.cos(goc) * toc_do
        vy = math.sin(goc) * toc_do

        xs.append(x)
        ys.append(y)
        vxs.append(vx)
        vys.append(vy)

    return xs, ys, vxs, vys


# ==============================================================================
# PHẦN 3: 3 QUY TẮC BOIDS + XỬ LÝ BIÊN & GIỚI HẠN TỐC ĐỘ
# ==============================================================================

def luat_tach_nhau(i, xs, ys):
    """
    LUẬT 1 — TÁCH NHAU (Separation):
    Nếu có con chim khác ở quá gần (< BAN_KINH_TRANH), tạo lực đẩy ngược chiều
    để tránh va chạm.
    """
    luc_x = 0.0
    luc_y = 0.0
    so_chim = len(xs)

    for j in range(so_chim):
        if j == i:
            continue  # Không tự so sánh với chính mình

        kc = tinh_khoang_cach(xs[i], ys[i], xs[j], ys[j])
        if 0 < kc < BAN_KINH_TRANH:
            # Vector hướng từ chim j ra xa phía chim i
            luc_x = luc_x + (xs[i] - xs[j])
            luc_y = luc_y + (ys[i] - ys[j])

    return luc_x * HE_SO_TACH_NHAU, luc_y * HE_SO_TACH_NHAU


def luat_dong_huong(i, xs, ys, vxs, vys):
    """
    LUẬT 2 — ĐỒNG HƯỚNG (Alignment):
    Tính vận tốc trung bình của các hàng xóm trong tầm nhìn (< BAN_KINH_NHIN),
    sau đó lái vận tốc của chim i dần về vận tốc trung bình đó.
    """
    tong_vx = 0.0
    tong_vy = 0.0
    dem_hang_xom = 0
    so_chim = len(xs)

    for j in range(so_chim):
        if j == i:
            continue

        kc = tinh_khoang_cach(xs[i], ys[i], xs[j], ys[j])
        if kc < BAN_KINH_NHIN:
            tong_vx = tong_vx + vxs[j]
            tong_vy = tong_vy + vys[j]
            dem_hang_xom = dem_hang_xom + 1

    if dem_hang_xom == 0:
        return 0.0, 0.0

    vx_trung_binh = tong_vx / dem_hang_xom
    vy_trung_binh = tong_vy / dem_hang_xom

    luc_x = (vx_trung_binh - vxs[i]) * HE_SO_DONG_HUONG
    luc_y = (vy_trung_binh - vys[i]) * HE_SO_DONG_HUONG
    return luc_x, luc_y


def luat_tu_dan(i, xs, ys):
    """
    LUẬT 3 — TỤ ĐÀN (Cohesion):
    Tính vị trí trung tâm (tâm đàn) của các hàng xóm trong tầm nhìn,
    sau đó kéo chim i bay hướng về vị trí trung tâm đó.
    """
    tong_x = 0.0
    tong_y = 0.0
    dem_hang_xom = 0
    so_chim = len(xs)

    for j in range(so_chim):
        if j == i:
            continue

        kc = tinh_khoang_cach(xs[i], ys[i], xs[j], ys[j])
        if kc < BAN_KINH_NHIN:
            tong_x = tong_x + xs[j]
            tong_y = tong_y + ys[j]
            dem_hang_xom = dem_hang_xom + 1

    if dem_hang_xom == 0:
        return 0.0, 0.0

    tam_x = tong_x / dem_hang_xom
    tam_y = tong_y / dem_hang_xom

    luc_x = (tam_x - xs[i]) * HE_SO_TU_DAN
    luc_y = (tam_y - ys[i]) * HE_SO_TU_DAN
    return luc_x, luc_y


def giu_trong_khung(x, y, vx, vy):
    """Khi chim bay gần 4 mép khung, tác động lực nhẹ để chim vòng lại."""
    if x < LE_BIEN:
        vx = vx + LUC_QUAY_DAU
    elif x > CHIEU_RONG - LE_BIEN:
        vx = vx - LUC_QUAY_DAU

    if y < LE_BIEN:
        vy = vy + LUC_QUAY_DAU
    elif y > CHIEU_CAO - LE_BIEN:
        vy = vy - LUC_QUAY_DAU

    return vx, vy


def gioi_han_toc_do(vx, vy):
    """Giữ tốc độ bay luôn nằm trong khoảng [TOC_DO_TOI_THIEU, TOC_DO_TOI_DA]."""
    toc_do = math.sqrt(vx * vx + vy * vy)
    if toc_do == 0:
        return TOC_DO_TOI_THIEU, 0.0

    if toc_do > TOC_DO_TOI_DA:
        vx = (vx / toc_do) * TOC_DO_TOI_DA
        vy = (vy / toc_do) * TOC_DO_TOI_DA
    elif toc_do < TOC_DO_TOI_THIEU:
        vx = (vx / toc_do) * TOC_DO_TOI_THIEU
        vy = (vy / toc_do) * TOC_DO_TOI_THIEU

    return vx, vy


# ==============================================================================
# PHẦN 4: CẬP NHẬT MỘT BƯỚC MÔ PHỎNG & ĐO ĐỘ ĐỒNG HƯỚNG
# ==============================================================================

def cap_nhat_dan_chim(xs, ys, vxs, vys):
    """
    Cập nhật đồng bộ toàn bộ đàn chim sau 1 bước thời gian.
    (Tính vận tốc mới cho TẤT CẢ chim trước, sau đó mới cập nhật vị trí
    để kết quả không bị phụ thuộc vào thứ tự duyệt chim.)
    """
    so_chim = len(xs)
    vxs_moi = []
    vys_moi = []

    # Bước 1: Tính vận tốc mới cho từng con chim dựa trên trạng thái hiện tại
    for i in range(so_chim):
        tx, ty = luat_tach_nhau(i, xs, ys)
        dx, dy = luat_dong_huong(i, xs, ys, vxs, vys)
        cx, cy = luat_tu_dan(i, xs, ys)

        vx_moi = vxs[i] + tx + dx + cx
        vy_moi = vys[i] + ty + dy + cy

        vx_moi, vy_moi = giu_trong_khung(xs[i], ys[i], vx_moi, vy_moi)
        vx_moi, vy_moi = gioi_han_toc_do(vx_moi, vy_moi)

        vxs_moi.append(vx_moi)
        vys_moi.append(vy_moi)

    # Bước 2: Áp dụng đồng loạt vận tốc mới và cập nhật tọa độ mới
    for i in range(so_chim):
        vxs[i] = vxs_moi[i]
        vys[i] = vys_moi[i]
        xs[i] = xs[i] + vxs[i]
        ys[i] = ys[i] + vys[i]


def tinh_do_dong_huong(vxs, vys):
    """
    Đo mức độ đồng bộ hướng bay của cả đàn (Polarization), giá trị từ 0 đến 1:
      - Gần 0: cả đàn bay tán loạn nhiều hướng.
      - Gần 1: cả đàn tự tổ chức bay cùng một hướng.
    """
    tong_ux = 0.0
    tong_uy = 0.0
    so_chim = len(vxs)

    for i in range(so_chim):
        toc_do = math.sqrt(vxs[i] * vxs[i] + vys[i] * vys[i])
        if toc_do > 0:
            tong_ux = tong_ux + (vxs[i] / toc_do)
            tong_uy = tong_uy + (vys[i] / toc_do)

    return math.sqrt(tong_ux * tong_ux + tong_uy * tong_uy) / so_chim


def tinh_vector_don_vi(vxs, vys):
    """Chuẩn hóa vector vận tốc về độ dài 1 để vẽ các mũi tên đều nhau."""
    uxs = []
    uys = []
    for i in range(len(vxs)):
        toc_do = math.sqrt(vxs[i] * vxs[i] + vys[i] * vys[i])
        if toc_do > 0:
            uxs.append(vxs[i] / toc_do)
            uys.append(vys[i] / toc_do)
        else:
            uxs.append(1.0)
            uys.append(0.0)
    return uxs, uys


# ==============================================================================
# PHẦN 5: TRỰC QUAN HÓA CHUYỂN ĐỘNG BẰNG MATPLOTLIB
# ==============================================================================

def chay_mo_phong():
    """Chạy hoạt ảnh đàn chim bay tự do (phiên bản không OOP)."""
    xs, ys, vxs, vys = khoi_tao_dan_chim(SO_CHIM, seed=SEED)

    fig, ax = plt.subplots(figsize=(7, 7))
    ax.set_xlim(0, CHIEU_RONG)
    ax.set_ylim(0, CHIEU_CAO)
    ax.set_aspect("equal")
    ax.grid(alpha=0.25)

    uxs, uys = tinh_vector_don_vi(vxs, vys)
    # quiver vẽ mỗi con chim là một mũi tên chỉ hướng bay
    mui_ten = ax.quiver(
        xs, ys, uxs, uys,
        angles="xy", scale_units="xy", scale=0.35,
        width=0.008, headwidth=4, headlength=5,
        color="royalblue",
    )
    tieu_de = ax.set_title("Boids (Không OOP) — Bước 0")

    def cap_nhat_khung_hinh(buoc):
        cap_nhat_dan_chim(xs, ys, vxs, vys)

        # Cập nhật vị trí mới và hướng mũi tên mới lên hình vẽ
        toa_do_moi = list(zip(xs, ys))
        uxs_moi, uys_moi = tinh_vector_don_vi(vxs, vys)
        mui_ten.set_offsets(toa_do_moi)
        mui_ten.set_UVC(uxs_moi, uys_moi)

        do_dong_huong = tinh_do_dong_huong(vxs, vys)
        tieu_de.set_text(
            f"Boids (Không OOP) — Bước {buoc + 1} | Độ đồng hướng: {do_dong_huong:.2f}"
        )
        return mui_ten, tieu_de

    # Giữ biến `anim` để Python không tự hủy bộ chạy hoạt ảnh
    anim = FuncAnimation(fig, cap_nhat_khung_hinh, frames=400, interval=40, blit=False)
    plt.tight_layout()
    plt.show()
    return anim


if __name__ == "__main__":
    chay_mo_phong()
