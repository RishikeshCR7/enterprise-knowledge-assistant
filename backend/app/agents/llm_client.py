import os
import json
import logging
from typing import List, Dict, Any, Generator, Optional
from app.agents.query_rewriter import classify_intent
from app.agents.reranker import deduplicate_sources, compute_confidence_score

logger = logging.getLogger(__name__)

# Minimum confidence score threshold required to attempt grounded RAG generation
MIN_CONFIDENCE_THRESHOLD = 35

SYSTEM_PROMPT = """You are an Enterprise Knowledge Assistant. Your job is to answer employee queries using ONLY the provided company documentation snippets below.

Rules:
1. Base your answer strictly on the provided context snippets.
2. Cite sources using [Source X] notation where X is the source number.
3. If the provided context does not contain enough information, state clearly: "Based on available authorized documents, I cannot find enough information to answer this question."
4. Be professional, clear, and direct.
"""

# Keywords mapping queries to target enterprise departments
DEPT_QUERY_KEYWORDS = {
    "Engineering": ["coding", "code", "engineering", "api", "docker", "architecture", "software", "dev", "security", "token", "mfa"],
    "HR": ["hr", "leave", "vacation", "hiring", "salary", "remuneration", "pto", "payroll", "interview"],
    "Finance": ["finance", "budget", "expense", "reimbursement", "expenditure", "accounting", "cost"],
    "Legal": ["legal", "contract", "nda", "compliance", "agreement", "vendor"],
    "Sales": ["sales", "pricing", "discount", "deal", "client", "onboarding", "customer"]
}


def _detect_target_department(query: str) -> Optional[str]:
    query_lower = query.lower()
    for dept, keywords in DEPT_QUERY_KEYWORDS.items():
        if any(kw in query_lower for kw in keywords):
            return dept
    return None


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

    def generate_response(
        self,
        query: str,
        context_chunks: List[Dict[str, Any]],
        user_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generates grounded RAG response.
        If no authorized context chunks are retrieved, constructs a clear, role-aware RBAC security notification.
        """
        # 1. Greeting Handler
        if classify_intent(query) == "GREETING":
            return {
                "answer": "Hello! How can I help you today? Feel free to ask any questions regarding company policies, engineering standards, financial guidelines, or legal compliance.",
                "sources": [],
                "confidence_score": 100
            }

        # 2. Deduplicate sources & compute confidence score
        unique_sources = deduplicate_sources(context_chunks)
        confidence_score = compute_confidence_score(context_chunks)

        # 3. Role-Aware RBAC Access Refusal Handler
        if confidence_score < MIN_CONFIDENCE_THRESHOLD or not context_chunks:
            user_role_raw = (user_context.get("role") if user_context else "Employee") or "Employee"
            user_dept_raw = (user_context.get("department") if user_context else "General") or "General"
            
            user_role = str(user_role_raw.value if hasattr(user_role_raw, "value") else user_role_raw).replace("UserRole.", "").replace("Department.", "")
            user_dept = str(user_dept_raw.value if hasattr(user_dept_raw, "value") else user_dept_raw).replace("Department.", "").replace("UserRole.", "")
            target_dept = _detect_target_department(query)

            if target_dept and target_dept != user_dept and user_role != "Executive":
                # Clear RBAC Security Access Denied Notice
                rbac_denied_msg = (
                    f"🔒 **Access Restricted by Role-Based Access Control (RBAC)**\n\n"
                    f"As a **{user_role}** ({user_dept} Department), your security clearance is restricted to **{user_dept}** documentation.\n\n"
                    f"The requested query pertains to **{target_dept}** records, which require **{target_dept}** or **Executive** clearance. "
                    f"No authorized documents were retrieved for your role profile.\n\n"
                    f"💡 *To view this information, please request access from your administrator or switch to an authorized role profile (such as {target_dept} Specialist or Executive Manager).* "
                )
                return {
                    "answer": rbac_denied_msg,
                    "sources": [],
                    "confidence_score": 10
                }
            else:
                scope_desc = "Enterprise-wide" if user_role == "Executive" else f"**{user_dept}**"
                no_doc_msg = (
                    f"⚠️ **No Matching Documents Found**\n\n"
                    f"I could not find matching authorized documents in the {scope_desc} knowledge base for your query: *\"{query}\"*.\n\n"
                    f"Please try rephrasing your question or check the document library."
                )
                return {
                    "answer": no_doc_msg,
                    "sources": [],
                    "confidence_score": 15
                }

        prompt_content = self._build_prompt_payload(query, context_chunks)

        # 4. Try Groq API if key is present
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
                    return {"answer": answer, "sources": unique_sources, "confidence_score": confidence_score}
            except Exception as e:
                logger.warning(f"Groq API call failed: {str(e)}. Falling back.")

        # 5. Grounded Fallback Synthesizer if API keys are not provided
        snippets_summary = []
        for s in unique_sources:
            snippets_summary.append(f"• **{s['title']}** ({s['department']} Department - Security: {s['security_level']})")
        
        summary_list = "\n".join(snippets_summary)
        first_chunk_text = context_chunks[0].get("text", "")[:300]
        
        answer = (
            f"Based on retrieved company documentation for **{query}**:\n\n"
            f"{first_chunk_text}...\n\n"
            f"**Referenced Sources:**\n{summary_list}"
        )

        return {"answer": answer, "sources": unique_sources, "confidence_score": confidence_score}

    def generate_stream(
        self,
        query: str,
        context_chunks: List[Dict[str, Any]],
        user_context: Optional[Dict[str, Any]] = None
    ) -> Generator[str, None, None]:
        """
        Task B5: Streams response tokens for live streaming chat output.
        """
        result = self.generate_response(query, context_chunks, user_context=user_context)
        answer = result["answer"]
        
        # Stream word by word for live token rendering
        words = answer.split(" ")
        for i, word in enumerate(words):
            chunk = word if i == 0 else " " + word
            yield chunk


llm_client = LLMClient()
