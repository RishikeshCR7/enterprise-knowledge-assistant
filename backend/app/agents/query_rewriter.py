import logging
from typing import Dict, Any, Optional
from app.rbac.roles import UserContext, UserRole, Department

logger = logging.getLogger(__name__)

# Enterprise Domain Query Expansion Rules
DOMAIN_KEYWORD_EXPANSIONS = {
    "vacation": "official HR leave policy vacation entitlement and holiday request guidelines",
    "leave": "HR leave policy paid time off parental leave and sick absence policy",
    "salary": "HR compensation policy salary structure payroll and remuneration guidelines",
    "hiring": "HR recruitment process interview procedures and hiring policy",
    "coding": "Engineering software coding standards best practices and style guide",
    "api": "Engineering API design guidelines REST specifications and endpoints documentation",
    "docker": "Engineering Docker containerization deployment and infrastructure guide",
    "expense": "Finance corporate expense policy travel reimbursement and claim limits",
    "budget": "Finance quarterly budget financial planning and department expenditure report",
    "nda": "Legal non-disclosure agreement vendor contract terms and compliance policy",
    "pricing": "Sales product pricing strategy client discount matrix and deal structure",
}


def rewrite_query(raw_query: str, user_context: Optional[Dict[str, Any]] = None) -> str:
    """
    Task B1: Rewrites raw user questions into optimized enterprise search queries.
    Transforms raw inputs like 'Vacation policy?' into clear, domain-expanded queries.
    Incorporates user role/department context when available.
    """
    if not raw_query or not raw_query.strip():
        return "general enterprise documentation"

    query_lower = raw_query.strip().lower()
    expanded_terms = []

    # 1. Match domain keywords and apply contextual expansions
    for keyword, expansion in DOMAIN_KEYWORD_EXPANSIONS.items():
        if keyword in query_lower:
            expanded_terms.append(expansion)

    # 2. Extract department or role context if provided
    context_prefix = ""
    if user_context:
        dept = user_context.get("department")
        role = user_context.get("role")
        if dept:
            context_prefix = f"[{dept} Department] "
        elif role:
            context_prefix = f"[{role} Role] "

    # 3. Combine original query with domain expansion terms
    if expanded_terms:
        combined_expansion = " ".join(expanded_terms)
        rewritten = f"{context_prefix}{raw_query.strip()} — Search focus: {combined_expansion}"
    else:
        # Generic enhancement for short queries (< 4 words)
        words = raw_query.strip().split()
        if len(words) <= 3:
            rewritten = f"{context_prefix}Retrieve official guidelines and documentation regarding: {raw_query.strip()}"
        else:
            rewritten = f"{context_prefix}{raw_query.strip()}"

    logger.info(f"Query rewritten: '{raw_query}' -> '{rewritten}'")
    return rewritten
