# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** L3B — Truy xuất chính sách thương mại điện tử
**Thành viên có trong repo:** Đặng Thái Anh — 2A202602740
**Ngày:** 20/09/2026

> Repo hiện chỉ có thông tin và kết quả của một thành viên. Báo cáo không tự tạo tên hoặc kết quả của thành viên khác; cần bổ sung nếu nhóm thực tế có thêm người.

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Chủ đề và lý do chọn

**Chủ đề:** Chính sách đổi trả, hoàn tiền và trách nhiệm buyer/seller trên eBay.

Chủ đề có nhiều mốc thời gian và trách nhiệm khác nhau giữa người mua và người bán, phù hợp để đánh giá retrieval có metadata filter. Nguồn đều là trang trợ giúp/chính sách eBay công khai; corpus lưu bản tóm tắt tiếng Việt có provenance thay vì sao chép toàn bộ trang.

### Danh sách tài liệu

| # | Tài liệu | Nguồn | Ngày lấy / phiên bản | Ký tự nội dung | Metadata chính |
|---|---|---|---|---:|---|
| 1 | Người mua yêu cầu eBay can thiệp | `https://ocsnext.ebay.com/help/buying/returns-refunds/ask-ebay-to-step-in?id=4701` | 2026-09-20 / not-stated | 1,012 | buyer, case-escalation, vi |
| 2 | Người mua trả hàng để nhận hoàn tiền | `https://www.ebay.com/help/buyanl/returns-refunds/return-item-refund?id=4041` | 2026-09-20 / not-stated | 1,545 | buyer, return-process, vi |
| 3 | Bảo đảm hoàn tiền eBay | `https://www.ebay.com/help/policies/ebay/ebay?id=4210` | 2026-09-20 / not-stated | 1,374 | both, buyer-protection, vi |
| 4 | Người bán yêu cầu eBay can thiệp | `https://www.ebay.com/help/selling/managing-returns-refunds/ask-ebay-to-step-in?id=4702` | 2026-09-20 / not-stated | 1,265 | seller, case-escalation, vi |
| 5 | Người bán xử lý yêu cầu đổi trả | `https://ocsnext.ebay.com/help/selling/managing-returns-refunds/handling-return-requests?id=4115` | 2026-09-20 / not-stated | 1,411 | seller, return-processing, vi |
| 6 | Người bán xử lý tranh chấp thanh toán | `https://www.ebay.com/help/selling/getting-paid/handling-chargebacks?id=4799` | 2026-09-20 / not-stated | 1,256 | seller, payment-dispute, vi |
| 7 | Bảo vệ người bán trước tranh chấp thanh toán | `https://www.ebay.com/help/policies/selling-policies/payment-est-seller-protections?id=5293` | 2026-09-20 / not-stated | 1,462 | seller, seller-protection, vi |
| 8 | Người bán hoàn tiền cho người mua | `https://www.ebay.com/help/selling/managing-returns-refunds/refunding-buyers?id=5182` | 2026-09-20 / not-stated | 1,459 | seller, refunds, vi |
| 9 | Thiết lập chính sách đổi trả | `https://www.ebay.com/help/Selling/Returns_Refunds/Setting_up_your_return_policy?id=4368` | 2026-09-20 / not-stated | 1,130 | seller, return-policy, vi |
| 10 | Phí vận chuyển hoàn hàng | `https://www.ebay.com/help/Selling/Returns_Refunds/Return_shipping_for_sellers?id=4703` | 2026-09-20 / not-stated | 1,161 | seller, return-shipping, vi |

**Quản trị dữ liệu:**
- [x] 10 tài liệu công khai, không có dữ liệu cá nhân, đăng nhập hoặc nội dung nội bộ.
- [x] Mỗi file có `doc_id`, `title`, `source_url`, `retrieved_at`, `document_version`, `audience`, `category`, `language`.
- [x] `sources.csv` khớp 1-1 với 10 file Markdown.
- [x] Corpus có đủ `buyer`, `seller` và `both` để metadata filter có ý nghĩa.

### Cấu trúc Metadata

| Trường | Kiểu | Ví dụ | Tác dụng |
|---|---|---|---|
| `doc_id` | string | `seller-return-shipping` | Liên kết các chunk với tài liệu gốc và hỗ trợ xóa theo tài liệu. |
| `audience` | enum | `buyer`, `seller`, `both` | Lọc đúng chính sách theo đối tượng trước khi search. |
| `category` | string | `return-shipping` | Thu hẹp theo loại chính sách. |
| `source_url` | URL | trang Help eBay | Truy vết nguồn. |
| `retrieved_at` | date | `2026-09-20` | Ghi nhận thời điểm thu thập. |
| `document_version` | string | `not-stated` | Không bịa phiên bản khi nguồn không công bố. |

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

### Phân tích đường cơ sở

`chunk_size=500`:

| Tài liệu | Chiến lược | Số chunk | Độ dài TB | Nhận xét |
|---|---|---:|---:|---|
| buyer-ask-ebay-to-step-in | fixed_size | 3 | 337.3 | Kích thước đều nhưng có thể cắt ngang mục. |
| buyer-ask-ebay-to-step-in | by_sentences | 3 | 335.7 | Dễ đọc, ít làm đứt câu. |
| buyer-ask-ebay-to-step-in | recursive | 3 | 336.0 | Ưu tiên ranh giới đoạn. |
| seller-handle-return-request | fixed_size | 3 | 470.3 | Có nguy cơ trộn hai quy tắc. |
| seller-handle-return-request | by_sentences | 4 | 351.0 | Mạch lạc nhưng không giữ heading. |
| seller-handle-return-request | recursive | 4 | 351.2 | Giữ đoạn tốt hơn fixed-size. |
| seller-return-policy-options | fixed_size | 3 | 376.7 | Có thể cắt danh sách lựa chọn. |
| seller-return-policy-options | by_sentences | 3 | 375.0 | Nội dung dễ đọc. |
| seller-return-policy-options | recursive | 3 | 375.3 | Cân bằng kích thước/ngữ cảnh. |

### Chiến lược của thành viên

**Đặng Thái Anh — HeadingChunker + Recursive fallback**

Tài liệu chính sách đã được biên soạn theo các mục `##`, nên mỗi heading là một đơn vị nghĩa tự nhiên. `HeadingChunker` tách theo heading; section dài hơn 700 ký tự mới dùng `RecursiveChunker`, đồng thời gắn lại heading vào mảnh con để không mất ngữ cảnh.

```python
text = re.sub(r"^#\s+[^\n]+\n+", "", text.strip())
sections = re.split(r"(?=^##\s)", text, flags=re.MULTILINE)
```

### So sánh

| Chiến lược | Điểm truy xuất | Điểm mạnh | Điểm yếu |
|---|---:|---|---|
| HeadingChunker | 10 / 10 | Chunk trùng cấu trúc điều khoản, dễ trích nguồn | Phụ thuộc tài liệu có heading tốt |
| Recursive baseline | Chưa chạy đủ 5 query | Giữ đoạn tốt, dùng được cho text hỗn hợp | Không biết tên section nếu bị tách sâu |
| Sentence baseline | Chưa chạy đủ 5 query | Dễ đọc | Kích thước không đều, có thể tách heading khỏi nội dung |
| Fixed-size baseline | Chưa chạy đủ 5 query | Đơn giản, dự đoán được số chunk | Dễ cắt ngang quy tắc và mốc thời gian |

Heading chunking phù hợp nhất với corpus này vì các trang chính sách được tổ chức theo từng điều khoản. Kết quả 5/5 top-1 liên quan cho thấy tận dụng cấu trúc tài liệu hiệu quả hơn việc chỉ cắt theo số ký tự.

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (10 điểm)

| # | Query | Gold answer | Chunk chứa thông tin |
|---|---|---|---|
| 1 | Sau khi mở yêu cầu đổi trả chưa được giải quyết, buyer phải chờ bao lâu để yêu cầu eBay can thiệp? | Hơn 3 ngày làm việc; hoặc hàng hoàn đã giao hơn 2 ngày mà chưa hoàn tiền. | `buyer-ask-ebay-to-step-in` / Khi nào đủ điều kiện |
| 2 | Seller có bao nhiêu ngày để phản hồi yêu cầu đổi trả? | 3 ngày làm việc. | `seller-handle-return-request` / Thời hạn phản hồi |
| 3 | Ai trả phí gửi hàng hoàn khi hàng hỏng hoặc sai mô tả? | Người bán. | `seller-handle-return-request` và `seller-return-shipping` |
| 4 | Seller có thể chọn chính sách 30 và 60 ngày như thế nào? | Buyer-paid hoặc free returns cho 30/60 ngày. | `seller-return-policy-options` / Các lựa chọn chính sách |
| 5 | Sau khi nhận hàng hoàn, seller phải hoàn tiền trong bao lâu? | Thông thường 2 ngày làm việc. | `ebay-money-back-guarantee` / Trách nhiệm người bán |

| # | Chiến lược tốt nhất | Có chunk liên quan trong top-3? | Ghi chú |
|---|---|---|---|
| 1 | Heading + buyer filter | Có, top-1 | Score 0.584 |
| 2 | Heading + seller filter | Có, top-1 | Score 0.576 |
| 3 | Heading + seller filter | Có, top-1 | Score 0.499; hai tài liệu đều có bằng chứng |
| 4 | Heading + seller filter | Có, top-1 | Score 0.456 |
| 5 | Heading + both filter | Có, top-1 | Score 0.492 |

Metadata filter giúp rõ nhất ở câu 1–4: nó loại chính sách của đối tượng còn lại trước khi xếp hạng, tránh buyer/seller cùng dùng từ “đổi trả”, “hoàn tiền” nhưng có trách nhiệm khác nhau.

## 4. Demo & Bài học nhóm (5 điểm)

**Các insight chính:**
- Filter phải chạy trước top-k; lọc sau có thể để tài liệu sai audience chiếm hết slot.
- Chunk chỉ chứa tiêu đề từng đứng top-1 nhưng không trả lời được câu hỏi; loại chunk rỗng nghĩa đã cải thiện bằng chứng top-1.
- Một embedding lexical đơn giản vẫn đạt 5/5 khi corpus/query cùng ngôn ngữ và heading tốt, nhưng điểm paraphrase thấp cho thấy cần model ngữ nghĩa khi câu hỏi đa dạng hơn.

So sánh baseline cho thấy chất lượng không chỉ phụ thuộc kích thước chunk mà còn phụ thuộc việc ranh giới chunk có trùng với cấu trúc nghiệp vụ hay không. Nếu làm lại, nhóm sẽ giữ heading chunking nhưng thử thêm multilingual semantic embedding và nhiều câu hỏi paraphrase khó hơn.

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|---|---:|
| Lựa chọn tài liệu | 10 / 10 |
| Thiết kế chiến lược | 13 / 15 |
| Chất lượng truy xuất | 10 / 10 |
| Thuyết trình | 4 / 5 |
| **Tổng phần nhóm** | **37 / 40** |

Hai điểm thiết kế và một điểm demo được giữ lại vì repo chưa có kết quả thật của thành viên khác để so sánh ngang hàng.
