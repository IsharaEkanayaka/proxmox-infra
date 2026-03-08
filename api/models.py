from pydantic import BaseModel, Field
from typing import Optional


# --- Cluster ---

class CreateClusterRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=63, pattern=r'^[a-zA-Z0-9][a-zA-Z0-9_-]*$')
    node_count: int = Field(..., ge=1, le=20)


class CreateClusterResponse(BaseModel):
    cluster_id: str
    job_id: str


class UpdateClusterRequest(BaseModel):
    environment_id: Optional[str] = None


class ClusterNodes(BaseModel):
    control_plane: list[str]
    workers: list[str]


class ClusterDetail(BaseModel):
    id: str
    name: str
    node_count: int
    control_plane_count: int
    worker_count: int
    status: str
    nodes: ClusterNodes
    environment_id: Optional[str] = None
    latest_job_id: Optional[str] = None
    created_at: str


# --- Environment ---

class CreateEnvironmentRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=63, pattern=r'^[a-zA-Z0-9][a-zA-Z0-9_-]*$')


class EnvironmentDetail(BaseModel):
    id: str
    name: str
    status: str
    clusters: list[str] = []
    created_at: str


# --- Job ---

class JobDetail(BaseModel):
    id: str
    cluster_id: str
    type: str
    status: str
    error: Optional[str] = None
    created_at: str


# --- Namespace ---

class CreateNamespaceRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=63, pattern=r'^[a-z][a-z0-9-]*$')


class NamespaceDetail(BaseModel):
    id: str
    cluster_id: str
    name: str
    status: str
    created_at: str


# --- Auth ---

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    token: str
    user: 'UserDetail'


# --- User ---

class CreateUserRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=63, pattern=r'^[a-zA-Z0-9][a-zA-Z0-9._-]*$')
    name: str = Field(..., min_length=1, max_length=100)
    role: str = Field('viewer', pattern=r'^(admin|team_lead|developer|viewer)$')
    password: str = Field(..., min_length=4, max_length=128)


class UserDetail(BaseModel):
    id: str
    username: str
    name: str
    role: str
    api_key: Optional[str] = None
    is_active: bool
    created_at: str


class GrantPermissionRequest(BaseModel):
    user_id: str
    resource_type: str = Field(..., pattern=r'^(cluster|namespace|environment)$')
    resource_id: str
    access: str = Field('read', pattern=r'^(read|write)$')


class PermissionDetail(BaseModel):
    id: int
    user_id: str
    resource_type: str
    resource_id: str
    access: str
