"""
MÔ PHỎNG HỆ SINH THÁI SÓI - CỪU - CỎ (WOLF - SHEEP - GRASS)
CÁCH 2: SỬ DỤNG OOP (Lập trình hướng đối tượng)

Kịch bản kinh điển (mô hình sinh thái NetLogo / Mesa):
  Trên một đồng cỏ hình lưới (RONG x CAO) có 3 thành phần tương tác:
    1. CỎ (Grass): mọc sẵn ở nhiều ô. Khi bị cừu ăn sẽ biến thành đất trống
       và cần THOI_GIAN_MOC_CO bước để mọc xanh trở lại.
    2. CỪU (Sheep): mỗi bước đi ngẫu nhiên 1 ô (tốn 1 năng lượng). Nếu ô có cỏ
       thì ăn để tăng năng lượng. Hết năng lượng sẽ chết; còn sống có thể sinh sản.
    3. SÓI (Wolf): mỗi bước đi ngẫu nhiên 1 ô (tốn 1 năng lượng). Nếu gặp cừu
       tại ô đó thì ăn thịt 1 con cừu để tăng năng lượng. Hết năng lượng sẽ chết;
       còn sống có thể sinh sản.

Cách tổ chức SỬ DỤNG OOP (Object-Oriented):
  - Tính KẾ THỪA (Inheritance):
      + Lớp cha `DongVat`: gom phần chung của cả Cừu và Sói (tọa độ x, y,
        năng lượng, trạng thái con_song, và cách di chuyển ngẫu nhiên).
      + Lớp con `Cuu(DongVat)`: chỉ cần viết phần RIÊNG là ăn cỏ & sinh cừu con.
      + Lớp con `Soi(DongVat)`: chỉ cần viết phần RIÊNG là săn cừu & sinh sói con.
  - Tính ĐÓNG GÓI (Encapsulation):
      + Lớp `DongCo`: quản lý lưới cỏ mọc lại theo thời gian.
      + Lớp `HeSinhThai`: quản lý đồng cỏ, danh sách Cừu, danh sách Sói và điều
        phối từng bước chạy (tương đương 1-1 với lớp `mesa.Model` trong Mesa).

So sánh trực tiếp với file `wolf_sheep_grass_no_oop.py` (cùng tham số, cùng seed -> cùng kết quả).
Cách chạy: python wolf_sheep_grass_oop.py
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

SEED = 42                  # Cố định số ngẫu nhiên để đối chiếu với bản không OOP


# ==============================================================================
# PHẦN 2: LỚP `DongCo` — QUẢN LÝ LƯỚI CỎ (GRASS)
# ==============================================================================

class DongCo:
    """Quản lý trạng thái cỏ mọc trên toàn bộ lưới 2D (CAO x RONG)."""

    def __init__(self, rong, cao, thoi_gian_moc, rng):
        self.rong = rong
        self.cao = cao
        self.thoi_gian_moc = thoi_gian_moc

        # Ma trận lưu số bước còn lại để cỏ mọc: 0 = đã mọc xanh, > 0 = đang mọc
        self.luoi = []
        for y in range(cao):
            hang = []
            for x in range(rong):
                if rng.random() < 0.5:
                    hang.append(0)
                else:
                    hang.append(rng.randint(1, thoi_gian_moc))
            self.luoi.append(hang)

    def moc_them_mot_buoc(self):
        """Giảm bộ đếm thời gian mọc cỏ ở mọi ô đang trống."""
        for y in range(self.cao):
            for x in range(self.rong):
                if self.luoi[y][x] > 0:
                    self.luoi[y][x] = self.luoi[y][x] - 1

    def co_san_co(self, x, y):
        """Kiểm tra tại ô (x, y) có cỏ xanh hay không."""
        return self.luoi[y][x] == 0

    def bi_an(self, x, y):
        """Đánh dấu ô (x, y) vừa bị cừu ăn và bắt đầu đếm ngược mọc lại."""
        self.luoi[y][x] = self.thoi_gian_moc

    def dem_o_co_xanh(self):
        """Đếm tổng số ô hiện đang có cỏ xanh."""
        dem = 0
        for y in range(self.cao):
            for x in range(self.rong):
                if self.luoi[y][x] == 0:
                    dem = dem + 1
        return dem

    def tao_ban_do_mau(self):
        """Trả về ma trận nhị phân (1 = cỏ xanh, 0 = đất trống) để vẽ matplotlib."""
        ban_do = []
        for y in range(self.cao):
            hang = []
            for x in range(self.rong):
                hang.append(1 if self.luoi[y][x] == 0 else 0)
            ban_do.append(hang)
        return ban_do


# ==============================================================================
# PHẦN 3: LỚP CHA `DongVat` VÀ HAI LỚP CON `Cuu`, `Soi` (KẾ THỪA)
# ==============================================================================

class DongVat:
    """Lớp cha chứa dữ liệu và hành vi dùng chung cho cả Cừu và Sói."""

    def __init__(self, x, y, nang_luong):
        self.x = x
        self.y = y
        self.nang_luong = nang_luong
        self.con_song = True

    def di_chuyen_ngau_nhien(self, rong, cao, rng):
        """Di chuyển 1 ô ngẫu nhiên (nối vòng 2 đầu) và tiêu hao 1 năng lượng."""
        dx, dy = rng.choice(CAC_HUONG_DI)
        self.x = (self.x + dx) % rong
        self.y = (self.y + dy) % cao
        self.nang_luong = self.nang_luong - 1.0


class Cuu(DongVat):
    """Lớp con Cừu: kế thừa DongVat, bổ sung hành vi ăn cỏ và sinh cừu con."""

    def hanh_dong(self, dong_co, rng):
        """
        Thực hiện 1 bước của con cừu.
        Nếu sinh sản thì trả về đối tượng `Cuu` con mới; ngược lại trả về None.
        """
        # 1. Di chuyển và tốn 1 năng lượng (dùng lại phương thức của lớp cha)
        self.di_chuyen_ngau_nhien(dong_co.rong, dong_co.cao, rng)

        # 2. Nếu ô hiện tại có cỏ xanh thì ăn để tăng năng lượng
        if dong_co.co_san_co(self.x, self.y):
            dong_co.bi_an(self.x, self.y)
            self.nang_luong = self.nang_luong + NANG_LUONG_CO

        # 3. Kiểm tra chết đói
        if self.nang_luong <= 0:
            self.con_song = False
            return None

        # 4. Kiểm tra sinh sản (chia đôi năng lượng cho con)
        if rng.random() < TY_LE_SINH_CUU:
            self.nang_luong = self.nang_luong / 2.0
            return Cuu(self.x, self.y, self.nang_luong)

        return None


class Soi(DongVat):
    """Lớp con Sói: kế thừa DongVat, bổ sung hành vi săn cừu và sinh sói con."""

    def hanh_dong(self, dong_co, danh_sach_cuu, rng):
        """
        Thực hiện 1 bước của con sói.
        Nếu sinh sản thì trả về đối tượng `Soi` con mới; ngược lại trả về None.
        """
        # 1. Di chuyển và tốn 1 năng lượng (dùng lại phương thức của lớp cha)
        self.di_chuyen_ngau_nhien(dong_co.rong, dong_co.cao, rng)

        # 2. Tìm các con cừu còn sống đang ở cùng ô với con sói này
        cuu_tai_o = []
        for cuu in danh_sach_cuu:
            if cuu.con_song and cuu.x == self.x and cuu.y == self.y:
                cuu_tai_o.append(cuu)

        # Nếu gặp cừu -> chọn ngẫu nhiên 1 con để ăn thịt
        if len(cuu_tai_o) > 0:
            nan_nhan = rng.choice(cuu_tai_o)
            nan_nhan.con_song = False
            self.nang_luong = self.nang_luong + NANG_LUONG_CUU

        # 3. Kiểm tra chết đói
        if self.nang_luong <= 0:
            self.con_song = False
            return None

        # 4. Kiểm tra sinh sản (chia đôi năng lượng cho con)
        if rng.random() < TY_LE_SINH_SOI:
            self.nang_luong = self.nang_luong / 2.0
            return Soi(self.x, self.y, self.nang_luong)

        return None


# ==============================================================================
# PHẦN 4: LỚP `HeSinhThai` — ĐIỀU PHỐI TOÀN BỘ MÔ HÌNH
# ==============================================================================

class HeSinhThai:
    """Đóng gói toàn bộ môi trường (đồng cỏ, cừu, sói) và lịch sử thống kê."""

    def __init__(self, seed=SEED):
        self.rng = random.Random(seed)
        self.buoc_hien_tai = 0

        # 1. Tạo đồng cỏ
        self.dong_co = DongCo(RONG, CAO, THOI_GIAN_MOC_CO, self.rng)

        # 2. Tạo quần thể Cừu
        self.danh_sach_cuu = []
        for i in range(SO_CUU_BAN_DAU):
            x = self.rng.randrange(RONG)
            y = self.rng.randrange(CAO)
            nang_luong = float(self.rng.randint(1, 2 * NANG_LUONG_CO))
            self.danh_sach_cuu.append(Cuu(x, y, nang_luong))

        # 3. Tạo quần thể Sói
        self.danh_sach_soi = []
        for i in range(SO_SOI_BAN_DAU):
            x = self.rng.randrange(RONG)
            y = self.rng.randrange(CAO)
            nang_luong = float(self.rng.randint(1, 2 * NANG_LUONG_CUU))
            self.danh_sach_soi.append(Soi(x, y, nang_luong))

        # 4. Lưu lịch sử biến động quần thể theo từng bước
        self.ds_buoc = [0]
        self.lich_su_cuu = [len(self.danh_sach_cuu)]
        self.lich_su_soi = [len(self.danh_sach_soi)]
        self.lich_su_co_chia4 = [self.dong_co.dem_o_co_xanh() / 4.0]

    def cap_nhat_mot_buoc(self):
        """Thực hiện 1 bước mô phỏng của toàn bộ hệ sinh thái."""
        self.buoc_hien_tai = self.buoc_hien_tai + 1

        # Giai đoạn 1: Cỏ mọc thêm 1 bước
        self.dong_co.moc_them_mot_buoc()

        # Giai đoạn 2: Tất cả Cừu hành động theo thứ tự ngẫu nhiên
        self.rng.shuffle(self.danh_sach_cuu)
        cuu_moi_sinh = []
        for cuu in self.danh_sach_cuu:
            cuu_con = cuu.hanh_dong(self.dong_co, self.rng)
            if cuu_con is not None:
                cuu_moi_sinh.append(cuu_con)

        # Giữ lại cừu còn sống và thêm cừu con mới sinh
        # (So với bản không OOP: chỉ cần lọc ĐÚNG 1 danh sách thay vì 3 danh sách!)
        cuu_con_song = []
        for cuu in self.danh_sach_cuu:
            if cuu.con_song:
                cuu_con_song.append(cuu)
        cuu_con_song.extend(cuu_moi_sinh)
        self.danh_sach_cuu = cuu_con_song

        # Giai đoạn 3: Tất cả Sói hành động theo thứ tự ngẫu nhiên
        self.rng.shuffle(self.danh_sach_soi)
        soi_moi_sinh = []
        for soi in self.danh_sach_soi:
            soi_con = soi.hanh_dong(self.dong_co, self.danh_sach_cuu, self.rng)
            if soi_con is not None:
                soi_moi_sinh.append(soi_con)

        # Loại bỏ những con cừu vừa bị sói ăn
        cuu_sau_san = []
        for cuu in self.danh_sach_cuu:
            if cuu.con_song:
                cuu_sau_san.append(cuu)
        self.danh_sach_cuu = cuu_sau_san

        # Loại bỏ sói chết đói và thêm sói con mới sinh
        soi_con_song = []
        for soi in self.danh_sach_soi:
            if soi.con_song:
                soi_con_song.append(soi)
        soi_con_song.extend(soi_moi_sinh)
        self.danh_sach_soi = soi_con_song

        # Giai đoạn 4: Ghi lại thống kê
        self.ds_buoc.append(self.buoc_hien_tai)
        self.lich_su_cuu.append(len(self.danh_sach_cuu))
        self.lich_su_soi.append(len(self.danh_sach_soi))
        self.lich_su_co_chia4.append(self.dong_co.dem_o_co_xanh() / 4.0)

    def lay_toa_do_ve(self, danh_sach_dong_vat):
        """Trích xuất danh sách tọa độ (x, y) để vẽ scatter; tránh lỗi khi danh sách rỗng."""
        if len(danh_sach_dong_vat) == 0:
            return [(-10, -10)]
        toa_do = []
        for dv in danh_sach_dong_vat:
            toa_do.append((dv.x, dv.y))
        return toa_do


# ==============================================================================
# PHẦN 5: CHẠY MÔ PHỎNG VÀ TRỰC QUAN HÓA BẰNG MATPLOTLIB
# ==============================================================================

def chay_mo_phong(so_buoc=300):
    """Chạy hoạt ảnh hệ sinh thái Sói - Cừu - Cỏ (phiên bản OOP)."""
    he_sinh_thai = HeSinhThai(seed=SEED)

    fig, (ax_ban_do, ax_do_thi) = plt.subplots(1, 2, figsize=(12, 5.5))

    # --- Khung trái: Bản đồ lưới cỏ + Cừu + Sói ---
    mau_co = ListedColormap(["#d9c3a3", "#a8e6a1"])
    hinh_co = ax_ban_do.imshow(
        he_sinh_thai.dong_co.tao_ban_do_mau(), cmap=mau_co, vmin=0, vmax=1, origin="lower"
    )
    toa_do_cuu = he_sinh_thai.lay_toa_do_ve(he_sinh_thai.danh_sach_cuu)
    toa_do_soi = he_sinh_thai.lay_toa_do_ve(he_sinh_thai.danh_sach_soi)

    ve_cuu = ax_ban_do.scatter(
        [p[0] for p in toa_do_cuu], [p[1] for p in toa_do_cuu],
        c="white", edgecolors="black", s=45, label="Cừu"
    )
    ve_soi = ax_ban_do.scatter(
        [p[0] for p in toa_do_soi], [p[1] for p in toa_do_soi],
        c="crimson", marker="^", edgecolors="black", s=65, label="Sói"
    )
    ax_ban_do.set_xlim(-0.5, RONG - 0.5)
    ax_ban_do.set_ylim(-0.5, CAO - 0.5)
    ax_ban_do.legend(loc="upper right")
    tieu_de_ban_do = ax_ban_do.set_title("Sói - Cừu - Cỏ (OOP) — Bước 0")

    # --- Khung phải: Đồ thị số lượng theo thời gian ---
    duong_cuu, = ax_do_thi.plot(
        he_sinh_thai.ds_buoc, he_sinh_thai.lich_su_cuu, color="royalblue", lw=2, label="Cừu"
    )
    duong_soi, = ax_do_thi.plot(
        he_sinh_thai.ds_buoc, he_sinh_thai.lich_su_soi, color="crimson", lw=2, label="Sói"
    )
    duong_co, = ax_do_thi.plot(
        he_sinh_thai.ds_buoc, he_sinh_thai.lich_su_co_chia4,
        color="forestgreen", lw=1.8, linestyle="--", label="Cỏ (chia 4)"
    )
    ax_do_thi.set_xlim(0, so_buoc)
    ax_do_thi.set_ylim(0, 120)
    ax_do_thi.set_xlabel("Bước thời gian")
    ax_do_thi.set_ylabel("Số lượng")
    ax_do_thi.set_title("Biến động quần thể theo thời gian")
    ax_do_thi.grid(alpha=0.3)
    ax_do_thi.legend(loc="upper right")

    def cap_nhat_khung_hinh(buoc):
        # Gọi đúng 1 phương thức của đối tượng HeSinhThai (không cần nonlocal hay 6 biến list!)
        he_sinh_thai.cap_nhat_mot_buoc()

        so_cuu = len(he_sinh_thai.danh_sach_cuu)
        so_soi = len(he_sinh_thai.danh_sach_soi)
        so_co = he_sinh_thai.dong_co.dem_o_co_xanh()

        # Cập nhật khung trái
        hinh_co.set_data(he_sinh_thai.dong_co.tao_ban_do_mau())
        ve_cuu.set_offsets(he_sinh_thai.lay_toa_do_ve(he_sinh_thai.danh_sach_cuu))
        ve_soi.set_offsets(he_sinh_thai.lay_toa_do_ve(he_sinh_thai.danh_sach_soi))
        tieu_de_ban_do.set_text(
            f"OOP — Bước {he_sinh_thai.buoc_hien_tai} | Cừu: {so_cuu}, Sói: {so_soi}, Cỏ: {so_co}"
        )

        # Cập nhật đồ thị khung phải
        duong_cuu.set_data(he_sinh_thai.ds_buoc, he_sinh_thai.lich_su_cuu)
        duong_soi.set_data(he_sinh_thai.ds_buoc, he_sinh_thai.lich_su_soi)
        duong_co.set_data(he_sinh_thai.ds_buoc, he_sinh_thai.lich_su_co_chia4)

        gia_tri_lon_nhat = max(
            max(he_sinh_thai.lich_su_cuu),
            max(he_sinh_thai.lich_su_soi),
            max(he_sinh_thai.lich_su_co_chia4),
        )
        if gia_tri_lon_nhat > ax_do_thi.get_ylim()[1] * 0.9:
            ax_do_thi.set_ylim(0, gia_tri_lon_nhat * 1.2)

        return hinh_co, ve_cuu, ve_soi, duong_cuu, duong_soi, duong_co, tieu_de_ban_do

    anim = FuncAnimation(fig, cap_nhat_khung_hinh, frames=so_buoc, interval=80, repeat=False, blit=False)
    plt.tight_layout()
    plt.show()
    return anim


if __name__ == "__main__":
    chay_mo_phong()
