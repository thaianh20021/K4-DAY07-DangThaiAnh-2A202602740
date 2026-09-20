# Ngày 7 — Bài tập đã hoàn thành
## Nền tảng Dữ liệu: Embedding & Vector Store

**Sinh viên:** Đặng Thái Anh
**MSSV:** 2A202602740
**Ngày hoàn thành:** 20/09/2026

---

## Phần 1 — Khởi động (Cá nhân)

### Bài tập 1.1 — Cosine Similarity bằng ngôn ngữ đời thường

**Điều gì xảy ra khi hai đoạn văn bản có cosine similarity cao?**

Hai vector embedding có hướng gần giống nhau, vì vậy hai đoạn văn thường cùng chủ đề hoặc diễn đạt ý nghĩa tương tự. Giá trị gần `1` thể hiện tương đồng cao, gần `0` là ít liên quan và gần `-1` là ngược hướng.

**Ví dụ tương tự cao:**

- Câu A: “Người bán phải hoàn tiền sau khi nhận lại hàng.”
- Câu B: “Seller cần refund khi kiện hàng trả về đã được giao.”
- Hai câu khác từ vựng nhưng cùng nói về nghĩa vụ hoàn tiền của người bán.

**Ví dụ tương tự thấp:**

- Câu A: “Người mua có thể yêu cầu eBay can thiệp.”
- Câu B: “Python là một ngôn ngữ lập trình bậc cao.”
- Hai câu thuộc hai miền kiến thức hoàn toàn khác nhau.

**Tại sao ưu tiên cosine similarity hơn Euclidean distance?**

Cosine tập trung vào hướng của vector thay vì độ lớn tuyệt đối. Text dài có thể tạo vector có độ lớn khác text ngắn dù nội dung gần nhau, nên Euclidean distance dễ bị ảnh hưởng bởi độ dài trong khi cosine phù hợp hơn để so sánh ý nghĩa.

---

### Bài tập 1.2 — Bài toán tính toán Chunking

Cho tài liệu `10,000` ký tự, `chunk_size=500`, `overlap=50`:

```text
step = chunk_size - overlap
     = 500 - 50
     = 450

chunks = ceil((document_length - overlap) / step)
       = ceil((10000 - 50) / 450)
       = ceil(22.11)
       = 23
```

Kiểm tra bằng chương trình:

```powershell
python -c "from src import FixedSizeChunker; print(len(FixedSizeChunker(500, 50).chunk('a' * 10000)))"
```

Kết quả: **23 chunks**.

Khi overlap tăng lên `100`:

```text
step = 500 - 100 = 400
chunks = ceil((10000 - 100) / 400)
       = ceil(24.75)
       = 25
```

Kết quả thực tế cũng là **25 chunks**. Overlap lớn giúp thông tin nằm sát ranh giới xuất hiện ở hai chunk liên tiếp, giảm nguy cơ mất ngữ cảnh; đổi lại số chunk, dung lượng lưu trữ và chi phí embedding tăng.

---

## Phần 2 — Lập trình cốt lõi (Cá nhân)

### Danh sách hoàn thành

- [x] `Document` dataclass
- [x] `FixedSizeChunker`
- [x] `SentenceChunker`
- [x] `RecursiveChunker`
- [x] `compute_similarity`
- [x] `ChunkingStrategyComparator`
- [x] `EmbeddingStore.__init__`
- [x] `EmbeddingStore.add_documents`
- [x] `EmbeddingStore.search`
- [x] `EmbeddingStore.get_collection_size`
- [x] `EmbeddingStore.search_with_filter`
- [x] `EmbeddingStore.delete_document`
- [x] `KnowledgeBaseAgent.answer`

### Tóm tắt cách triển khai

**`SentenceChunker`:** dùng regex `(?<=[.!?])(?:[ \t]+|\n+)` để tách sau dấu kết thúc câu nhưng vẫn giữ dấu câu. Các câu được gom theo `max_sentences_per_chunk`; text rỗng trả `[]`.

**`RecursiveChunker`:** ưu tiên tách theo đoạn, dòng, câu, từ rồi ký tự. Mảnh còn dài tiếp tục được tách đệ quy; các mảnh nhỏ liền nhau được gom lại gần `chunk_size` để tránh tạo quá nhiều chunk vụn.

**`compute_similarity`:** tính dot product chia cho tích độ lớn hai vector. Nếu một vector có độ lớn bằng `0`, hàm trả `0.0` để tránh chia cho không.

**`EmbeddingStore`:** lưu record trong RAM gồm id, content, metadata và embedding. Query được embed, chấm điểm bằng dot product, sắp xếp giảm dần; metadata filter được áp dụng trước khi lấy top-k.

**`KnowledgeBaseAgent`:** truy xuất top-k, dựng context đánh số `[1]`, `[2]`, thêm nguồn và yêu cầu LLM chỉ sử dụng context. Agent trả thông báo rõ ràng nếu không có kết quả.

### Kết quả kiểm thử

```text
..........................................                               [100%]
42 passed in 0.08s
```

---

## Phần 3 — So sánh chiến lược truy xuất (Nhóm)

### Bài tập 3.0 — Chuẩn bị tài liệu

**Chủ đề:** chính sách đổi trả, hoàn tiền, tranh chấp thanh toán và bảo vệ buyer/seller trên eBay.

Corpus gồm 10 bản tóm tắt tiếng Việt từ các trang chính sách/trợ giúp công khai. Không lưu dữ liệu cá nhân, nội dung sau đăng nhập hoặc thông tin nhạy cảm.

| # | Tài liệu | Ngày lấy / phiên bản | Ký tự | Metadata chính |
|---|---|---|---:|---|
| 1 | Người mua yêu cầu eBay can thiệp | 2026-09-20 / not-stated | 1,012 | buyer, case-escalation, vi |
| 2 | Người mua trả hàng để nhận hoàn tiền | 2026-09-20 / not-stated | 1,545 | buyer, return-process, vi |
| 3 | Bảo đảm hoàn tiền eBay | 2026-09-20 / not-stated | 1,374 | both, buyer-protection, vi |
| 4 | Người bán yêu cầu eBay can thiệp | 2026-09-20 / not-stated | 1,265 | seller, case-escalation, vi |
| 5 | Người bán xử lý yêu cầu đổi trả | 2026-09-20 / not-stated | 1,411 | seller, return-processing, vi |
| 6 | Người bán xử lý tranh chấp thanh toán | 2026-09-20 / not-stated | 1,256 | seller, payment-dispute, vi |
| 7 | Bảo vệ người bán trước tranh chấp | 2026-09-20 / not-stated | 1,462 | seller, seller-protection, vi |
| 8 | Người bán hoàn tiền cho người mua | 2026-09-20 / not-stated | 1,459 | seller, refunds, vi |
| 9 | Thiết lập chính sách đổi trả | 2026-09-20 / not-stated | 1,130 | seller, return-policy, vi |
| 10 | Phí vận chuyển hoàn hàng | 2026-09-20 / not-stated | 1,161 | seller, return-shipping, vi |

URL nguồn và provenance đầy đủ nằm trong `data/ecommerce/sources.csv`.

### Metadata schema

| Trường | Kiểu | Ví dụ | Mục đích |
|---|---|---|---|
| `doc_id` | string | `seller-return-shipping` | Nhận diện tài liệu gốc, xóa toàn bộ chunk cùng tài liệu. |
| `title` | string | `Phí vận chuyển hoàn hàng` | Hiển thị và truy vết. |
| `source_url` | URL | Trang Help eBay | Kiểm chứng nguồn. |
| `retrieved_at` | date | `2026-09-20` | Theo dõi độ mới dữ liệu. |
| `document_version` | string | `not-stated` | Ghi phiên bản nếu nguồn công bố; không tự suy đoán. |
| `audience` | enum | `buyer`, `seller`, `both` | Lọc đúng đối tượng trước retrieval. |
| `category` | string | `payment-dispute` | Thu hẹp loại chính sách. |
| `language` | string | `vi` | Hỗ trợ corpus đa ngôn ngữ. |

---

### Bài tập 3.1 — Thiết kế chiến lược truy xuất

#### Đường cơ sở

Chạy `ChunkingStrategyComparator().compare(text, chunk_size=500)` trên ba tài liệu:

| Tài liệu | Chiến lược | Số chunk | Độ dài trung bình |
|---|---|---:|---:|
| buyer-ask-ebay-to-step-in | fixed_size | 3 | 337.3 |
| buyer-ask-ebay-to-step-in | by_sentences | 3 | 335.7 |
| buyer-ask-ebay-to-step-in | recursive | 3 | 336.0 |
| seller-handle-return-request | fixed_size | 3 | 470.3 |
| seller-handle-return-request | by_sentences | 4 | 351.0 |
| seller-handle-return-request | recursive | 4 | 351.2 |
| seller-return-policy-options | fixed_size | 3 | 376.7 |
| seller-return-policy-options | by_sentences | 3 | 375.0 |
| seller-return-policy-options | recursive | 3 | 375.3 |

#### Chiến lược tùy chỉnh: HeadingChunker

Tài liệu chính sách có cấu trúc theo heading `##`, nên mỗi section là một đơn vị ngữ nghĩa tự nhiên. Section dài quá `700` ký tự mới dùng `RecursiveChunker`; heading được gắn lại vào từng mảnh con để giữ ngữ cảnh.

```python
class HeadingChunker:
    def __init__(self, chunk_size: int = 700) -> None:
        self.chunk_size = chunk_size
        self.fallback = RecursiveChunker(chunk_size=chunk_size)

    def chunk(self, text: str) -> list[str]:
        text = re.sub(r"^#\s+[^\n]+\n+", "", text.strip())
        sections = [
            section.strip()
            for section in re.split(r"(?=^##\s)", text, flags=re.MULTILINE)
            if section.strip()
        ]
        chunks = []
        for section in sections:
            heading = section.splitlines()[0]
            if len(section) <= self.chunk_size:
                chunks.append(section)
                continue
            for part in self.fallback.chunk(section):
                chunks.append(part if part.startswith(heading) else f"{heading}\n\n{part}")
        return chunks
```

**So sánh:** fixed-size dễ cắt ngang điều khoản; sentence chunking giữ câu nhưng có thể tách heading khỏi nội dung; recursive giữ đoạn tốt nhưng không tận dụng cấu trúc nghiệp vụ. Heading chunking tạo **47 chunks từ 10 tài liệu** và đạt **5/5 Hit@3**, đồng thời cả 5 câu đều có bằng chứng đúng ở top-1.

---

### Bài tập 3.2 — Câu hỏi đánh giá

| # | Câu hỏi | Câu trả lời chuẩn | Chunk chứa thông tin |
|---|---|---|---|
| 1 | Sau khi mở yêu cầu đổi trả mà vấn đề chưa giải quyết, buyer phải chờ bao lâu để yêu cầu eBay can thiệp? | Hơn 3 ngày làm việc; nếu hàng hoàn đã giao hơn 2 ngày mà chưa hoàn tiền cũng có thể yêu cầu hỗ trợ. | `buyer-ask-ebay-to-step-in` — Khi nào đủ điều kiện |
| 2 | Seller có bao nhiêu ngày làm việc để phản hồi yêu cầu đổi trả? | 3 ngày làm việc. | `seller-handle-return-request` — Thời hạn phản hồi |
| 3 | Ai chịu phí vận chuyển hoàn nếu hàng hỏng hoặc không đúng mô tả? | Người bán chịu phí vận chuyển hoàn. | `seller-handle-return-request` và `seller-return-shipping` |
| 4 | Seller có thể chọn thời hạn đổi trả 30 và 60 ngày như thế nào? | Có thể chọn buyer-paid hoặc free returns cho 30/60 ngày. | `seller-return-policy-options` — Các lựa chọn chính sách |
| 5 | Sau khi nhận lại hàng hoàn, seller phải hoàn tiền trong bao lâu? | Thông thường trong 2 ngày làm việc. | `ebay-money-back-guarantee` — Trách nhiệm người bán |

Câu 1 dùng `metadata_filter={"audience": "buyer"}`; câu 2–4 dùng `seller`; câu 5 dùng `both`.

---

### Bài tập 3.3 — Dự đoán độ tương tự Cosine

Backend dùng để đo là stdlib lexical hashing embedder trong `bench.py`, vì vậy điểm phản ánh mức trùng từ/bigram tốt hơn mức hiểu từ đồng nghĩa.

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Kết luận |
|---|---|---|---|---:|---|
| 1 | Người bán phải hoàn tiền trong hai ngày. | Sau khi nhận hàng hoàn, người bán có 2 ngày làm việc để hoàn tiền. | Cao | 0.3710 | Cao nhất |
| 2 | Người mua có thể yêu cầu eBay can thiệp. | Người mua được phép nhờ eBay tham gia giải quyết. | Cao tương đối | 0.2226 | Tương đồng nhưng ít từ trùng |
| 3 | Người bán chịu phí gửi trả hàng bị hỏng. | Hàng lỗi được người bán thanh toán phí vận chuyển hoàn. | Cao tương đối | 0.3004 | Tương đồng |
| 4 | Chính sách đổi trả 30 ngày. | Python là ngôn ngữ lập trình bậc cao. | Thấp | 0.0000 | Không liên quan |
| 5 | Người mua đổi ý và đặt nhầm. | Nhãn vận chuyển cần mã tracking. | Thấp | 0.0000 | Thấp nhất đồng hạng |

Điểm bất ngờ nhất là cặp 2 chỉ đạt `0.2226` dù ý nghĩa gần nhau. Nguyên nhân là lexical hashing không hiểu tốt các cặp đồng nghĩa như “yêu cầu can thiệp” và “nhờ tham gia giải quyết”; model embedding đa ngữ thực sẽ phù hợp hơn với paraphrase.

---

### Bài tập 3.4 — Chạy đánh giá và so sánh

| # | Top-1 document/section | Score | Hit@3 | Agent trả lời đúng? |
|---|---|---:|---|---|
| 1 | `buyer-ask-ebay-to-step-in` — Khi nào đủ điều kiện | 0.584 | Có | Có |
| 2 | `seller-handle-return-request` — Thời hạn phản hồi | 0.576 | Có | Có |
| 3 | `seller-handle-return-request` — Hàng sai, hỏng hoặc không đúng mô tả | 0.499 | Có | Có |
| 4 | `seller-return-policy-options` — Các lựa chọn chính sách | 0.456 | Có | Có |
| 5 | `ebay-money-back-guarantee` — Trách nhiệm của người bán | 0.492 | Có | Có |

```text
Loaded 47 chunks from 10 documents
Retrieval score: 10/10 (5/5 Hit@3)
```

**Chiến lược tốt nhất:** heading chunking vì ranh giới chunk trùng với từng điều khoản chính sách và giữ được tên section để truy vết.

**Metadata filtering:** có ích ở câu 1–4 vì buyer và seller dùng nhiều từ giống nhau như “đổi trả”, “hoàn tiền”, “can thiệp” nhưng nghĩa vụ khác nhau. Lọc trước top-k ngăn tài liệu sai đối tượng chiếm slot kết quả.

**So sánh nhóm:** repo không có kết quả thật của thành viên khác, nên không tự tạo số liệu. Phần so sánh hiện dùng ba baseline built-in và chiến lược heading của cá nhân.

---

### Bài tập 3.5 — Phân tích lỗi

**Failure case thực tế:** trong lần chạy đầu, câu hỏi 1 trả về top-1 là chunk chỉ có tiêu đề `# Người mua yêu cầu eBay can thiệp`. Document đúng nhưng chunk không chứa câu trả lời “hơn 3 ngày làm việc”, nên agent chỉ lặp lại tiêu đề và không trả lời được câu hỏi.

**Nguyên nhân:** `HeadingChunker` tách trước mỗi `##`, khiến tiêu đề cấp 1 `#` trở thành một chunk riêng. Chunk này có nhiều từ giống query nhưng grounding quality rất thấp.

**Cải thiện:** loại heading cấp 1 đứng một mình trước khi tách section:

```python
text = re.sub(r"^#\s+[^\n]+\n+", "", text.strip())
```

Sau khi sửa, top-1 của câu 1 trở thành section `## Khi nào đủ điều kiện`, score `0.584`, và agent trả lời đúng cả mốc 3 ngày lẫn 2 ngày.

**Bài học:** retrieval không chỉ cần lấy đúng document; chunk top-k phải chứa bằng chứng đủ để trả lời. Một chunk có keyword phù hợp nhưng không có thông tin thực tế vẫn là failure về grounding.

---

## Danh sách kiểm tra nộp bài

- [x] `pytest tests/ -v` — 42/42 tests passed
- [x] Hoàn thành thư mục `src/`
- [x] Corpus có 10 tài liệu và `sources.csv` khớp 1-1
- [x] Có metadata `buyer`, `seller`, `both`
- [x] Có đúng 5 benchmark queries và gold answers
- [x] Có query dùng metadata filtering
- [x] Có custom heading chunker
- [x] Có `bench.py` và `ket_qua_benchmark.txt`
- [x] Hoàn thành `report/REPORT_NHOM.md`
- [x] Hoàn thành `report/REPORT_CANHAN.md`
- [x] Retrieval đạt 10/10, 5/5 Hit@3
