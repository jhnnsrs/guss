



from typing import Dict, List
from pydantic import BaseModel, EmailStr, Field, root_validator

from ser.services.auth import App, User
from ser.secrets import generate_random_password


class Setup(BaseModel):
    admin_username: str
    admin_email: EmailStr
    admin_password: str

    # postgres db
    debug: bool = True
    common_redis: bool = True
    common_db: bool = True
    postgres_password: str = Field(default_factory=generate_random_password)
    postgres_user: str = "arkitekt"

    hosts: List[str] = ["localhost"]

    dev_services: Dict[str, str] = Field(default_factory=list)
    services: List[str]


    loks: List[User] = Field(default_factory=list)
    apps: List[App]  = Field(default_factory=list)

    
    @root_validator()
    def validate_loks_and_apps(cls, values):
        available_users = [user.username for user in values.get("loks", [])]

        for app in values.get("apps", []):
            if app.tenant == values["admin_username"]:
                raise ValueError("App should not be hold by admin account")

            if app.tenant is None:
                app.tenant = available_users[0]

            if app.tenant not in available_users:

                raise ValueError(f"{app} has unknown tenant available are {available_users}")

        return values



    @root_validator()
    def validate_admin_not_in_loks(cls, values):
        available_users = [user.username for user in values.get("loks", [])]

        if values["admin_username"] in available_users:
            raise ValueError("Admin can't be a lok user")

        return values