

import imp
from typing import List
from pydantic import BaseModel, Field
from ser.secrets import public_key
from ser.services.auth import AdminUser
from ser.setup import Setup
from django.core.management.utils import get_random_secret_key

class PostgresConfig(BaseModel):
    host: str = "daten"
    port: int = 5432
    user: str = "hello_django"
    password: str = "hello_django"
    db_name: str

    @classmethod
    def from_setup(cls, setup: Setup, **kwargs):
        return PostgresConfig(user=setup.postgres_user, password=setup.postgres_password, **kwargs)


class RedisConfig(BaseModel):
    host: str = "redis"
    port: int = 6379


class LokConfig(BaseModel):
    public_key: str = Field(default_factory=lambda: public_key)
    key_type: str = "RS256"
    issuer: str = "herre"



class ServerConfig(BaseModel):
    debug: bool = False
    hosts: List[str] = ["*"]
    admin: AdminUser 
    secret_key: str = Field(default_factory=get_random_secret_key)

    @classmethod
    def from_setup(cls, setup: Setup, **kwargs):
        return ServerConfig(admin=AdminUser(username=setup.admin_username, email=setup.admin_email, password=setup.admin_password), debug=setup.debug, **kwargs)




    