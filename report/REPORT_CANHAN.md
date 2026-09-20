# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Đặng Thái Anh
**MSSV:** 2A202602740
**Nhóm:** L3B — Truy xuất chính sách thương mại điện tử
**Ngày:** 20/09/2026

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine

Cosine similarity cao nghĩa là hai vector cùng hướng, thường biểu diễn hai đoạn văn có nội dung hoặc ý nghĩa gần nhau. Giá trị gần `1` là tương đồng cao, gần `0` là ít liên quan, và gần `-1` là ngược hướng.

**Ví dụ tương tự cao:**
- Câu A: “Người bán phải hoàn tiền sau khi nhận hàng hoàn.”
- Câu B: “Seller cần refund khi kiện hàng trả lại đã được giao.”
- Hai câu dùng từ khác nhau nhưng cùng nói về nghĩa vụ hoàn tiền của người bán.

**Ví dụ tương tự thấp:**
- Câu A: “Người mua được yêu cầu eBay can thiệp.”
- Câu B: “Python là ngôn ngữ lập trình bậc cao.”
- Hai câu thuộc hai chủ đề hoàn toàn khác nhau.

Cosine ưu tiên hướng của vector thay vì độ lớn tuyệt đối. Điều này phù hợp với text embedding vì văn bản dài có thể tạo vector lớn hơn nhưng không nhất thiết khác nghĩa; Euclidean distance dễ bị ảnh hưởng bởi độ lớn đó.

### Bài toán Chunking

Với `length=10000`, `chunk_size=500`, `overlap=50`:

```text
step = 500 - 50 = 450
chunks = ceil((10000 - 50) / 450) = ceil(22.11) = 23
```

Kiểm tra bằng `FixedSizeChunker` cũng cho kết quả **23 chunks**. Khi overlap tăng lên `100`, step giảm còn `400` và số chunk tăng thành **25**. Overlap lớn giúp thông tin nằm sát biên không bị mất ngữ cảnh, đổi lại tốn thêm lưu trữ và tính toán embedding.

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

### Các hàm chia nhỏ

**`SentenceChunker.chunk`:** Tôi dùng regex `(?<=[.!?])(?:[ \t]+|\n+)` để tách tại khoảng trắng sau dấu kết thúc câu, nhờ đó dấu câu vẫn nằm trong nội dung. Text rỗng trả `[]`; giới hạn hiện tại là chữ viết tắt như `TS.` hoặc số thập phân có thể bị hiểu nhầm là ranh giới câu.

**`RecursiveChunker.chunk` / `_split`:** Thuật toán thử separator từ lớn đến nhỏ: đoạn, dòng, câu, từ rồi ký tự. Mảnh dài tiếp tục được tách đệ quy, sau đó các mảnh nhỏ liền nhau được gom lại gần `chunk_size`; base case là text đã đủ ngắn hoặc không còn separator, khi đó dùng hard split.

### Lớp EmbeddingStore

**`add_documents` + `search`:** Mỗi `Document` được chuẩn hóa thành record gồm id, content, bản sao metadata và embedding. Search embedding câu hỏi, tính dot product với từng record, sắp xếp score giảm dần và chỉ trả top-k mà không làm lộ vector embedding.

**`search_with_filter` + `delete_document`:** Metadata được lọc trước khi similarity search để tài liệu sai audience không chiếm top-k. `delete_document` loại toàn bộ chunk có cùng `metadata['doc_id']` và trả `True` khi thực sự xóa được dữ liệu.

### Tác tử KnowledgeBaseAgent

`answer` truy xuất top-k, đánh số context `[1]`, `[2]`, kèm nguồn và yêu cầu LLM chỉ dùng thông tin được cung cấp. Agent hỗ trợ `metadata_filter`; nếu store không có kết quả thì trả thông báo rõ ràng thay vì gọi LLM với context rỗng.

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

```text
..........................................                               [100%]
42 passed in 0.09s
```

**Số lượng bài test vượt qua:** **42 / 42**

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

Điểm thực tế được tính bằng stdlib lexical hashing embedder dùng trong benchmark; đây là backend tái lập được, không phải mô hình ngữ nghĩa lớn.

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|---|---|---|---|---:|---|
| 1 | Người bán phải hoàn tiền trong hai ngày. | Sau khi nhận hàng hoàn, người bán có 2 ngày làm việc để hoàn tiền. | Cao | 0.3710 | Có |
| 2 | Người mua có thể yêu cầu eBay can thiệp. | Người mua được phép nhờ eBay tham gia giải quyết. | Cao tương đối | 0.2226 | Có |
| 3 | Người bán chịu phí gửi trả hàng bị hỏng. | Hàng lỗi được người bán thanh toán phí vận chuyển hoàn. | Cao tương đối | 0.3004 | Có |
| 4 | Chính sách đổi trả 30 ngày. | Python là ngôn ngữ lập trình bậc cao. | Thấp | 0.0000 | Có |
| 5 | Người mua đổi ý và đặt nhầm. | Nhãn vận chuyển cần mã tracking. | Thấp | 0.0000 | Có |

Kết quả bất ngờ nhất là cặp 2 có cùng nghĩa nhưng điểm chỉ `0.2226`. Điều này cho thấy lexical hashing chủ yếu nhận ra từ trùng lặp, không hiểu từ đồng nghĩa tốt như Sentence Transformers hoặc OpenAI/Gemini embeddings.

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chiến lược: `HeadingChunker(chunk_size=700)` + stdlib lexical hashing + metadata pre-filter.

| # | Câu hỏi | Top-1 chunk truy xuất được | Score | Relevant | Agent trả lời |
|---|---|---|---:|---|---|
| 1 | Sau khi mở yêu cầu đổi trả mà vấn đề chưa được giải quyết, người mua phải chờ bao nhiêu ngày trước khi yêu cầu eBay can thiệp? | `buyer-ask-ebay-to-step-in` — Khi nào đủ điều kiện | 0.584 | Có | Hơn 3 ngày; hàng hoàn đã giao hơn 2 ngày mà chưa hoàn tiền cũng đủ điều kiện. |
| 2 | Người bán có bao nhiêu ngày để phản hồi yêu cầu đổi trả? | `seller-handle-return-request` — Thời hạn phản hồi | 0.576 | Có | 3 ngày làm việc. |
| 3 | Ai chịu phí vận chuyển hoàn nếu hàng hỏng hoặc sai mô tả? | `seller-handle-return-request` — Hàng sai, hỏng hoặc không đúng mô tả | 0.499 | Có | Người bán chịu phí gửi trả. |
| 4 | Người bán có thể chọn thời hạn đổi trả 30 và 60 ngày thế nào? | `seller-return-policy-options` — Các lựa chọn chính sách | 0.456 | Có | Có lựa chọn buyer-paid hoặc free returns cho 30/60 ngày. |
| 5 | Sau khi nhận hàng hoàn, người bán phải hoàn tiền trong bao lâu? | `ebay-money-back-guarantee` — Trách nhiệm người bán | 0.492 | Có | Thông thường trong 2 ngày làm việc. |

**Số câu có chunk liên quan trong top-3:** **5 / 5**

Repo chưa có kết quả của thành viên khác để so sánh trung thực. Điều rút ra từ việc so với ba baseline là heading chunking giữ nguyên từng điều khoản, dễ truy vết nguồn hơn fixed-size và tránh sinh chunk tiêu đề không có nội dung.

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|---|---:|
| Khởi động | 5 / 5 |
| Hướng tiếp cận | 10 / 10 |
| Hoàn thiện code | 30 / 30 |
| Dự đoán độ tương tự | 5 / 5 |
| Kết quả truy xuất | 10 / 10 |
| **Tổng phần cá nhân** | **60 / 60** |
