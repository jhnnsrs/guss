

from enum import Enum
from typing import List
from pydantic import BaseModel, Field
import pydantic
from ser.secrets import generate_random_client_id, generate_random_client_secret

class User(BaseModel):
    username: str
    email: pydantic.EmailStr
    password: str
    groups: List[str] = Field(default_factory=list)


class ClientType(str, Enum):
    CONFIDENTIAL = "confidential"
    PUBLIC = "public"


class GrantType(str, Enum):
    AUTHORIZATION_CODE = "authorization-code"
    CLIENT_CREDENTIALS = "client-credentials"


class App(BaseModel):
    name: str
    client_type: ClientType = ClientType.PUBLIC
    grant_type: GrantType = GrantType.AUTHORIZATION_CODE
    client_id: str = Field(default_factory=generate_random_client_id)
    client_secret: str = Field(default_factory=generate_random_client_secret)
    redirect_uris: List[str] = []
    tenant: str


class AdminUser(BaseModel):
    username: str
    email: pydantic.EmailStr
    password: str