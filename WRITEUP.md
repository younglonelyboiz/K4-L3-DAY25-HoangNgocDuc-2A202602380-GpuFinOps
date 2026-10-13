# Báo cáo Phân tích FinOps GPU — NimbusAI (Lab 25)

> **Người thực hiện:** FinOps Engineer tại NimbusAI  
> **Phạm vi đánh giá:** Dữ liệu Telemetry GPU, Danh mục giá tháng 6/2026, Nhật ký Token (2,400 requests), Workloads (8 jobs)  
> **Đầu ra đính kèm:** `outputs/report.md`, `outputs/savings.png`, `outputs/focus_export.csv`

---

## 1. Tổng quan Baseline vs. Optimized

| Chỉ số FinOps | Trước tối ưu (Baseline) | Sau tối ưu (Optimized) | Chênh lệch (Savings) | % Tiết kiệm |
|---|---|---|---|---|
| **Tổng chi phí hàng tháng** | **$27,133** | **$14,626** | **-$12,507** | **46.1%** |
| Chi phí Inference ngày | $48.87/ngày | $8.48/ngày | -$40.39/ngày | **82.6%** |
| Đơn giá **$/1M-token** | **$6.488** | **$1.126** | **-$5.362** | **82.6%** |
| Chi phí Hạ tầng Workload | $25,667/tháng | $15,627/tháng | -$10,040/tháng | **39.1%** |

* **Nhận xét chính:** Chiến lược FinOps toàn diện đã giúp NimbusAI cắt giảm gần một nửa hóa đơn điện toán đám mây tổng thể (**46.1%**), trong đó chi phí phục vụ mô hình inference trên mỗi đơn vị sản lượng token giảm vượt bậc tới **82.6%** (từ $6.488 xuống $1.126/1M-token).

---

## 2. Phân tích Chi tiết Từng Đòn bẩy Tiết kiệm

Tổng giá trị tiết kiệm **$12,507/tháng** được phân bổ qua 4 đòn bẩy:

```
[Purchasing Strategy]  ████████████████████████████████████  $10,040 (80.3%)
[Inference Levers]     █████                                 $1,212   (9.7%)
[Right-size Util-lies] ██                                    $655     (5.2%)
[Kill Idle GPUs]       ██                                    $600     (4.8%)
```

1. **Purchasing Strategy (Spot + Reserved) — Đóng góp lớn nhất ($10,040/tháng, 80.3%):**
   * *Nguyên nhân:* Khối lượng tính toán huấn luyện và fine-tuning (như `job-train-llm` chạy 8x H100) tiêu tốn lượng GPU-giờ khổng lồ. Áp dụng Spot instance (giảm 40% giá kèm cơ chế checkpoint bù đắp gián đoạn) cho các job ngắt quãng được và chuyển các job chạy 24/7 liên tục sang Reserved 3 năm (chiết khấu 45%) đã tạo ra khoản cắt giảm tiền mặt tuyệt đối lớn nhất.
2. **Inference Optimization (Cascade + Caching + Batch) ($1,212/tháng, 9.7%):**
   * Giảm sâu chi phí biên của từng request: Chuyển 80% câu hỏi đơn giản sang model nhỏ (rẻ hơn 15×), tận dụng Prompt Caching (giảm 90% phí input lặp lại) và Batch API (giảm 50% cho traffic đánh giá ban đêm).
3. **Right-sizing Util-lies ($655/tháng, 5.2%):**
   * Thay thế các GPU bị nghẽn bộ nhớ/dư thừa compute sang thế hệ phù hợp hơn.
4. **Kill Idle GPUs ($600/tháng, 4.8%):**
   * Dập tắt các instance bỏ không (điển hình là `gpu-h100-5` bị idle 8 giờ/ngày).

---

## 3. Bản chất Hiện tượng "GPU-Util Lie"

* **Phát hiện:** Hai GPU `gpu-h100-4` (H100) và `gpu-a10g-1` (A10G) bị gắn cờ "GPU-Util Lie".
  * `gpu-h100-4` có chỉ số `GPU-Util = 98.2%`, nhưng chỉ số **MFU chỉ đạt 0.194 (19.4%)** và **MBU chỉ đạt 0.207 (20.7%)**.
* **Nguyên nhân kỹ thuật:** Lệnh `nvidia-smi` chỉ đo tỷ lệ thời gian mà nhân xử lý GPU có tín hiệu xung nhịp ("clock đang bận"), chứ **không đo lường lượng phép tính FLOPs thực sự được thực hiện**. Khi một mô hình decode LLM bị nghẽn băng thông bộ nhớ (memory-bound), nhân tensor phải chờ nạp trọng số từ HBM, dẫn đến GPU-Util báo gần 100% nhưng hiệu suất tính toán thực MFU chỉ đạt chưa tới 1/5 công suất đỉnh.
* **Tác động tài chính:** Doanh nghiệp đang trả trọn gói $2.50/giờ cho H100 nhưng chỉ nhận lại công năng của một card tầm trung.
* **Giải pháp:** Hạ cấp (right-size) `gpu-h100-4` từ H100 xuống A100, tiết kiệm ngay $655/tháng mà throughput hệ thống không hề bị suy giảm.

---

## 4. Báo cáo Kết quả 2 Phần Mở rộng (Your Turn Extensions)

### Extension 3: Kinh tế học Prompt Caching (`cache_is_worth_it`)
* **Mục tiêu:** Xác định điểm hòa vốn kinh tế thực sự của Prompt Caching (đọc cache được giảm 90% nhưng phải chịu chi phí ghi/lưu trữ prefix ban đầu).
* **Kết quả đo lường:**
  * Với model nhỏ ($0.20/1M in, phí ghi $0.25): Ngưỡng hòa vốn là **1.39 lượt đọc**.
  * Với model lớn ($3.00/1M in, phí ghi $3.75): Ngưỡng hòa vốn là **1.39 lượt đọc**.
* **Đối chiếu thực tế:** Trong tập dữ liệu của NimbusAI (2,400 queries thuộc 4 nhóm dự án Chat, Doc-QA, Search, Eval), tần suất tái sử dụng system prompt trung bình đạt **~600 lượt đọc**, vượt xa ngưỡng hòa vốn 1.39 lượt.
* **Kết luận:** Prompt Caching mang lại ROI dương vượt trội và phải được bật mặc định cho toàn bộ endpoint Chat và RAG.

### Extension 5: Điều phối Lấy Carbon làm Trọng tâm (Carbon-aware Scheduling)
* **Mục tiêu:** Dời các tác vụ đào tạo và xử lý batch có thể gián đoạn (`interruptible=1`) sang vùng điện toán sạch nhất.
* **Kết quả đo lường:**
  * 5 workloads batch/training tiêu thụ tổng cộng **4,227 kWh điện/tháng**.
  * Baseline tại `us-east-1` (380 gCO2/kWh, $0.12/kWh): Phát thải **1,606.3 kg CO2e**, tiền điện $507.24/tháng.
  * Tối ưu tại `europe-north1` (30 gCO2/kWh, $0.09/kWh - thủy điện Na Uy): Phát thải chỉ **126.8 kg CO2e**, tiền điện $380.43/tháng.
  * **Mức cắt giảm:** Tiết kiệm **1,479.5 kg CO2e phát thải (giảm 92.1%)** và giảm thêm $126.81/tháng chi phí điện.
* **Đánh giá Trade-off:** Độ trễ mạng (latency) tăng thêm khi chuyển sang cụm châu Âu hoàn toàn không ảnh hưởng đến người dùng cuối (0ms user impact) do đây là các job chạy offline không đồng bộ.

---

## 5. Khuyến nghị Hành động Cho NimbusAI (FinOps Lead)

Nếu đảm nhận vai trò FinOps Lead tại NimbusAI, 3 hành động tiên quyết cần triển khai trong 30 ngày tới là:

1. **Chuẩn hóa Hợp đồng Mua sắm Điện toán Đám mây (Commitment & Spot Policy):**
   * Ký cam kết Reserved 3 năm cho 3 job inference cốt lõi (`job-infer-chat`, `job-infer-rag`, `job-infer-search`) để khóa ngay mức chiết khấu 45%.
   * Bắt buộc chuyển toàn bộ pipeline huấn luyện offline sang Spot instance kết hợp cơ chế lưu checkpoint định kỳ 30 phút.
2. **Triển khai AI Gateway với Cascade Routing & Prompt Caching Tự động:**
   * Tích hợp lớp Proxy định tuyến phân tầng: Chuyển hướng 80% query thường nhật về model nhỏ, chỉ phân luồng sang model lớn khi độ phức tạp vượt ngưỡng; tự động cache các prefix system prompt dùng chung.
3. **Chuyển dịch Giám sát từ GPU-Util sang MFU/MBU và Kích hoạt Auto-Termination:**
   * Xóa bỏ metric `GPU-Util` khỏi dashboard vận hành, thay bằng đồ thị MFU/MBU và Arithmetic Intensity (Roofline Model) trên Grafana.
   * Cài đặt Daemon tự động tắt (drain & terminate) bất kỳ instance nào rơi vào trạng thái idle quá 2 giờ, ngăn chặn triệt để lãng phí $600/tháng.

