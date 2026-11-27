# MesaBasic — Mô phỏng đa tác nhân (Agent-Based Modeling) với Python & Mesa 3.x

Bộ mã nguồn minh họa phục vụ giảng dạy môn **Mô phỏng hệ đa tác nhân / Hệ phi tập trung & Blockchain**, thiết kế theo lộ trình từ cơ bản đến ứng dụng:

- So sánh trực tiếp 3 cách lập trình: **Không OOP (thủ tục)** -> **OOP thuần** -> **Thư viện Mesa 3.x**.
- Làm quen đầy đủ 3 loại không gian trong Mesa: lưới rời rạc (`MultiGrid`), không gian liên tục (`ContinuousSpace`) và mạng đồ thị (`NetworkGrid`).
- Ứng dụng mô phỏng các hệ phi tập trung: phân phối token, thị trường AMM, mạng lan truyền P2P và bỏ phiếu DAO.

## Yêu cầu cài đặt

- Python 3.10+
- Các thư viện cần thiết:

```bash
pip install "mesa>=3" matplotlib numpy networkx
```

## Danh mục mã nguồn

### 1. Làm quen với Mesa 3.x
| File | Nội dung |
| :--- | :--- |
| `ex1_hello_mesa.py` | Khung tối giản nhất của Mesa 3.x (`Agent`, `Model`, `shuffle_do`). |
| `ex2_datacollector.py` | Thu thập dữ liệu theo thời gian bằng `mesa.DataCollector` (`model_reporters`, `agent_reporters`). |

### 2. Mô phỏng đàn bay tự do — Boids (Không OOP vs. OOP vs. Mesa)
| File | Cách cài đặt |
| :--- | :--- |
| `boids_no_oop.py` | Lập trình thủ tục (4 danh sách song song `xs, ys, vxs, vys`). |
| `boids_oop.py` | Lập trình hướng đối tượng (`class Boid`, `class DanChim`). |
| `boids_mesa.py` | Sử dụng **Mesa 3.x** (`ContinuousSpace`, cập nhật 2 pha, `DataCollector` vẽ đồ thị độ đồng hướng). |

### 3. Mô phỏng hệ sinh thái Sói – Cừu – Cỏ (Không OOP vs. OOP vs. Mesa)
| File | Cách cài đặt |
| :--- | :--- |
| `wolf_sheep_grass_no_oop.py` | Lập trình thủ tục (ma trận cỏ + 6 danh sách song song cho cừu và sói). |
| `wolf_sheep_grass_oop.py` | Lập trình hướng đối tượng (kế thừa `DongVat` -> `Cuu`, `Soi`; đóng gói `DongCo`, `HeSinhThai`). |
| `wolf_sheep_grass_mesa.py` | Sử dụng **Mesa 3.x** (`MultiGrid`, `agents_by_type`, `shuffle_do`, `DataCollector`). |

### 4. Mô phỏng hệ phi tập trung & Blockchain với Mesa
| File | Nội dung |
| :--- | :--- |
| `vd_mesa1_token_distribution.py` | Phân phối token ngẫu nhiên & hệ số Gini nổi lên theo thời gian. |
| `vd_mesa2_amm_market.py` | Thị trường AMM tích không đổi (`x * y = k`) với NoiseTrader và Arbitrageur. |
| `vd_mesa3_gossip_network.py` | Lan truyền khối trên mạng P2P (`NetworkGrid`: Erdős–Rényi vs. Barabási–Albert). |
| `dao_voting.py` | Mô phỏng bỏ phiếu DAO theo trọng số token & quyền lực "cá voi". |
| `dao_compare_rules.py` | So sánh 3 luật bỏ phiếu DAO: 1 người 1 phiếu, theo token và bậc hai (quadratic). |

## Cách chạy

Ví dụ chạy mô phỏng Sói – Cừu – Cỏ bằng Mesa:

```bash
python wolf_sheep_grass_mesa.py
```
