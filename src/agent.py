from typing import Callable

from .store import EmbeddingStore


class KnowledgeBaseAgent:
    """
    An agent that answers questions using a vector knowledge base.

    Retrieval-augmented generation (RAG) pattern:
        1. Retrieve top-k relevant chunks from the store.
        2. Build a prompt with the chunks as context.
        3. Call the LLM to generate an answer.
    """

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        self.store = store
        self.llm_fn = llm_fn

    def answer(self, question: str, top_k: int = 3, metadata_filter: dict | None = None) -> str:
        results = self.store.search_with_filter(question, top_k, metadata_filter)
        if not results:
            return "Không tìm thấy thông tin phù hợp trong kho kiến thức."

        context_parts = []
        for index, result in enumerate(results, start=1):
            metadata = result["metadata"]
            source = metadata.get("source_url") or metadata.get("source") or metadata.get("doc_id") or result["id"]
            context_parts.append(f"[{index}] Nguồn: {source}\n{result['content']}")

        context = "\n\n".join(context_parts)
        prompt = (
            "Bạn là trợ lý trả lời dựa trên kho kiến thức.\n"
            "Chỉ sử dụng ngữ cảnh được cung cấp. Nếu không đủ thông tin, hãy nói rõ. "
            "Khi trả lời, hãy trích dẫn nguồn bằng số như [1], [2].\n\n"
            f"Câu hỏi: {question}\n\n"
            f"Ngữ cảnh:\n{context}\n\n"
            "Trả lời:"
        )
        return self.llm_fn(prompt)
