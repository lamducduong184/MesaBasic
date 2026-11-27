"""
MÔ PHỎNG HỆ SINH THÁI SÓI - CỪU - CỎ (WOLF - SHEEP - GRASS)
CÁCH 3: SỬ DỤNG THƯ VIỆN MESA 3.x

Mục tiêu bài học:
  Thấy rõ lợi ích khi dùng thư viện mô phỏng đa tác nhân Mesa so với việc tự viết
  bằng OOP thuần (`wolf_sheep_grass_oop.py`) hay không OOP (`wolf_sheep_grass_no_oop.py`):
    1. Không cần tự viết lưới 2D hay phép chia dư nối vòng (% RONG, % CAO):
       Mesa cung cấp sẵn `mesa.space.MultiGrid(rong, cao, torus=True)`.
    2. Không cần tự quản lý, xáo trộn hay lọc danh sách sống/chết:
       Mesa quản lý sẵn trong `model.agents_by_type[Loai]` và `shuffle_do("step")`.
    3. Không cần tự tạo các list `lich_su_*` để thống kê:
       Mesa cung cấp sẵn `mesa.DataCollector` trả về bảng DataFrame để vẽ đồ thị.

Kịch bản (giống hệt 2 bản trước để dễ so sánh):
  - Lưới đồng cỏ 20x20 có nối vòng 2 đầu (torus).
  - 3 loại tác nhân đều kế thừa `mesa.Agent`: `OCo` (Cỏ), `Cuu` (Cừu), `Soi` (Sói).
  - Cừu và Sói kế thừa chung từ lớp cha `DongVat(mesa.Agent)`.

Yêu cầu: mesa>=3, matplotlib.
Cách chạy: python wolf_sheep_grass_mesa.py
"""
import mesa
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

SEED = 12                  # Cố định số ngẫu nhiên để tái lập kết quả (dao động ổn định 300 bước)


# ==============================================================================
# PHẦN 2: CÁC HÀM THỐNG KÊ CHO `DataCollector`
# (Viết hàm bình thường thay cho lambda để sinh viên dễ đọc và dễ sửa.)
# ==============================================================================

def dem_cuu(model):
    """Đếm số lượng Cừu đang còn sống trong mô hình."""
    return len(model.agents_by_type[Cuu])


def dem_soi(model):
    """Đếm số lượng Sói đang còn sống trong mô hình."""
    return len(model.agents_by_type[Soi])


def dem_co_xanh(model):
    """Đếm tổng số ô hiện đang có cỏ mọc xanh."""
    dem = 0
    for o_co in model.agents_by_type[OCo]:
        if o_co.da_moc:
            dem = dem + 1
    return dem


# ==============================================================================
# PHẦN 3: ĐỊNH NGHĨA CÁC TÁC NHÂN (AGENTS) BẰNG `mesa.Agent`
# ==============================================================================

class OCo(mesa.Agent):
    """Tác nhân đại diện cho một ô cỏ cố định trên lưới."""

    def __init__(self, model, da_moc, dem_nguoc):
        # Bắt buộc gọi super().__init__(model) trong Mesa 3.x:
        # -> Tự cấp mã unique_id và tự đăng ký vào model.agents_by_type[OCo]
        super().__init__(model)
        self.da_moc = da_moc          # True: cỏ đã mọc xanh; False: đất trống
        self.dem_nguoc = dem_nguoc    # Số bước còn lại để cỏ mọc xanh trở lại

    def bi_an(self):
        """Gọi khi có con cừu ăn cỏ tại ô này."""
        self.da_moc = False
        self.dem_nguoc = THOI_GIAN_MOC_CO

    def step(self):
        """Mỗi bước, nếu đất đang trống thì giảm thời gian chờ mọc đi 1."""
        if not self.da_moc:
            self.dem_nguoc = self.dem_nguoc - 1
            if self.dem_nguoc <= 0:
                self.da_moc = True


class DongVat(mesa.Agent):
    """
    Lớp cha cho động vật (Cừu và Sói) kế thừa `mesa.Agent`.
    Gom các thuộc tính và hành vi dùng chung: năng lượng, di chuyển, chết.
    """

    def __init__(self, model, nang_luong):
        super().__init__(model)
        self.nang_luong = nang_luong

    def di_chuyen_ngau_nhien(self):
        """Di chuyển ngẫu nhiên sang 1 trong 4 ô kề và tiêu hao 1 năng lượng."""
        # Nhờ Mesa MultiGrid, ta không cần tự viết công thức (x + dx) % RONG
        cac_o_ke = self.model.grid.get_neighborhood(
            self.pos,
            moore=False,           # False = 4 hướng (lên, xuống, trái, phải)
            include_center=False,  # Không đứng yên tại ô cũ
        )
        o_moi = self.model.random.choice(cac_o_ke)
        self.model.grid.move_agent(self, o_moi)

        # Mỗi bước di chuyển tốn 1 đơn vị năng lượng
        self.nang_luong = self.nang_luong - 1.0

    def chet(self):
        """Xóa con vật khỏi cả lưới không gian lẫn danh sách quản lý của Mesa."""
        self.model.grid.remove_agent(self)
        self.remove()


class Cuu(DongVat):
    """Tác nhân Cừu: di chuyển, ăn cỏ, chết đói hoặc sinh cừu con."""

    def step(self):
        # 1. Di chuyển sang ô kề ngẫu nhiên và mất 1 năng lượng
        self.di_chuyen_ngau_nhien()

        # 2. Xem tất cả các tác nhân đang ở cùng ô `self.pos` để tìm ô cỏ
        tac_nhan_cung_o = self.model.grid.get_cell_list_contents([self.pos])
        for tac_nhan in tac_nhan_cung_o:
            if isinstance(tac_nhan, OCo) and tac_nhan.da_moc:
                tac_nhan.bi_an()
                self.nang_luong = self.nang_luong + NANG_LUONG_CO
                break

        # 3. Kiểm tra chết đói
        if self.nang_luong <= 0:
            self.chet()
            return

        # 4. Nếu còn sống, kiểm tra sinh sản (chia đôi năng lượng cho cừu con)
        if self.model.random.random() < TY_LE_SINH_CUU:
            self.nang_luong = self.nang_luong / 2.0
            cuu_con = Cuu(self.model, self.nang_luong)
            self.model.grid.place_agent(cuu_con, self.pos)


class Soi(DongVat):
    """Tác nhân Sói: di chuyển, săn cừu cùng ô, chết đói hoặc sinh sói con."""

    def step(self):
        # 1. Di chuyển sang ô kề ngẫu nhiên và mất 1 năng lượng
        self.di_chuyen_ngau_nhien()

        # 2. Tìm tất cả các con Cừu đang ở cùng ô `self.pos`
        tac_nhan_cung_o = self.model.grid.get_cell_list_contents([self.pos])
        cuu_tai_o = []
        for tac_nhan in tac_nhan_cung_o:
            if isinstance(tac_nhan, Cuu):
                cuu_tai_o.append(tac_nhan)

        # Nếu có cừu cùng ô -> chọn ngẫu nhiên 1 con để ăn thịt
        if len(cuu_tai_o) > 0:
            nan_nhan = self.model.random.choice(cuu_tai_o)
            nan_nhan.chet()
            self.nang_luong = self.nang_luong + NANG_LUONG_CUU

        # 3. Kiểm tra chết đói
        if self.nang_luong <= 0:
            self.chet()
            return

        # 4. Nếu còn sống, kiểm tra sinh sản (chia đôi năng lượng cho sói con)
        if self.model.random.random() < TY_LE_SINH_SOI:
            self.nang_luong = self.nang_luong / 2.0
            soi_con = Soi(self.model, self.nang_luong)
            self.model.grid.place_agent(soi_con, self.pos)


# ==============================================================================
# PHẦN 4: ĐỊNH NGHĨA MÔ HÌNH `HeSinhThaiMesa` KẾ THỪA `mesa.Model`
# ==============================================================================

class HeSinhThaiMesa(mesa.Model):
    """Mô hình hệ sinh thái Sói - Cừu - Cỏ xây dựng bằng thư viện Mesa."""

    def __init__(self, rong=RONG, cao=CAO, seed=SEED):
        # Khởi tạo mô hình Mesa và cố định hạt giống ngẫu nhiên
        super().__init__(rng=seed)
        self.rong = rong
        self.cao = cao

        # Tạo lưới 2D cho phép nhiều tác nhân đứng chung 1 ô (MultiGrid)
        # torus=True: nối vòng 2 đầu bản đồ (đi qua mép phải quay lại mép trái)
        self.grid = mesa.space.MultiGrid(rong, cao, torus=True)

        # 1. Phủ tác nhân Cỏ (OCo) lên toàn bộ các ô trên lưới
        for x in range(rong):
            for y in range(cao):
                if self.random.random() < 0.5:
                    co = OCo(self, da_moc=True, dem_nguoc=0)
                else:
                    cho_moc = self.random.randint(1, THOI_GIAN_MOC_CO)
                    co = OCo(self, da_moc=False, dem_nguoc=cho_moc)
                self.grid.place_agent(co, (x, y))

        # 2. Tạo quần thể Cừu ban đầu và đặt ngẫu nhiên lên lưới
        for i in range(SO_CUU_BAN_DAU):
            x = self.random.randrange(rong)
            y = self.random.randrange(cao)
            nang_luong = float(self.random.randint(1, 2 * NANG_LUONG_CO))
            cuu = Cuu(self, nang_luong)
            self.grid.place_agent(cuu, (x, y))

        # 3. Tạo quần thể Sói ban đầu và đặt ngẫu nhiên lên lưới
        for i in range(SO_SOI_BAN_DAU):
            x = self.random.randrange(rong)
            y = self.random.randrange(cao)
            nang_luong = float(self.random.randint(1, 2 * NANG_LUONG_CUU))
            soi = Soi(self, nang_luong)
            self.grid.place_agent(soi, (x, y))

        # 4. Khai báo DataCollector để tự động ghi lại số lượng Cừu, Sói, Cỏ
        self.datacollector = mesa.DataCollector(
            model_reporters={
                "Cuu": dem_cuu,
                "Soi": dem_soi,
                "Co": dem_co_xanh,
            }
        )

        # Ghi nhận trạng thái ban đầu (bước 0) trước khi chạy mô phỏng
        self.datacollector.collect(self)

    def step(self):
        """
        Thực hiện 1 bước mô phỏng của toàn bộ hệ sinh thái.
        Nhờ Mesa, toàn bộ việc xáo trộn, gọi hành động và thu thập dữ liệu
        chỉ gọn trong 4 dòng rõ ràng!
        """
        # Giai đoạn 1: Cỏ mọc thêm 1 bước
        self.agents_by_type[OCo].do("step")

        # Giai đoạn 2: Tất cả Cừu hành động theo thứ tự ngẫu nhiên
        self.agents_by_type[Cuu].shuffle_do("step")

        # Giai đoạn 3: Tất cả Sói hành động theo thứ tự ngẫu nhiên
        self.agents_by_type[Soi].shuffle_do("step")

        # Giai đoạn 4: Ghi lại thống kê sau bước này vào DataCollector
        self.datacollector.collect(self)

    def tao_ban_do_mau_co(self):
        """Tạo ma trận 2D (1 = cỏ xanh, 0 = đất trống) để vẽ bằng imshow."""
        ban_do = [[0] * self.rong for _ in range(self.cao)]
        for o_co in self.agents_by_type[OCo]:
            x, y = o_co.pos
            ban_do[y][x] = 1 if o_co.da_moc else 0
        return ban_do

    def lay_toa_do_ve(self, loai_tac_nhan):
        """Trích xuất danh sách tọa độ (x, y) của Cừu hoặc Sói để vẽ scatter."""
        danh_sach = self.agents_by_type[loai_tac_nhan]
        if len(danh_sach) == 0:
            return [(-10, -10)]  # Điểm ẩn ngoài khung nếu loài đó đã tuyệt chủng
        toa_do = []
        for tac_nhan in danh_sach:
            toa_do.append(tac_nhan.pos)
        return toa_do


# ==============================================================================
# PHẦN 5: CHẠY MÔ PHỎNG & TRỰC QUAN HÓA BẰNG MATPLOTLIB
# ==============================================================================

def chay_mo_phong(so_buoc=300):
    """Chạy hoạt ảnh hệ sinh thái Sói - Cừu - Cỏ bằng Mesa + Matplotlib."""
    model = HeSinhThaiMesa(rong=RONG, cao=CAO, seed=SEED)

    fig, (ax_ban_do, ax_do_thi) = plt.subplots(1, 2, figsize=(12, 5.5))

    # --- Khung trái: Bản đồ lưới cỏ + Cừu + Sói ---
    mau_co = ListedColormap(["#d9c3a3", "#a8e6a1"])  # 0: nâu đất, 1: xanh cỏ
    hinh_co = ax_ban_do.imshow(
        model.tao_ban_do_mau_co(), cmap=mau_co, vmin=0, vmax=1, origin="lower"
    )

    toa_do_cuu = model.lay_toa_do_ve(Cuu)
    toa_do_soi = model.lay_toa_do_ve(Soi)
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
    tieu_de_ban_do = ax_ban_do.set_title("Sói - Cừu - Cỏ (Mesa 3.x) — Bước 0")

    # --- Khung phải: Đồ thị số lượng lấy trực tiếp từ DataCollector ---
    df = model.datacollector.get_model_vars_dataframe()
    duong_cuu, = ax_do_thi.plot(df.index, df["Cuu"], color="royalblue", lw=2, label="Cừu")
    duong_soi, = ax_do_thi.plot(df.index, df["Soi"], color="crimson", lw=2, label="Sói")
    duong_co, = ax_do_thi.plot(
        df.index, df["Co"] / 4.0,
        color="forestgreen", lw=1.8, linestyle="--", label="Cỏ (chia 4)"
    )
    ax_do_thi.set_xlim(0, so_buoc)
    ax_do_thi.set_ylim(0, 120)
    ax_do_thi.set_xlabel("Bước thời gian")
    ax_do_thi.set_ylabel("Số lượng")
    ax_do_thi.set_title("Biến động quần thể (từ Mesa DataCollector)")
    ax_do_thi.grid(alpha=0.3)
    ax_do_thi.legend(loc="upper right")

    def cap_nhat_khung_hinh(buoc):
        # Chạy 1 bước mô phỏng của mô hình Mesa
        model.step()

        # Lấy bảng dữ liệu mới nhất từ DataCollector
        df_moi = model.datacollector.get_model_vars_dataframe()
        so_cuu = df_moi["Cuu"].iloc[-1]
        so_soi = df_moi["Soi"].iloc[-1]
        so_co = df_moi["Co"].iloc[-1]

        # Cập nhật khung trái (bản đồ 2D)
        hinh_co.set_data(model.tao_ban_do_mau_co())
        ve_cuu.set_offsets(model.lay_toa_do_ve(Cuu))
        ve_soi.set_offsets(model.lay_toa_do_ve(Soi))
        tieu_de_ban_do.set_text(
            f"Mesa 3.x — Bước {buoc + 1} | Cừu: {so_cuu}, Sói: {so_soi}, Cỏ: {so_co}"
        )

        # Cập nhật khung phải (đồ thị quần thể)
        duong_cuu.set_data(df_moi.index, df_moi["Cuu"])
        duong_soi.set_data(df_moi.index, df_moi["Soi"])
        duong_co.set_data(df_moi.index, df_moi["Co"] / 4.0)

        gia_tri_lon_nhat = max(
            df_moi["Cuu"].max(),
            df_moi["Soi"].max(),
            (df_moi["Co"] / 4.0).max(),
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
