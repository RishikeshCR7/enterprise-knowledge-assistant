from typing import List, Dict, Set, Any
from app.rbac.roles import UserRole, Department, SecurityLevel, UserContext

# Role-to-Department Access Mapping Matrix
ROLE_DEPARTMENT_ACCESS: Dict[UserRole, Set[Department]] = {
    UserRole.HR: {Department.HR},
    UserRole.ENGINEERING: {Department.ENGINEERING},
    UserRole.FINANCE: {Department.FINANCE},
    UserRole.LEGAL: {Department.LEGAL},
    UserRole.SALES: {Department.SALES},
    UserRole.EXECUTIVE: {
        Department.HR,
        Department.ENGINEERING,
        Department.FINANCE,
        Department.LEGAL,
        Department.SALES,
    },
}

# Role-to-Security Level Authorization
ROLE_SECURITY_CLEARANCE: Dict[UserRole, Set[SecurityLevel]] = {
    UserRole.HR: {SecurityLevel.PUBLIC, SecurityLevel.INTERNAL, SecurityLevel.CONFIDENTIAL},
    UserRole.ENGINEERING: {SecurityLevel.PUBLIC, SecurityLevel.INTERNAL, SecurityLevel.CONFIDENTIAL},
    UserRole.FINANCE: {SecurityLevel.PUBLIC, SecurityLevel.INTERNAL, SecurityLevel.CONFIDENTIAL},
    UserRole.LEGAL: {SecurityLevel.PUBLIC, SecurityLevel.INTERNAL, SecurityLevel.CONFIDENTIAL},
    UserRole.SALES: {SecurityLevel.PUBLIC, SecurityLevel.INTERNAL},
    UserRole.EXECUTIVE: {
        SecurityLevel.PUBLIC,
        SecurityLevel.INTERNAL,
        SecurityLevel.CONFIDENTIAL,
        SecurityLevel.RESTRICTED,
    },
}


def can_access_document(user: UserContext, doc_metadata: Dict[str, Any]) -> bool:
    """
    Evaluates whether a user context is authorized to view a document 
    based on allowed_roles, department, and security level metadata.
    """
    # 1. Executive bypass (full access)
    if user.role == UserRole.EXECUTIVE:
        return True

    # 2. Explicit role match check in allowed_roles
    allowed_roles = doc_metadata.get("allowed_roles")
    if not allowed_roles and "allowed_roles_str" in doc_metadata:
        allowed_roles = doc_metadata["allowed_roles_str"]

    if isinstance(allowed_roles, str):
        allowed_roles = [r.strip() for r in allowed_roles.split(",") if r.strip()]

    if allowed_roles:
        role_vals = [r.value if isinstance(r, UserRole) else str(r) for r in allowed_roles]
        if user.role.value in role_vals or user.role in allowed_roles:
            return True

    # 3. Department match check
    doc_dept = doc_metadata.get("department")
    allowed_departments = ROLE_DEPARTMENT_ACCESS.get(user.role, set())

    dept_accessible = doc_dept in [d.value for d in allowed_departments] or doc_dept in allowed_departments

    # 4. Security clearance check
    doc_sec_level = doc_metadata.get("security_level", SecurityLevel.INTERNAL.value)
    allowed_sec_levels = ROLE_SECURITY_CLEARANCE.get(user.role, set())
    sec_accessible = doc_sec_level in [s.value for s in allowed_sec_levels] or doc_sec_level in allowed_sec_levels

    return dept_accessible and sec_accessible


def build_chroma_rbac_filter(user: UserContext) -> Dict[str, Any]:
    """
    Builds a ChromaDB-compatible metadata query filter for vector search based on user role.
    """
    if user.role == UserRole.EXECUTIVE:
        return {}  # No restriction filter for Executive role

    # Enforce allowed_roles matching the user's role
    return {
        "allowed_roles": {
            "$in": [user.role.value]
        }
    }
