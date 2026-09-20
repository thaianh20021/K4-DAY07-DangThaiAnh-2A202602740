from __future__ import annotations

import hashlib
import math
import re
import sys
from pathlib import Path

from src import Document, EmbeddingStore, KnowledgeBaseAgent, RecursiveChunker


DATA_DIR = Path("data/ecommerce")
BENCHMARKS = [
    {
        "query": "Sau khi mở yêu cầu đổi trả mà vấn đề chưa được giải quyết, người mua phải chờ bao nhiêu ngày làm việc trước khi yêu cầu eBay can thiệp?",
        "gold": "Hơn 3 ngày làm việc kể từ khi mở yêu cầu; hàng hoàn đã giao hơn 2 ngày mà chưa hoàn tiền cũng có thể yêu cầu hỗ trợ.",
        "expected_doc": "buyer-ask-ebay-to-step-in",
        "filter": {"audience": "buyer"},
    },
    {
        "query": "Người bán có bao nhiêu ngày làm việc để phản hồi yêu cầu đổi trả?",
        "gold": "Người bán có 3 ngày làm việc để phản hồi và giải quyết yêu cầu.",
        "expected_doc": "seller-handle-return-request",
        "filter": {"audience": "seller"},
    },
    {
        "query": "Ai chịu phí vận chuyển hoàn nếu hàng bị hỏng hoặc không đúng mô tả?",
        "gold": "Người bán chịu phí vận chuyển hoàn, kể cả khi không cung cấp đổi trả miễn phí.",
        "expected_doc": "seller-return-shipping",
        "filter": {"audience": "seller"},
    },
    {
        "query": "Người bán có thể chọn các thời hạn đổi trả 30 ngày và 60 ngày như thế nào?",
        "gold": "Có thể chọn người mua trả phí hoặc đổi trả miễn phí cho thời hạn 30 hoặc 60 ngày.",
        "expected_doc": "seller-return-policy-options",
        "filter": {"audience": "seller"},
    },
    {
        "query": "Sau khi nhận lại hàng hoàn, người bán phải hoàn tiền trong bao lâu?",
        "gold": "Thông thường trong vòng 2 ngày làm việc sau khi nhận hàng hoàn.",
        "expected_doc": "ebay-money-back-guarantee",
        "filter": {"audience": "both"},
    },
]


class HashingEmbedder:
    def __init__(self, dimensions: int = 2048) -> None:
        self.dimensions = dimensions
        self._backend_name = "stdlib lexical hashing"

    def __call__(self, text: str) -> list[float]:
        tokens = re.findall(r"\w+", text.lower(), flags=re.UNICODE)
        features = tokens + [f"{left}_{right}" for left, right in zip(tokens, tokens[1:])]
        vector = [0.0] * self.dimensions
        for feature in features:
            digest = hashlib.blake2b(feature.encode("utf-8"), digest_size=8).digest()
            vector[int.from_bytes(digest, "big") % self.dimensions] += 1.0
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]


class HeadingChunker:
    def __init__(self, chunk_size: int = 700) -> None:
        self.chunk_size = chunk_size
        self.fallback = RecursiveChunker(chunk_size=chunk_size)

    def chunk(self, text: str) -> list[str]:
        text = re.sub(r"^#\s+[^\n]+\n+", "", text.strip())
        sections = [section.strip() for section in re.split(r"(?=^##\s)", text, flags=re.MULTILINE) if section.strip()]
        chunks: list[str] = []
        for section in sections:
            heading = section.splitlines()[0] if section.startswith("## ") else ""
            if len(section) <= self.chunk_size:
                chunks.append(section)
                continue
            for part in self.fallback.chunk(section):
                chunks.append(part if not heading or part.startswith(heading) else f"{heading}\n\n{part}")
        return chunks


def parse_document(path: Path) -> tuple[dict[str, str], str]:
    raw = path.read_text(encoding="utf-8")
    _, frontmatter, content = raw.split("---", 2)
    metadata = {}
    for line in frontmatter.strip().splitlines():
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip().strip('"')
    return metadata, content.strip()


def load_chunks() -> list[Document]:
    chunker = HeadingChunker()
    documents: list[Document] = []
    for path in sorted(DATA_DIR.glob("*.md")):
        metadata, content = parse_document(path)
        for index, chunk in enumerate(chunker.chunk(content)):
            documents.append(
                Document(
                    id=f"{metadata['doc_id']}#{index}",
                    content=chunk,
                    metadata={**metadata, "source": str(path)},
                )
            )
    return documents


def extractive_llm(prompt: str) -> str:
    match = re.search(r"\[1\] Nguồn:.*?\n(.+?)(?:\n\n\[2\]|\n\nTrả lời:)", prompt, flags=re.DOTALL)
    evidence = " ".join(match.group(1).split()) if match else "Không tìm thấy bằng chứng."
    return f"Theo nguồn [1]: {evidence}"


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    documents = load_chunks()
    store = EmbeddingStore("ecommerce", embedding_fn=HashingEmbedder())
    store.add_documents(documents)
    agent = KnowledgeBaseAgent(store, extractive_llm)

    print(f"Loaded {len(documents)} chunks from {len(list(DATA_DIR.glob('*.md')))} documents")
    hits = 0
    output_lines = [f"Loaded {len(documents)} chunks"]
    for number, benchmark in enumerate(BENCHMARKS, start=1):
        results = store.search_with_filter(
            benchmark["query"], top_k=3, metadata_filter=benchmark["filter"]
        )
        retrieved_ids = [result["metadata"]["doc_id"] for result in results]
        hit = benchmark["expected_doc"] in retrieved_ids
        hits += int(hit)
        answer = agent.answer(
            benchmark["query"], top_k=3, metadata_filter=benchmark["filter"]
        )

        print(f"\nQ{number}: {benchmark['query']}")
        print(f"Gold: {benchmark['gold']}")
        for rank, result in enumerate(results, start=1):
            print(f"  {rank}. {result['metadata']['doc_id']} score={result['score']:.3f}")
        print(f"Hit@3: {'YES' if hit else 'NO'}")
        print(f"Agent: {answer[:300]}")

        output_lines.extend(
            [
                "",
                f"Q{number}: {benchmark['query']}",
                f"Gold: {benchmark['gold']}",
                *(f"{rank}. {result['metadata']['doc_id']} score={result['score']:.3f}" for rank, result in enumerate(results, start=1)),
                f"Hit@3: {'YES' if hit else 'NO'}",
                f"Agent: {answer}",
            ]
        )

    score = hits * 2
    print(f"\nRetrieval score: {score}/10 ({hits}/5 Hit@3)")
    output_lines.extend(["", f"Retrieval score: {score}/10 ({hits}/5 Hit@3)"])
    Path("ket_qua_benchmark.txt").write_text("\n".join(output_lines) + "\n", encoding="utf-8")
    return 0 if hits == len(BENCHMARKS) else 1


if __name__ == "__main__":
    raise SystemExit(main())
