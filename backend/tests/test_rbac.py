from app.rbac import (
    UserRole,
    Department,
    SecurityLevel,
    UserContext,
    can_access_document,
    build_chroma_rbac_filter,
)


def test_rbac_roles_and_permissions():
    hr_user = UserContext(
        user_id="usr_001",
        username="hr_alice",
        role=UserRole.HR,
        department=Department.HR,
    )

    eng_user = UserContext(
        user_id="usr_002",
        username="eng_bob",
        role=UserRole.ENGINEERING,
        department=Department.ENGINEERING,
    )

    hr_doc = {
        "doc_id": "doc_hr_1",
        "title": "Salary Policy",
        "department": "HR",
        "security_level": "Confidential",
        "allowed_roles": ["HR", "Executive"],
    }

    # HR User should be allowed to access HR Doc
    assert can_access_document(hr_user, hr_doc) is True

    # Engineering User should NOT be allowed to access HR Doc
    assert can_access_document(eng_user, hr_doc) is False

    # Check ChromaDB filter generation
    eng_filter = build_chroma_rbac_filter(eng_user)
    assert eng_filter == {"allowed_roles": {"$in": ["Engineering"]}}

    print("[OK] RBAC tests passed successfully!")


if __name__ == "__main__":
    test_rbac_roles_and_permissions()
