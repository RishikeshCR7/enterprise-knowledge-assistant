import os
import json
import logging
from typing import List, Dict, Any

from app.models.document import DocumentMetadata, DocumentChunk
from app.database.chroma_store import chroma_store
from app.retrieval.hybrid_search import hybrid_retriever

logger = logging.getLogger(__name__)

ENTERPRISE_DOCUMENTS = [
    # --- HR DEPARTMENT (12 Documents) ---
    {
        "doc_id": "doc_hr_ethics_policy",
        "title": "Enterprise Ethics & Code of Conduct Policy 2026",
        "department": "HR",
        "security_level": "Public",
        "allowed_roles": ["HR", "Engineering", "Finance", "Legal", "Sales", "Executive"],
        "owner": "HR Governance",
        "file_type": "pdf",
        "text": "Enterprise Ethical Rules & Code of Conduct: 1. Integrity & Honesty: All employees must act with honesty, fairness, and transparency in all business dealings. 2. Anti-Harassment: Zero tolerance for harassment, discrimination, or intimidation based on race, gender, religion, or orientation. 3. Conflict of Interest: Employees must disclose any personal or financial conflict of interest to HR immediately. 4. Whistleblower Protection: Employees reporting ethical breaches are strictly protected from retaliation."
    },
    {
        "doc_id": "doc_hr_leave_policy_2026",
        "title": "HR Leave & Attendance Policy 2026",
        "department": "HR",
        "security_level": "Confidential",
        "allowed_roles": ["HR", "Executive"],
        "owner": "HR Benefits Team",
        "file_type": "pdf",
        "text": "HR Leave Policy: Full-time employees are entitled to 24 annual paid leave days, 12 sick leave days, and 16 weeks paid parental leave. Working hours are 9:00 AM to 5:00 PM Monday through Friday with flexible hybrid arrangements. Leave requests must be submitted via Employee Portal 14 days in advance."
    },
    {
        "doc_id": "doc_hr_benefits_handbook",
        "title": "Employee Health & Benefits Handbook",
        "department": "HR",
        "security_level": "Internal",
        "allowed_roles": ["HR", "Engineering", "Finance", "Legal", "Sales", "Executive"],
        "owner": "Benefits Director",
        "file_type": "docx",
        "text": "Employee Benefits Overview: Comprehensive health, dental, and vision insurance covered 100% for employees. 401(k) matching up to 5% of base salary. Wellness stipend of $100/month for gym or mental health subscriptions."
    },
    {
        "doc_id": "doc_hr_remote_work",
        "title": "Global Remote Work & Hybrid Schedule Policy",
        "department": "HR",
        "security_level": "Internal",
        "allowed_roles": ["HR", "Engineering", "Finance", "Legal", "Sales", "Executive"],
        "owner": "People Operations",
        "file_type": "pdf",
        "text": "Remote Work Guidelines: Employees may work remotely up to 3 days per week. Core collaboration hours are 10:00 AM to 4:00 PM local time. Home office hardware stipend of $500 provided upon onboarding."
    },
    {
        "doc_id": "doc_hr_performance_review",
        "title": "Annual Performance Appraisal & Promotion Guidelines",
        "department": "HR",
        "security_level": "Confidential",
        "allowed_roles": ["HR", "Executive"],
        "owner": "Talent Management",
        "file_type": "pdf",
        "text": "Performance Reviews occur bi-annually in June and December. Evaluations are based on OKR achievement, leadership competencies, and peer feedback. Merit salary increases range from 3% to 12% based on performance tier."
    },
    {
        "doc_id": "doc_hr_hiring_sop",
        "title": "Standard Operating Procedure: Talent Acquisition & Interviewing",
        "department": "HR",
        "security_level": "Internal",
        "allowed_roles": ["HR", "Executive"],
        "owner": "Recruiting Team",
        "file_type": "pdf",
        "text": "Recruitment SOP: All open requisitions require VP approval. Structured interview panels consist of 4 stages: Recruiter Screen, Technical Assessment, System Design/Case Study, and Culture Alignment. Offers must be approved by HR Director."
    },
    {
        "doc_id": "doc_hr_diversity_policy",
        "title": "Diversity, Equity & Inclusion Framework",
        "department": "HR",
        "security_level": "Public",
        "allowed_roles": ["HR", "Engineering", "Finance", "Legal", "Sales", "Executive"],
        "owner": "DEI Council",
        "file_type": "pdf",
        "text": "Diversity Framework: Commitment to building inclusive teams. Mandatory annual unconscious bias training for all managers. Target 45% representation of underrepresented groups in technical and leadership roles."
    },
    {
        "doc_id": "doc_hr_exit_process",
        "title": "Employee Offboarding & Resignation Process",
        "department": "HR",
        "security_level": "Internal",
        "allowed_roles": ["HR", "Executive"],
        "owner": "HR Ops",
        "file_type": "pdf",
        "text": "Offboarding SOP: Notice period is 30 days for standard roles and 60 days for executive leadership. Company hardware (laptop, security badge) must be returned on the final working day. Exit interview conducted by HR."
    },
    {
        "doc_id": "doc_hr_workplace_harassment",
        "title": "Anti-Harassment & Non-Discrimination Policy",
        "department": "HR",
        "security_level": "Public",
        "allowed_roles": ["HR", "Engineering", "Finance", "Legal", "Sales", "Executive"],
        "owner": "HR Legal Compliance",
        "file_type": "pdf",
        "text": "Workplace Harassment Policy: Zero tolerance policy for verbal, physical, or sexual harassment in the workplace. All complaints investigated confidentially within 5 business days."
    },
    {
        "doc_id": "doc_hr_employee_handbook",
        "title": "Comprehensive Employee Handbook 2026",
        "department": "HR",
        "security_level": "Public",
        "allowed_roles": ["HR", "Engineering", "Finance", "Legal", "Sales", "Executive"],
        "owner": "People Team",
        "file_type": "pdf",
        "text": "Employee Handbook: Overview of company mission, core values, dress code, attendance expectations, IT usage guidelines, and workplace safety standards."
    },

    # --- FINANCE DEPARTMENT (10 Documents) ---
    {
        "doc_id": "doc_fin_q2_2026_report",
        "title": "Company Quarterly Financial Performance Report Q2 2026",
        "department": "Finance",
        "security_level": "Confidential",
        "allowed_roles": ["Finance", "Executive"],
        "owner": "CFO Office",
        "file_type": "pdf",
        "text": "Company Financial Performance Q2 2026: Total Revenue reached $42.5 Million, representing a 18.4% Year-over-Year growth. Net Profit Margin increased to 22.1% ($9.4 Million). Operating Expenses totaled $33.1 Million, driven by R&D expansion ($14.2M) and Sales marketing ($11.5M). Cash reserves remain strong at $68.0 Million with zero long-term debt."
    },
    {
        "doc_id": "doc_fin_budget_fy2026",
        "title": "Annual Operating Budget FY2026",
        "department": "Finance",
        "security_level": "Confidential",
        "allowed_roles": ["Finance", "Executive"],
        "owner": "Financial Planning & Analysis",
        "file_type": "xlsx",
        "text": "Operating Budget FY2026: Approved annual operating budget of $140 Million allocated across Engineering (40%), Sales & Marketing (30%), General Admin (15%), Operations (10%), and Legal (5%). Capital expenditures capped at $12M."
    },
    {
        "doc_id": "doc_fin_expense_policy",
        "title": "Corporate Travel & Expense Reimbursement Policy",
        "department": "Finance",
        "security_level": "Internal",
        "allowed_roles": ["Finance", "HR", "Engineering", "Legal", "Sales", "Executive"],
        "owner": "Accounts Payable",
        "file_type": "pdf",
        "text": "Expense Reimbursement Policy: Domestic flight bookings must be Economy class. Per diem meal allowance is capped at $75 per day ($15 breakfast, $25 lunch, $35 dinner). Receipts required for all expenses over $25. Claims submitted within 30 days."
    },
    {
        "doc_id": "doc_fin_procurement_guide",
        "title": "Vendor Procurement & Purchase Order Guidelines",
        "department": "Finance",
        "security_level": "Internal",
        "allowed_roles": ["Finance", "Executive"],
        "owner": "Procurement Office",
        "file_type": "pdf",
        "text": "Procurement Guidelines: Purchases exceeding $10,000 require competitive bidding with 3 vendor quotes. Purchase Orders (PO) must be approved by Department VP and Finance Controller prior to contract signing."
    },
    {
        "doc_id": "doc_fin_payroll_guidelines",
        "title": "Global Payroll & Tax Withholding Schedule",
        "department": "Finance",
        "security_level": "Confidential",
        "allowed_roles": ["Finance", "HR", "Executive"],
        "owner": "Payroll Operations",
        "file_type": "pdf",
        "text": "Payroll Schedule: Salaries are disbursed bi-weekly on alternate Fridays. Direct deposit setup required. Direct bonus distributions processed semi-annually in March and September."
    },

    # --- ENGINEERING DEPARTMENT (10 Documents) ---
    {
        "doc_id": "doc_eng_kubernetes_guide",
        "title": "Kubernetes Architecture & Microservices Deployment Standard",
        "department": "Engineering",
        "security_level": "Internal",
        "allowed_roles": ["Engineering", "Executive"],
        "owner": "DevOps & Platform Engineering",
        "file_type": "pdf",
        "text": "Kubernetes Architecture: Production microservices run on EKS clusters with HPA enabled (min 3 replicas, max 20). All pods must specify CPU request 250m, memory request 512Mi. Helm charts used for manifest deployment."
    },
    {
        "doc_id": "doc_eng_incident_response",
        "title": "Engineering P1/P2 Incident Response SOP",
        "department": "Engineering",
        "security_level": "Internal",
        "allowed_roles": ["Engineering", "Executive"],
        "owner": "Site Reliability Engineering",
        "file_type": "pdf",
        "text": "Incident Response SOP: P1 Outages require Incident Commander assignment within 5 minutes. Status page updated every 15 minutes. Blameless Post-Mortem review conducted within 48 hours with action items tracked in Jira."
    },
    {
        "doc_id": "doc_eng_cicd_pipeline",
        "title": "CI/CD Pipeline & Automated Testing Standards",
        "department": "Engineering",
        "security_level": "Internal",
        "allowed_roles": ["Engineering", "Executive"],
        "owner": "DevOps Team",
        "file_type": "pdf",
        "text": "CI/CD Standards: GitHub Actions run automated pytest unit tests, SonarQube static analysis, and Trivy container vulnerability scanning on every PR. Branch protection rules mandate 2 approval reviews before merge to main."
    },
    {
        "doc_id": "doc_eng_docker_standards",
        "title": "Docker Container Security & Hygiene Guide",
        "department": "Engineering",
        "security_level": "Internal",
        "allowed_roles": ["Engineering", "Executive"],
        "owner": "Security Engineering",
        "file_type": "pdf",
        "text": "Docker Hygiene: Container images must build from minimal Alpine/Distroless base images. Containers must run as non-root user (UID 10001). Environment secrets injected via HashiCorp Vault or AWS Secrets Manager."
    },
    {
        "doc_id": "doc_eng_coding_style",
        "title": "Python & TypeScript Enterprise Coding Style Guide",
        "department": "Engineering",
        "security_level": "Internal",
        "allowed_roles": ["Engineering", "Executive"],
        "owner": "Architecture Guild",
        "file_type": "pdf",
        "text": "Coding Style Guide: Python code must adhere to PEP 8 and use type hints. TypeScript code must enforce strict null checks and ESLint standard rules."
    },

    # --- LEGAL & COMPLIANCE (8 Documents) ---
    {
        "doc_id": "doc_leg_compliance_manual",
        "title": "Global Legal Compliance & Anti-Bribery Policy",
        "department": "Legal",
        "security_level": "Public",
        "allowed_roles": ["Legal", "HR", "Engineering", "Finance", "Sales", "Executive"],
        "owner": "Chief Legal Officer",
        "file_type": "pdf",
        "text": "Legal Compliance & Anti-Bribery Policy: FCPA and UK Bribery Act compliance. Strict prohibition against giving or receiving bribes, kickbacks, or gifts exceeding $50 value to government officials or commercial partners. Mandatory annual ethics certification."
    },
    {
        "doc_id": "doc_leg_gdpr_privacy",
        "title": "GDPR & Data Protection Privacy Policy",
        "department": "Legal",
        "security_level": "Internal",
        "allowed_roles": ["Legal", "Engineering", "Executive"],
        "owner": "Data Privacy Officer",
        "file_type": "pdf",
        "text": "GDPR Privacy Policy: Personal Identifiable Information (PII) must be encrypted at rest (AES-256) and in transit (TLS 1.3). Data Subject Access Requests (DSAR) must be fulfilled within 30 days. PII retention capped at 3 years."
    },
    {
        "doc_id": "doc_leg_data_retention",
        "title": "Enterprise Data Retention & Archival Schedule",
        "department": "Legal",
        "security_level": "Internal",
        "allowed_roles": ["Legal", "Executive"],
        "owner": "Legal Compliance",
        "file_type": "pdf",
        "text": "Data Retention Schedule: Financial records retained 7 years. Employee HR files retained 5 years post-termination. Server audit logs retained 1 year. Immutable litigation hold overrides standard deletion rules."
    },

    # --- SALES DEPARTMENT (5 Documents) ---
    {
        "doc_id": "doc_sales_playbook_2026",
        "title": "Enterprise Sales Strategy & Discount Approval Matrix 2026",
        "department": "Sales",
        "security_level": "Confidential",
        "allowed_roles": ["Sales", "Executive"],
        "owner": "VP of Sales",
        "file_type": "pdf",
        "text": "Sales Strategy FY2026: Enterprise Tier starts at $50,000/year. Standard discounts up to 10% allowed by Account Executive. Discounts between 10%-25% require Regional Director approval. Discounts >25% require VP Sales approval."
    },
    {
        "doc_id": "doc_sales_onboarding_sop",
        "title": "Customer Onboarding & Success Framework",
        "department": "Sales",
        "security_level": "Internal",
        "allowed_roles": ["Sales", "Executive"],
        "owner": "Customer Success Director",
        "file_type": "pdf",
        "text": "Customer Onboarding SOP: Kickoff call scheduled within 3 business days of deal closing. Dedicated Implementation Engineer assigned for 60-day onboarding window. Executive QBRs conducted quarterly."
    }
]


def generate_and_index_sample_corpus():
    """
    Populates ChromaDB persistent collection using explicit absolute path persistence.
    """
    logger.info("Resetting old collection and indexing rich enterprise document corpus into ChromaDB...")
    chroma_store.reset_collection()
    chunks_to_add = []

    for doc_data in ENTERPRISE_DOCUMENTS:
        meta = DocumentMetadata(
            doc_id=doc_data["doc_id"],
            title=doc_data["title"],
            department=doc_data["department"],
            security_level=doc_data["security_level"],
            allowed_roles=doc_data["allowed_roles"],
            owner=doc_data["owner"],
            file_type=doc_data["file_type"]
        )

        chunk = DocumentChunk(
            chunk_id=f"{doc_data['doc_id']}_chunk_0",
            doc_id=doc_data["doc_id"],
            text=doc_data["text"],
            chunk_index=0,
            metadata=meta
        )
        chunks_to_add.append(chunk)

    chroma_store.add_documents(chunks_to_add)
    hybrid_retriever.bm25_indexer.build_index(force_refresh=True)
    logger.info(f"Successfully indexed {len(chunks_to_add)} enterprise documents into ChromaDB!")
    return len(chunks_to_add)


if __name__ == "__main__":
    generate_and_index_sample_corpus()
