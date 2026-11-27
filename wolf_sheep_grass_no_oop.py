"""
MÔ PHỎNG HỆ SINH THÁI SÓI - CỪU - CỎ (WOLF - SHEEP - GRASS)
CÁCH 1: KHÔNG SỬ DỤNG OOP (Lập trình thủ tục)

Kịch bản kinh điển (mô hình sinh thái NetLogo / Mesa):
  Trên một đồng cỏ hình lưới (RONG x CAO) có 3 thành phần tương tác:
    1. CỎ (Grass): mọc sẵn ở nhiều ô. Khi bị cừu ăn sẽ biến thành đất trống
       và cần THOI_GIAN_MOC_CO bước để mọc xanh trở lại.
    2. CỪU (Sheep): mỗi bước đi ngẫu nhiên 1 ô (tốn 1 năng lượng). Nếu ô có cỏ
       thì ăn để tăng năng lượng. Hết năng lượng sẽ chết; còn sống có thể sinh sản.
    3. SÓI (Wolf): mỗi bước đi ngẫu nhiên 1 ô (tốn 1 năng lượng). Nếu gặp cừu
       tại ô đó thì ăn thịt 1 con cừu để tăng năng lượng. Hết năng lượng sẽ chết;
       còn sống có thể sinh sản.

Cách tổ chức KHÔNG dùng OOP (Procedural):
  - Lưới cỏ lưu trong ma trận 2 chiều `luoi_co[y][x]`:
      + 0   : cỏ đã mọc xanh (cừu có thể ăn)
      + > 0 : số bước còn lại để cỏ mọc lại
  - Quần thể Cừu bị tách thành 3 danh sách song song: `cuu_x`, `cuu_y`, `cuu_nl`
  - Quần thể Sói bị tách thành 3 danh sách song song: `soi_x`, `soi_y`, `soi_nl`
  - Khi một con vật chết hoặc mới sinh, ta phải cẩn thận cập nhật ĐỒNG BỘ cả 3
    danh sách để không bị lệch chỉ số giữa vị trí và năng lượng.

So sánh trực tiếp với file `wolf_sheep_grass_oop.py` (cùng tham số, cùng seed -> cùng kết quả).
Cách chạy: python wolf_sheep_grass_no_oop.py
"""
import random
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.animation import FuncAnimation


# ==============================================================================
# PHẦN 1: CÁC THAM SỐ MÔ PHỎNG (HẰNG SỐ)
# ==============================================================================

RONG = 20                  # Chiều rộng lưới đồng cỏ (số cột)
CAO = 20                   # Chiều cao lưới đồng cỏ (số hàng)

SO_CUU_BAN_DAU = 100       # Số lượng cừu ban đầu
SO_SOI_BAN_DAU = 40        # Số lượng sói ban đầu

THOI_GIAN_MOC_CO = 20      # Số bước để cỏ mọc lại sau khi bị ăn
NANG_LUONG_CO = 5          # Năng lượng cừu nhận được khi ăn 1 ô cỏ
NANG_LUONG_CUU = 20        # Năng lượng sói nhận được khi ăn 1 con cừu

TY_LE_SINH_CUU = 0.05      # Xác suất cừu sinh sản ở mỗi bước (5%)
TY_LE_SINH_SOI = 0.04      # Xác suất sói sinh sản ở mỗi bước (4%)

# 4 hướng di chuyển kề nhau trên lưới: lên, xuống, trái, phải
CAC_HUONG_DI = [(0, -1), (0, 1), (-1, 0), (1, 0)]

SEED = 42                  # Cố định số ngẫu nhiên để đối chiếu với bản OOP


# ==============================================================================
# PHẦN 2: CÁC HÀM KHỞI TẠO DỮ LIỆU
# ==============================================================================

def khoi_tao_luoi_co(rng):
    """
    Tạo ma trận 2D kích thước CAO x RONG biểu diễn đồng cỏ.
    Ban đầu khoảng 50% số ô đã có cỏ xanh (= 0), 50% đang chờ mọc (1..THOI_GIAN_MOC_CO).
    """
    luoi_co = []
    for y in range(CAO):
        hang = []
        for x in range(RONG):
            if rng.random() < 0.5:
                hang.append(0)  # Cỏ đã mọc xanh
            else:
                hang.append(rng.randint(1, THOI_GIAN_MOC_CO))
        luoi_co.append(hang)
    return luoi_co


def khoi_tao_quan_the(so_luong, nang_luong_toi_da, rng):
    """
    Khởi tạo ngẫu nhiên vị trí và năng lượng cho một quần thể (cừu hoặc sói).
    Trả về 3 danh sách song song: danh_sach_x, danh_sach_y, danh_sach_nang_luong.
    """
    ds_x = []
    ds_y = []
    ds_nl = []

    for i in range(so_luong):
        x = rng.randrange(RONG)
        y = rng.randrange(CAO)
        nang_luong = float(rng.randint(1, nang_luong_toi_da))

        ds_x.append(x)
        ds_y.append(y)
        ds_nl.append(nang_luong)

    return ds_x, ds_y, ds_nl


# ==============================================================================
# PHẦN 3: CÁC HÀM XỬ LÝ QUY TẮC SINH THÁI TRONG 1 BƯỚC
# ==============================================================================

def di_chuyen_ngau_nhien(x, y, rng):
    """
    Di chuyển 1 bước sang ô kề ngẫu nhiên.
    Phép chia lấy dư (% RONG, % CAO) tạo bản đồ nối vòng 2 đầu:
    đi quá mép phải sẽ xuất hiện lại ở mép trái (và tương tự trên/dưới).
    """
    dx, dy = rng.choice(CAC_HUONG_DI)
    x_moi = (x + dx) % RONG
    y_moi = (y + dy) % CAO
    return x_moi, y_moi


def cap_nhat_co(luoi_co):
    """Mỗi ô đang chờ mọc (> 0) sẽ giảm thời gian đếm ngược đi 1 bước."""
    for y in range(CAO):
        for x in range(RONG):
            if luoi_co[y][x] > 0:
                luoi_co[y][x] = luoi_co[y][x] - 1


def cap_nhat_cuu(cuu_x, cuu_y, cuu_nl, luoi_co, rng):
    """
    Cập nhật toàn bộ quần thể Cừu trong 1 bước:
    di chuyển -> mất 1 năng lượng -> ăn cỏ -> kiểm tra chết -> sinh sản.
    Trả về 3 danh sách mới của quần thể Cừu sau bước này.
    """
    so_cuu = len(cuu_x)
    # Xáo trộn thứ tự duyệt để không con cừu nào luôn được ưu tiên ăn trước
    thu_tu = list(range(so_cuu))
    rng.shuffle(thu_tu)

    # Mảng đánh dấu con cừu nào còn sống sau bước này
    con_song = [True] * so_cuu

    # Danh sách tạm chứa cừu con mới sinh trong bước này
    con_x = []
    con_y = []
    con_nl = []

    for i in thu_tu:
        # 1. Di chuyển và tiêu hao 1 năng lượng
        cuu_x[i], cuu_y[i] = di_chuyen_ngau_nhien(cuu_x[i], cuu_y[i], rng)
        cuu_nl[i] = cuu_nl[i] - 1.0

        # 2. Nếu ô hiện tại có cỏ xanh (== 0), ăn cỏ để tăng năng lượng
        x = cuu_x[i]
        y = cuu_y[i]
        if luoi_co[y][x] == 0:
            luoi_co[y][x] = THOI_GIAN_MOC_CO
            cuu_nl[i] = cuu_nl[i] + NANG_LUONG_CO

        # 3. Kiểm tra chết đói
        if cuu_nl[i] <= 0:
            con_song[i] = False
            continue

        # 4. Nếu còn sống, kiểm tra sinh sản (chia đôi năng lượng cho con)
        if rng.random() < TY_LE_SINH_CUU:
            cuu_nl[i] = cuu_nl[i] / 2.0
            con_x.append(x)
            con_y.append(y)
            con_nl.append(cuu_nl[i])

    # Lọc giữ lại những con cừu còn sống (theo đúng thứ tự đã xáo trộn) + thêm cừu con
    cuu_x_moi = []
    cuu_y_moi = []
    cuu_nl_moi = []

    for i in thu_tu:
        if con_song[i]:
            cuu_x_moi.append(cuu_x[i])
            cuu_y_moi.append(cuu_y[i])
            cuu_nl_moi.append(cuu_nl[i])

    cuu_x_moi.extend(con_x)
    cuu_y_moi.extend(con_y)
    cuu_nl_moi.extend(con_nl)

    return cuu_x_moi, cuu_y_moi, cuu_nl_moi


def cap_nhat_soi(soi_x, soi_y, soi_nl, cuu_x, cuu_y, cuu_nl, rng):
    """
    Cập nhật toàn bộ quần thể Sói trong 1 bước:
    di chuyển -> mất 1 năng lượng -> săn cừu cùng ô -> kiểm tra chết -> sinh sản.
    Trả về 6 danh sách mới (3 của Sói và 3 của Cừu còn lại).
    """
    so_soi = len(soi_x)
    thu_tu = list(range(so_soi))
    rng.shuffle(thu_tu)

    soi_song = [True] * so_soi
    cuu_song = [True] * len(cuu_x)

    # Danh sách tạm chứa sói con mới sinh trong bước này
    con_x = []
    con_y = []
    con_nl = []

    for i in thu_tu:
        # 1. Di chuyển và tiêu hao 1 năng lượng
        soi_x[i], soi_y[i] = di_chuyen_ngau_nhien(soi_x[i], soi_y[i], rng)
        soi_nl[i] = soi_nl[i] - 1.0

        # 2. Tìm các con cừu còn sống đang ở cùng ô (x, y) với con sói này
        x = soi_x[i]
        y = soi_y[i]
        cuu_tai_o = []
        for idx_cuu in range(len(cuu_x)):
            if cuu_song[idx_cuu] and cuu_x[idx_cuu] == x and cuu_y[idx_cuu] == y:
                cuu_tai_o.append(idx_cuu)

        # Nếu có cừu tại ô này -> chọn ngẫu nhiên 1 con để ăn
        if len(cuu_tai_o) > 0:
            nan_nhan = rng.choice(cuu_tai_o)
            cuu_song[nan_nhan] = False
            soi_nl[i] = soi_nl[i] + NANG_LUONG_CUU

        # 3. Kiểm tra chết đói
        if soi_nl[i] <= 0:
            soi_song[i] = False
            continue

        # 4. Nếu còn sống, kiểm tra sinh sản (chia đôi năng lượng cho con)
        if rng.random() < TY_LE_SINH_SOI:
            soi_nl[i] = soi_nl[i] / 2.0
            con_x.append(x)
            con_y.append(y)
            con_nl.append(soi_nl[i])

    # Lọc lại danh sách Cừu (bỏ những con vừa bị sói ăn)
    cuu_x_moi = []
    cuu_y_moi = []
    cuu_nl_moi = []
    for idx_cuu in range(len(cuu_x)):
        if cuu_song[idx_cuu]:
            cuu_x_moi.append(cuu_x[idx_cuu])
            cuu_y_moi.append(cuu_y[idx_cuu])
            cuu_nl_moi.append(cuu_nl[idx_cuu])

    # Lọc lại danh sách Sói (bỏ sói chết đói) + thêm sói con mới sinh
    soi_x_moi = []
    soi_y_moi = []
    soi_nl_moi = []
    for i in thu_tu:
        if soi_song[i]:
            soi_x_moi.append(soi_x[i])
            soi_y_moi.append(soi_y[i])
            soi_nl_moi.append(soi_nl[i])

    soi_x_moi.extend(con_x)
    soi_y_moi.extend(con_y)
    soi_nl_moi.extend(con_nl)

    return soi_x_moi, soi_y_moi, soi_nl_moi, cuu_x_moi, cuu_y_moi, cuu_nl_moi


def dem_so_o_co_xanh(luoi_co):
    """Đếm tổng số ô trên bản đồ hiện đang có cỏ xanh (== 0)."""
    dem = 0
    for y in range(CAO):
        for x in range(RONG):
            if luoi_co[y][x] == 0:
                dem = dem + 1
    return dem


def tao_ban_do_mau_co(luoi_co):
    """Chuyển ma trận đếm ngược thành ma trận nhị phân (1 = cỏ xanh, 0 = đất trống) để vẽ."""
    ban_do = []
    for y in range(CAO):
        hang = []
        for x in range(RONG):
            hang.append(1 if luoi_co[y][x] == 0 else 0)
        ban_do.append(hang)
    return ban_do


def tao_toa_do_ve(ds_x, ds_y):
    """Chuyển 2 danh sách x, y thành cặp (x, y) cho matplotlib; tránh lỗi nếu quần thể = 0."""
    if len(ds_x) == 0:
        return [(-10, -10)]  # Điểm ẩn ngoài khung hình khi quần thể đã tuyệt chủng
    return list(zip(ds_x, ds_y))


# ==============================================================================
# PHẦN 4: CHẠY MÔ PHỎNG VÀ TRỰC QUAN HÓA BẰNG MATPLOTLIB
# ==============================================================================

def chay_mo_phong(so_buoc=300):
    """Chạy hoạt ảnh hệ sinh thái Sói - Cừu - Cỏ (phiên bản không OOP)."""
    rng = random.Random(SEED)

    # Khởi tạo các biến trạng thái rời rạc (đặc trưng của lập trình thủ tục)
    luoi_co = khoi_tao_luoi_co(rng)
    cuu_x, cuu_y, cuu_nl = khoi_tao_quan_the(SO_CUU_BAN_DAU, 2 * NANG_LUONG_CO, rng)
    soi_x, soi_y, soi_nl = khoi_tao_quan_the(SO_SOI_BAN_DAU, 2 * NANG_LUONG_CUU, rng)

    # Lưu lịch sử số lượng để vẽ đồ thị biến động quần thể
    ds_buoc = [0]
    lich_su_cuu = [len(cuu_x)]
    lich_su_soi = [len(soi_x)]
    lich_su_co_chia4 = [dem_so_o_co_xanh(luoi_co) / 4.0]

    # Tạo khung hình gồm 2 biểu đồ cạnh nhau: Trái = Bản đồ 2D, Phải = Đồ thị quần thể
    fig, (ax_ban_do, ax_do_thi) = plt.subplots(1, 2, figsize=(12, 5.5))

    # --- Khung trái: Bản đồ lưới cỏ + Cừu + Sói ---
    mau_co = ListedColormap(["#d9c3a3", "#a8e6a1"])  # 0: nâu đất, 1: xanh cỏ
    hinh_co = ax_ban_do.imshow(tao_ban_do_mau_co(luoi_co), cmap=mau_co, vmin=0, vmax=1, origin="lower")
    ve_cuu = ax_ban_do.scatter(cuu_x, cuu_y, c="white", edgecolors="black", s=45, label="Cừu")
    ve_soi = ax_ban_do.scatter(soi_x, soi_y, c="crimson", marker="^", edgecolors="black", s=65, label="Sói")
    ax_ban_do.set_xlim(-0.5, RONG - 0.5)
    ax_ban_do.set_ylim(-0.5, CAO - 0.5)
    ax_ban_do.legend(loc="upper right")
    tieu_de_ban_do = ax_ban_do.set_title("Sói - Cừu - Cỏ (Không OOP) — Bước 0")

    # --- Khung phải: Đồ thị số lượng theo thời gian ---
    duong_cuu, = ax_do_thi.plot(ds_buoc, lich_su_cuu, color="royalblue", lw=2, label="Cừu")
    duong_soi, = ax_do_thi.plot(ds_buoc, lich_su_soi, color="crimson", lw=2, label="Sói")
    duong_co, = ax_do_thi.plot(ds_buoc, lich_su_co_chia4, color="forestgreen", lw=1.8, linestyle="--", label="Cỏ (chia 4)")
    ax_do_thi.set_xlim(0, so_buoc)
    ax_do_thi.set_ylim(0, 120)
    ax_do_thi.set_xlabel("Bước thời gian")
    ax_do_thi.set_ylabel("Số lượng")
    ax_do_thi.set_title("Biến động quần thể theo thời gian")
    ax_do_thi.grid(alpha=0.3)
    ax_do_thi.legend(loc="upper right")

    def cap_nhat_khung_hinh(buoc):
        # Dùng nonlocal vì các danh sách được gán lại sau mỗi bước lọc sống/chết
        nonlocal cuu_x, cuu_y, cuu_nl, soi_x, soi_y, soi_nl

        # Chạy đúng 3 giai đoạn của 1 bước mô phỏng
        cap_nhat_co(luoi_co)
        cuu_x, cuu_y, cuu_nl = cap_nhat_cuu(cuu_x, cuu_y, cuu_nl, luoi_co, rng)
        soi_x, soi_y, soi_nl, cuu_x, cuu_y, cuu_nl = cap_nhat_soi(
            soi_x, soi_y, soi_nl, cuu_x, cuu_y, cuu_nl, rng
        )

        # Ghi nhận số lượng sau bước này
        so_cuu = len(cuu_x)
        so_soi = len(soi_x)
        so_co = dem_so_o_co_xanh(luoi_co)

        ds_buoc.append(buoc + 1)
        lich_su_cuu.append(so_cuu)
        lich_su_soi.append(so_soi)
        lich_su_co_chia4.append(so_co / 4.0)

        # Cập nhật hình vẽ khung trái
        hinh_co.set_data(tao_ban_do_mau_co(luoi_co))
        ve_cuu.set_offsets(tao_toa_do_ve(cuu_x, cuu_y))
        ve_soi.set_offsets(tao_toa_do_ve(soi_x, soi_y))
        tieu_de_ban_do.set_text(
            f"Không OOP — Bước {buoc + 1} | Cừu: {so_cuu}, Sói: {so_soi}, Cỏ: {so_co}"
        )

        # Cập nhật đồ thị khung phải
        duong_cuu.set_data(ds_buoc, lich_su_cuu)
        duong_soi.set_data(ds_buoc, lich_su_soi)
        duong_co.set_data(ds_buoc, lich_su_co_chia4)

        # Tự động nới trục tung nếu số lượng vượt khung hiện tại
        gia_tri_lon_nhat = max(max(lich_su_cuu), max(lich_su_soi), max(lich_su_co_chia4))
        if gia_tri_lon_nhat > ax_do_thi.get_ylim()[1] * 0.9:
            ax_do_thi.set_ylim(0, gia_tri_lon_nhat * 1.2)

        return hinh_co, ve_cuu, ve_soi, duong_cuu, duong_soi, duong_co, tieu_de_ban_do

    anim = FuncAnimation(fig, cap_nhat_khung_hinh, frames=so_buoc, interval=80, repeat=False, blit=False)
    plt.tight_layout()
    plt.show()
    return anim


if __name__ == "__main__":
    chay_mo_phong()
