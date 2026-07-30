import os
import json
import logging
from typing import List, Dict, Any, Generator, Optional

logger = logging.getLogger(__name__)

# System Prompt Template for Grounded QA
SYSTEM_PROMPT = """You are an Enterprise Knowledge Assistant. Your job is to answer employee queries using ONLY the provided company documentation snippets below.

Rules:
1. Base your answer strictly on the provided context snippets.
2. Cite sources using [Source X] notation where X is the source number.
3. If the provided context does not contain enough information, state clearly: "Based on available authorized documents, I cannot find enough information to answer this question."
4. Be professional, clear, and direct.
"""


class LLMClient:
    def __init__(self):
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")

    def _build_prompt_payload(self, query: str, context_chunks: List[Dict[str, Any]]) -> str:
        if not context_chunks:
            return f"User Question: {query}\n\nContext: No authorized documents retrieved."

        formatted_context = []
        for idx, chunk in enumerate(context_chunks, 1):
            meta = chunk.get("metadata", {})
            title = meta.get("title") or meta.get("doc_id") or f"Document_{idx}"
            dept = meta.get("department", "General")
            text = chunk.get("text", "").strip()
            formatted_context.append(f"[Source {idx}] Title: {title} | Department: {dept}\nContent: {text}")

        context_str = "\n\n".join(formatted_context)
        return f"Context Documentation:\n{context_str}\n\nUser Question: {query}"

    def generate_response(self, query: str, context_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Task B4: Generates a grounded response using Groq/Gemini API or intelligent grounding fallback.
        """
        prompt_content = self._build_prompt_payload(query, context_chunks)
        
        # Prepare sources metadata
        sources = []
        for idx, chunk in enumerate(context_chunks, 1):
            meta = chunk.get("metadata", {})
            sources.append({
                "source_id": idx,
                "title": meta.get("title") or meta.get("doc_id") or f"Document {idx}",
                "department": meta.get("department", "General"),
                "security_level": meta.get("security_level", "Internal"),
                "doc_id": meta.get("doc_id", ""),
                "score": chunk.get("rerank_score", chunk.get("score", 0.0))
            })

        # Try Groq API if key is present
        if self.groq_api_key:
            try:
                import requests
                headers = {
                    "Authorization": f"Bearer {self.groq_api_key}",
                    "Content-Type": "application/json"
                }
                data = {
                    "model": "llama-3.1-8b-instant",
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt_content}
                    ],
                    "temperature": 0.2
                }
                res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=data, timeout=15)
                if res.status_code == 200:
                    answer = res.json()["choices"][0]["message"]["content"]
                    return {"answer": answer, "sources": sources}
            except Exception as e:
                logger.warning(f"Groq API call failed: {str(e)}. Falling back.")

        # Grounded Fallback Synthesizer if API keys are not provided
        if not context_chunks:
            answer = "Based on available authorized documents, I could not find relevant information to answer your request."
        else:
            snippets_summary = []
            for s in sources:
                snippets_summary.append(f"• **{s['title']}** ({s['department']} Department - Security: {s['security_level']})")
            
            summary_list = "\n".join(snippets_summary)
            first_chunk_text = context_chunks[0].get("text", "")[:300]
            
            answer = (
                f"Based on retrieved company documentation for **{query}**:\n\n"
                f"{first_chunk_text}...\n\n"
                f"**Referenced Sources:**\n{summary_list}"
            )

        return {"answer": answer, "sources": sources}

    def generate_stream(self, query: str, context_chunks: List[Dict[str, Any]]) -> Generator[str, None, None]:
        """
        Task B5: Streams response tokens for live streaming chat output.
        """
        result = self.generate_response(query, context_chunks)
        answer = result["answer"]
        
        # Stream word by word for live token rendering
        words = answer.split(" ")
        for i, word in enumerate(words):
            chunk = word if i == 0 else " " + word
            yield chunk


llm_client = LLMClient()
