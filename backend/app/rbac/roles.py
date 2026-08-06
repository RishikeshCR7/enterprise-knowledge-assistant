from enum import Enum
from typing import List, Set, Dict, Optional
from pydantic import BaseModel, Field


class UserRole(str, Enum):
    HR = "HR"
    ENGINEERING = "Engineering"
    FINANCE = "Finance"
    LEGAL = "Legal"
    SALES = "Sales"
    EXECUTIVE = "Executive"


class Department(str, Enum):
    HR = "HR"
    ENGINEERING = "Engineering"
    FINANCE = "Finance"
    LEGAL = "Legal"
    SALES = "Sales"
    EXECUTIVE = "Executive"


class SecurityLevel(str, Enum):
    PUBLIC = "Public"
    INTERNAL = "Internal"
    CONFIDENTIAL = "Confidential"
    RESTRICTED = "Restricted"


class UserContext(BaseModel):
    user_id: str = Field(..., description="Unique identifier for the user")
    username: str = Field(..., description="User display name or email")
    role: UserRole = Field(..., description="Assigned role for RBAC enforcement")
    department: Department = Field(..., description="User's primary department")
