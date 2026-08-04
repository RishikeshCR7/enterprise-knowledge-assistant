import re
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# List of common greeting and casual phrases
GREETING_PATTERNS = [
    r'^\s*hi+\s*$',
    r'^\s*he+llo+\s*$',
    r'^\s*hey+\s*$',
    r'^\s*good\s+(morning|afternoon|evening)\s*$',
    r'^\s*thanks?\s*(you)?\s*$',
    r'^\s*who\s+are\s+you\s*$',
    r'^\s*what\s+can\s+you\s+do\s*$',
    r'^\s*help\s*$'
]

# Enterprise Domain Query Expansion Rules
DOMAIN_KEYWORD_EXPANSIONS = {
    "ethics": "Ethics Code of Conduct compliance anti harassment integrity policy employee conduct rules",
    "ethical": "Ethics Code of Conduct compliance anti harassment integrity policy employee conduct rules",
    "conduct": "Ethics Code of Conduct compliance anti harassment integrity policy employee conduct rules",
    "finances": "Finance quarterly financial performance report revenue net profit operating expenses budget",
    "financial": "Finance quarterly financial performance report revenue net profit operating expenses budget",
    "finance": "Finance quarterly financial performance report revenue net profit operating expenses budget",
    "revenue": "Finance quarterly financial performance report revenue net profit operating expenses budget",
    "profit": "Finance quarterly financial performance report revenue net profit operating expenses budget",
    "earnings": "Finance quarterly financial performance report revenue net profit operating expenses budget",
    "budget": "Finance Annual Operating Budget FY2026 department expenditure financial planning",
    "spending": "Finance Annual Operating Budget FY2026 department expenditure financial planning",
    "expenditure": "Finance Annual Operating Budget FY2026 department expenditure financial planning",
    "timing": "office working hours shift timings attendance work schedule policy",
    "timings": "office working hours shift timings attendance work schedule policy",
    "hours": "office working hours shift timings attendance work schedule policy",
    "shift": "office working hours shift timings attendance work schedule policy",
    "vacation": "HR leave policy vacation entitlement holiday request guidelines",
    "leave": "HR leave policy paid time off parental leave sick absence policy",
    "pto": "HR leave policy paid time off parental leave sick absence policy",
    "salary": "HR compensation policy salary structure payroll remuneration guidelines",
    "pay": "HR compensation policy salary structure payroll remuneration guidelines",
    "compensation": "HR compensation policy salary structure payroll remuneration guidelines",
    "hiring": "HR recruitment process interview procedures hiring policy",
    "coding": "Engineering software coding standards best practices style guide",
    "api": "Engineering API design guidelines REST specifications endpoints documentation",
    "docker": "Engineering Docker containerization deployment infrastructure guide",
    "expense": "Finance corporate expense policy travel reimbursement claim limits",
    "reimbursement": "Finance corporate expense policy travel reimbursement claim limits",
    "nda": "Legal non disclosure agreement vendor contract terms compliance policy",
    "pricing": "Sales product pricing strategy client discount matrix deal structure",
    "discount": "Sales product pricing strategy client discount matrix deal structure",
}


def classify_intent(raw_query: str) -> str:
    """
    Classifies user query intent into GREETING or ENTERPRISE_SEARCH.
    """
    if not raw_query or not raw_query.strip():
        return "GREETING"

    cleaned = raw_query.strip().lower()
    for pattern in GREETING_PATTERNS:
        if re.match(pattern, cleaned):
            return "GREETING"

    return "ENTERPRISE_SEARCH"


def rewrite_query(raw_query: str, user_context: Optional[Dict[str, Any]] = None) -> str:
    """
    Task B1: Rewrites raw user questions into optimized enterprise search queries.
    Cleans raw inputs and appends domain-specific search terms without polluting prefixes.
    """
    if not raw_query or not raw_query.strip():
        return "general enterprise documentation"

    query_lower = raw_query.strip().lower()

    # If greeting, return as is
    if classify_intent(raw_query) == "GREETING":
        return raw_query.strip()

    expanded_terms = []
    clean_words = set(re.findall(r'\b\w+\b', query_lower))

    # 1. Match domain keywords and apply contextual expansions
    for keyword, expansion in DOMAIN_KEYWORD_EXPANSIONS.items():
        if keyword in clean_words:
            expanded_terms.append(expansion)

    # 2. Clean query formulation
    if expanded_terms:
        unique_expansions = list(dict.fromkeys(expanded_terms))
        combined_expansion = " ".join(unique_expansions)
        rewritten = f"{raw_query.strip()} {combined_expansion}"
    else:
        words = raw_query.strip().split()
        if len(words) <= 3:
            rewritten = f"{raw_query.strip()} official company documentation"
        else:
            rewritten = raw_query.strip()

    logger.info(f"Query rewritten: '{raw_query}' -> '{rewritten}'")
    return rewritten
