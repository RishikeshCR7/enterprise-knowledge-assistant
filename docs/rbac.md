# Role-Based Access Control (RBAC) Technical Guide

## 🔒 Overview
The platform enforces strict enterprise security controls at two levels:
1. **Metadata Filter Enforcement** during ChromaDB & BM25 vector candidate retrieval.
2. **Post-Retrieval Authorization Evaluation** before candidate text chunks are exposed to Cross-Encoder reranking or LLM context assembly.

---

## 📊 RBAC Permission Matrix

| User Role | Accessible Departments | Permitted Security Clearances |
| :--- | :--- | :--- |
| **HR** | HR | Public, Internal, Confidential |
| **Engineering** | Engineering | Public, Internal, Confidential |
| **Finance** | Finance | Public, Internal, Confidential |
| **Legal** | Legal | Public, Internal, Confidential |
| **Sales** | Sales | Public, Internal |
| **Executive** | HR, Engineering, Finance, Legal, Sales | Public, Internal, Confidential, Restricted |

---

## 🛡️ Security Rules

1. **Executive Access**: Users with `Role.EXECUTIVE` bypass department filters and possess full access across all security clearances.
2. **Cross-Department Restriction**: Standard users are strictly isolated to documents belonging to their assigned department or explicit `allowed_roles` metadata lists.
3. **Restricted Documents**: Documents marked with `SecurityLevel.RESTRICTED` can ONLY be accessed by Executive leadership.
