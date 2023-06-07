from typing import Dict, List
from pydantic import BaseModel, EmailStr, Field, root_validator
from typing import Optional
from .secrets import generate_random_password, public_key, private_key, generate_random_username, generate_random_client_id, generate_random_client_secret, generate_random_token
from typing import Any, Literal, Union
import os
import itertools
import shutil
import yaml 
from .utils import remove_none, guard_empty
import json
from django.core.management.utils import get_random_secret_key
from ser.utils import create_config_mount, create_dev_mount, create_fakts_mount, create_docker_mount
import pydantic
from enum import Enum

class DockerCompose(BaseModel):
    version: str = "3.7"
    services: Optional[Dict]
    volumes: Optional[Dict]
    networks: Optional[Dict]
    secrets: Optional[Dict]



class DockerService(BaseModel):
    name: str
    image: str
    ports: Optional[List[str]]
    volumes: Optional[List[Optional[str]]]
    networks: Optional[List[Optional[str]]]
    environment: Optional[Dict]
    command: Optional[str]
    depends_on: Union[List[str], Dict[str, Any]] = Field(default_factory=list)
    labels: Optional[List[str]]



class DockerDriverOpts(BaseModel):
    o: str = "bind"
    type: str = "none"
    device: str 


class DockerVolume(BaseModel):
    name: str
    driver: str
    driver_opts: DockerDriverOpts

    @classmethod
    def from_local(cls, name,  path: str):
        return DockerVolume(name=name, driver="local", driver_opts=DockerDriverOpts(device=path))

class DockerNetwork(BaseModel):
    name: str
    driver: str

    @classmethod
    def from_local(cls, name,  path: str):
        return DockerNetwork(name=name, driver="bridge")


class Group(BaseModel):
    name: str
    description: str


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
    identifier: str
    version: str
    client_type: ClientType = ClientType.PUBLIC
    grant_type: GrantType = GrantType.AUTHORIZATION_CODE
    client_id: str = Field(default_factory=generate_random_client_id)
    client_secret: str = Field(default_factory=generate_random_client_secret)
    redirect_uris: List[str] = []
    scopes: List[str] = []
    tenant: str = None
    token: str = Field(default_factory=generate_random_token)


class AdminUser(BaseModel):
    username: str
    email: pydantic.EmailStr
    password: str


class Binding(BaseModel):
    name: str
    host: str
    ip: Optional[str]
    ssl: bool = False



class AdminUser(BaseModel):
    username: str
    password: str
    email: str



class Depend(BaseModel):
    pass


class Fakt(BaseModel):
    pass




def to_http_base(host: str, port: str, internal_lok: str = "lok", internal_port: str = None):
    return '{{"https" if request.is_secure else "http" }}://{{"' + host + '" if request.host == "' + internal_lok + '" else request.host}}:' + str(port)

def to_ws_base(host: str, port: str, internal_lok: str = "lok", internal_port: str = None):
    return '{{"wss" if request.is_secure else "ws" }}://{{"' + host + '" if request.host == "' + internal_lok + '" else request.host}}:' + str(port)


class DjangoConfig(BaseModel):
    debug: bool = False
    hosts: List[str] = ["*"]
    admin: AdminUser 
    secret_key: str = Field(default_factory=get_random_secret_key)



class BaseService(BaseModel):
    name: str
    interface: str
    description: str
    long: str
    image: Optional[str]
    requires: List[str]
    dev: Optional[bool]


    dependencies: Dict[str, Depend] = Field(default_factory=dict)


    def resolve(self, setup: "Setup"):
        print(f"Resolving {self.name} with {self.requires}")
        self.dependencies = {}
        for service in setup.services:
            if service.interface in self.requires:
                print("Depending on", service)
                self.dependencies[service.interface] = service.depend(self)
               

        print(self.dependencies)
        
    def create_dirs(self, setup: "Setup"):
        pass

    def create_fakt(self, setup: "Setup") -> Fakt:
        return None
    
    def create_raw_fakt(self, setup: "Setup") -> str:
        return None

    
    def create_config(self, setup: "Setup") -> BaseModel:
        """Also the place for validation

        Raises:
            NotImplementedError: _description_

        Returns:
            BaseModel: _description_
        """
        return None

    def create_docker_services(self, setup: "Setup") -> List[DockerService]:
        return []

    def create_docker_volumes(self, setup: "Setup") -> List[DockerVolume]:
        return []
    
    def create_docker_networks(self, setup: "Setup") -> List[DockerNetwork]:
        return []

    def create_dev(self, setup: "Setup") -> None:
        pass
    
    class Config:
        underscore_attrs_are_private = True




class GivingService(BaseService):

    def depend(self, service: BaseService):
        pass



class Bucket(BaseModel):
    name: str


class MinioUser(BaseModel):
    name: str
    access_key: str = Field(default_factory=generate_random_username)
    secret_key: str = Field(default_factory=generate_random_password)
    policies: List[str]




class BucketNeedingService(BaseService):
    required_buckets: List[Bucket]
    required_policies: List[str]


class DbDepend(Depend):
    username: str 
    password: str
    host: str 
    port: int
    db_name: str
    engine: str



class PostgresService(GivingService):
    name: Literal["postgres"]
    host: str = "db"
    port: int = 5432
    username: str = Field(default_factory=generate_random_username)
    password: str = Field(default_factory=generate_random_password)

    databases: List[str] = Field(default_factory=list)

    def depend(self, service: BaseService):
        database_name = f"{service.name}_db"
        self.databases.append(database_name)

        return DbDepend(
            username=self.username,
            password=self.password,
            port=self.port,
            host=self.host,
            db_name=database_name,
            engine="django.db.backends.postgresql"
        )

    def create_docker_services(self, setup: "Setup") -> List[DockerService]:

        volumes = []

        if self.dev:
            volumes.append(create_dev_mount(self.name))

        return [
            DockerService(
                name="db", 
                image=self.image, 
                volumes=volumes, 
                environment={
                    "POSTGRES_USER": self.username,
                    "POSTGRES_PASSWORD": self.password,
                    "POSTGRES_MULTIPLE_DATABASES": ", ".join(set(self.databases)),
                },
                depends_on=[],
                labels=[f"arkitekt.{setup.name}.service=postgres"])
        ]





class RabbitMQDepend(Depend):
    username: str 
    password: str
    v_host: str 
    host: str 
    port: int


class RabbitMQService(GivingService):
    name: Literal["rabbitmq"]
    host: str = "rabbitmq"
    port: int = 5672
    username: str = "guest"
    password: str = "guest"


    def depend(self, service: "Service"):
        return RabbitMQDepend(
            username=self.username,
            password=self.password,
            port=self.port,
            host=self.host,
            v_host=""
        )

    def create_docker_services(self, setup: "Setup") -> List[DockerService]:

        command = "rabbitmq-server"

        return [
            DockerService(
                name=self.host, 
                image=self.image, 
                command=command,
                ports=[], 
                volumes=[],  
                depends_on=[],
                labels=[f"arkitekt.{setup.name}.service=rabbitmq"])
        ]


class RedisDepend(Depend):
    host: str
    port: int


class RedisService(GivingService):
    name: Literal["redis"]
    host: str = "redis"
    port: int = 6379

    def depend(self, service: BaseService):
        return RedisDepend(host=self.host, port=self.port)

    def create_docker_services(self, setup: "Setup") -> List[DockerService]:

        return [
            DockerService(
                name=self.interface, 
                image=self.image, 
                ports=[], 
                volumes=[],  
                depends_on=[],
                labels=[f"arkitekt.{setup.name}.service=redis"])
        ]
    

class OrkestratorService(GivingService):
    name: Literal["orkestrator"]
    host: str = "orkestrator"
    port: int = 80
    public_port: int = 6789

    def create_docker_services(self, setup: "Setup") -> List[DockerService]:
        ports = [f"{self.public_port}:{self.port}"]

        return [
            DockerService(
                name=self.interface, 
                image=self.image, 
                ports=ports, 
                volumes=[],  
                depends_on=[],
                labels=[f"arkitekt.{setup.name}.service=orkestrator"])
        ]




class MinioDepend(Depend):
    host: str
    port: str
    protocol: str
    access_key: str
    secret_key: str
    buckets: List[Bucket]


class MinioConfig(BaseModel):
    buckets: List[Bucket]
    users: List[MinioUser]


class MinioFakt(Fakt):
    endpoint_url: str


class MinioService(GivingService):
    name: Literal["minio"]
    init_image: str = "jhnnsrs/init:prod"
    host: str = "minio"
    port: int = 9000
    public_port: int = 9000
    root_username: str = Field(default_factory=generate_random_username)
    root_password: str = Field(default_factory=generate_random_password)
    with_dashboard: bool = False
    dashboard_port: int = 9001
    public_dashboard_port: int = 9001

    buckets: List[Bucket] = Field(default_factory=list)
    users: List[MinioUser] = Field(default_factory=list)

    def depend(self, service: "Service"):
        assert hasattr(service, "required_buckets"), f"Service {service.name} needs to require buckets to depend on minio"
        assert hasattr(service, "required_policies"),  f"Service {service.name} needs to require policies to depend on minio"
        
        self.buckets = self.buckets + service.required_buckets

        user = MinioUser(name=service.name, policies=service.required_policies)
        self.users.append(user)

        return MinioDepend(
            host=self.host,
            port=self.port,
            protocol="http",
            access_key=user.access_key,
            secret_key=user.secret_key,
            buckets=service.required_buckets

        )

    def create_config(self, setup: "Setup") -> BaseModel:

        return MinioConfig(
            buckets=self.buckets,
            users=self.users,
        )

    def create_fakt(self, setup: "Setup") -> Fakt:

        base = to_http_base(self.host, self.public_port, internal_port=self.port)
        return MinioFakt(
            endpoint_url=f"{base}",
            healthz=f"{base}/minio/health/live",
        )
    


    def create_docker_services(self, setup: "Setup") -> List[DockerService]:

        ports = [f"{self.public_port}:{self.port}"]

        if self.with_dashboard:
            command = f"server /data --console-address :{self.public_dashboard_port}"
            ports.append(f"{self.dashboard_port}:{self.public_dashboard_port}")
        else:
            command = f"server /data"

        return [
            DockerService(
                name=self.interface, 
                image=self.image, 
                command=command,
                ports=ports, 
                environment={
                    "MINIO_ROOT_USER": self.root_username,
                    "MINIO_ROOT_PASSWORD": self.root_password,
                },
                depends_on=[],
                labels=[f"arkitekt.{setup.name}.service=minio"]),
             DockerService(
                name="initc", 
                image=self.init_image, 
                volumes=[create_config_mount(self.name)],
                environment={
                    "MINIO_HOST": f"http://minio:{self.port}",
                    "MINIO_ROOT_USER": self.root_username,
                    "MINIO_ROOT_PASSWORD": self.root_password,
                },
                depends_on={"minio": {"condition": "service_started"}})
        ]


    




class LokDepend(Depend):
    public_key: str
    key_type: str
    issuer: str


class Deployment(BaseModel):
    name: str

class LokConfig(BaseModel):
    activation_days: int
    redis: RedisDepend
    db: DbDepend
    token_expire_seconds: int
    minio: MinioDepend
    scopes: Dict[str, str]
    public_key: str
    private_key: str
    apps: List[App]
    users: List[User]
    groups: List[Group]
    django: DjangoConfig
    deployment: Deployment



DEFAULT_SCOPES = {
    "read": "Reading all of your Data",
  "read_starred": "Reading all of your shared Data",
  "provider": "Can act as a provider",
  "introspection": "Introspect the Token scope",
  "can_provide": "Can Provide Nodes",
  "can_assign": "Can Assign Nodes",
  "can_template": "Can Template Nodes",
  "can_create": "Can Create Nodes",
  "can_forward_bounce": "Can reserve and assign to Nodes mimicking other Users (only backend and admin)",
  "can_create_identifier": "Can create new identifier for the platform"
}


class LokFakt(Fakt):
    base_url: str
    endpoint_url: str
    healthz: str
    ws_endpoint_url: str
    client_id: str
    client_secret: str
    grant_type: str 
    name: str 

SCOPES_REPLACE = """
  scopes: {% for item in client.scopes %}
    - "{{item}}"
  {% endfor %}
"""

class LokService(GivingService, BucketNeedingService):
    name: Literal["lok"]
    public_key: str = Field(default_factory=lambda: public_key)
    private_key: str = Field(default_factory=lambda: private_key)
    activation_days: int = 7
    token_expire_seconds: int = 60 * 60 * 24 * 7
    scopes: Dict[str, str] = Field(default_factory=lambda: {**DEFAULT_SCOPES})
    key_type = "RS256"
    issuer = "lok"
    host: str = "lok"
    port: int = 8000
    public_port: int = 8000
    required_buckets: List[Bucket] = Field(default_factory=lambda: [Bucket(name="lokmedia")])
    required_policies: List[str] =  Field(default_factory=lambda: ["readwrite"])

    def depend(self, service: "Service"):
        return LokDepend(
            public_key=self.public_key,
            key_type=self.key_type,
            issuer=self.issuer
        )

    def create_config(self, setup: "Setup") -> BaseModel:

        return LokConfig(
            redis=self.dependencies["redis"],
            db=self.dependencies["db"],
            minio=self.dependencies["minio"],
            activation_days=self.activation_days,
            token_expire_seconds=self.token_expire_seconds,
            scopes=self.scopes,
            key_type=self.key_type,
            private_key=self.private_key,
            public_key=self.public_key,
            users=setup.users,
            apps=setup.apps,
            groups=setup.groups,
            django=DjangoConfig(
                debug=self.dev is True,
                admin=AdminUser(
                    username=setup.admin_username,
                    email=setup.admin_email,
                    password=setup.admin_password,
                )
            ),
            deployment=Deployment(name=setup.name)
        )

    
    def create_raw_fakt(self, setup: "Setup") -> str:

        base = to_http_base(self.host, self.public_port, internal_port=self.port)
        ws_base = to_ws_base(self.host, self.public_port, internal_port=self.port)   


        t = yaml.dump(json.loads(json.dumps({"lok": LokFakt(
            base_url=f"{base}/o",
            endpoint_url=f"{base}/graphql",
            healthz=f"{base}/ht",
            ws_endpoint_url=f"{ws_base}/graphql",
            client_id="{{client.client_id}}",
            client_secret="{{client.client_secret}}",
            grant_type="{{client.authorization_grant_type}}",
            name="{{client.name}}",
        ).dict()})))

        return t + SCOPES_REPLACE



    def create_docker_services(self, setup: "Setup") -> List[DockerService]:

        volumes = [create_config_mount(self.name), create_fakts_mount()]

        if self.dev:
            volumes.append(create_dev_mount(self.name))

        ports = [f"{self.public_port}:{self.port}"]

        return [
            DockerService(
                name="lok", 
                image=self.image, 
                ports=ports, 
                volumes=volumes,  
                depends_on=["redis","db"],
                labels=[f"arkitekt.{setup.name}.service=lok"])
        ]







class RekuestConfig(BaseModel):
    lok: "LokDepend"
    rabbitmq: "RabbitMQDepend"
    db: DbDepend
    redis: RedisDepend
    django: DjangoConfig


class RekuestAgentFakt(BaseModel):
    endpoint_url: str

class RekuestFakt(Fakt):
    endpoint_url: str
    healthz: str
    ws_endpoint_url: str
    agent: RekuestAgentFakt


class RekuestService(BaseService):
    name: Literal["rekuest"]
    host: str = "rekuest"
    port: int = 8090
    public_port: int = 8090


    def create_config(self, setup: "Setup") -> BaseModel:

        return RekuestConfig(
            lok=self.dependencies["lok"],
            rabbitmq=self.dependencies["rabbitmq"],
            redis=self.dependencies["redis"],
            db=self.dependencies["db"],
            django=DjangoConfig(
                debug=self.dev is True,
                admin=AdminUser(
                    username=setup.admin_username,
                    email=setup.admin_email,
                    password=setup.admin_password,
                )
            )
        )

    def create_fakt(self, setup: "Setup") -> Fakt:

        base = to_http_base(self.host, self.public_port, internal_port=self.port)
        ws_base = to_ws_base(self.host, self.public_port, internal_port=self.port)
        return RekuestFakt(
            base_url=f"{base}/o",
            endpoint_url=f"{base}/graphql",
            healthz=f"{base}/ht",
            agent=RekuestAgentFakt(endpoint_url=f"{ws_base}/agi"),
            ws_endpoint_url=f"{ws_base}/graphql"
        )


    def create_docker_services(self, setup: "Setup") -> List[DockerService]:

        volumes = [create_config_mount(self.name)]

        if self.dev:
            volumes.append(create_dev_mount(self.name))

        ports = [f"{self.public_port}:{self.port}"]

        return [
            DockerService(
                name="rekuest", 
                image=self.image, 
                ports=ports, 
                volumes=volumes,  
                depends_on=["redis","db", "rabbitmq"],
                labels=[f"arkitekt.{setup.name}.service=rekuest"])
        ]




class HubConfig(BaseModel):
    lok: "LokDepend"
    


class HubService(BaseService):
    name: Literal["hub"]
    port: int = 8040
    public_port: int = 8040
    docker_network_name: str = "hub"


    def create_config(self, setup: "Setup") -> BaseModel:

        return None

    def create_fakt(self, setup: "Setup") -> Fakt:
        base = to_http_base(self.host, self.public_port, internal_port=self.port)
        ws_base = to_ws_base(self.host, self.public_port, internal_port=self.port)
        return RekuestFakt(
            base_url=f"{base}/o",
            endpoint_url=f"{base}/graphql",
            healthz=f"{base}/ht",
            agent=RekuestAgentFakt(endpoint_url=f"{ws_base}/agi"),
            ws_endpoint_url=f"{ws_base}/graphql"
        )
        

    def create_docker_services(self, setup: "Setup") -> List[DockerService]:


        volumes = [create_config_mount(self.name)]

        if self.dev:
            volumes.append(create_dev_mount(self.name))

        ports = [f"{self.public_port}:{self.port}"]

        return [
            DockerService(
                name="hub", 
                image=self.image, 
                ports=ports, 
                environment={
                    "DOCKER_NETWORK_NAME": self.docker_network_name,
                },
                volumes=volumes,  
                depends_on=["lok"],
                labels=[f"arkitekt.{setup.name}.service=hub"])
        ]




class Virtualizer(BaseModel):
    engine: str = "docker"
    network: str = "dev"
    allowed_runtimes: List[str] = Field(default_factory=lambda: ["nvidia", "runc", "wasm"])





class PortConfig(BaseModel):
    lok: "LokDepend"
    redis: RedisDepend
    django: DjangoConfig
    db: DbDepend
    virtualizer: Virtualizer
    minio: MinioDepend


class PortFakt(Fakt):
    base_url: str
    endpoint_url: str
    healthz: str
    ws_endpoint_url: str


class PortService(BaseService):
    name: Literal["port"]
    host: str = "port"
    port: int = 8050
    public_port: int = 8050
    network_name: Optional[str] = None
    required_buckets: List[Bucket] = Field(default_factory=lambda: [Bucket(name="portmedia")])
    required_policies: List[str] =  Field(default_factory=lambda: ["readwrite"])

    def create_config(self, setup: "Setup") -> BaseModel:

        return PortConfig(
            lok=self.dependencies["lok"],
            redis=self.dependencies["redis"],
            db=self.dependencies["db"],
            minio=self.dependencies["minio"],
            django=DjangoConfig(
                debug=self.dev is True,
                admin=AdminUser(
                    username=setup.admin_username,
                    email=setup.admin_email,
                    password=setup.admin_password,
                )
            ),
            virtualizer=Virtualizer(
                network=self.generate_network_name(setup),
            )    
        )

    def create_fakt(self, setup: "Setup") -> Fakt:
        
        base = to_http_base(self.host, self.public_port, internal_port=self.port)
        ws_base = to_ws_base(self.host, self.public_port, internal_port=self.port)
        return PortFakt(
            base_url=f"{base}/o",
            endpoint_url=f"{base}/graphql",
            healthz=f"{base}/ht",
            ws_endpoint_url=f"{ws_base}/graphql"
            
        )
    
    def generate_network_name(self, setup: "Setup") -> str:
        return self.network_name or f"{setup.name}"

    def create_docker_services(self, setup: "Setup") -> List[DockerService]:


        volumes = [create_config_mount(self.name), create_docker_mount()]

        if self.dev:
            volumes.append(create_dev_mount(self.name))

        ports = [f"{self.public_port}:{self.port}"]
        return [
            DockerService(
                name=self.host, 
                image=self.image, 
                ports=ports, 
                volumes=volumes,  
                network=[self.generate_network_name(setup)],
                depends_on=["lok","db", "redis"],
                labels=[f"arkitekt.{setup.name}.service=port"])
        ]
    





class FlussConfig(BaseModel):
    lok: "LokDepend"
    redis: RedisDepend
    django: DjangoConfig
    db: DbDepend
    minio: MinioDepend


class FlussFakt(Fakt):
    base_url: str
    endpoint_url: str
    healthz: str
    ws_endpoint_url: str
    


class FlussService(BucketNeedingService):
    name: Literal["fluss"]
    host: str = "fluss"
    port: int = 8070
    public_port: int = 8070
    image: str = "jhnnsrs:fluss/prod"
    required_buckets: List[Bucket] = Field(default_factory=lambda: [Bucket(name="flussmedia")])
    required_policies: List[str] =  Field(default_factory=lambda: ["readwrite"])

    def create_config(self, setup: "Setup") -> BaseModel:

        return FlussConfig(
            lok=self.dependencies["lok"],
            redis=self.dependencies["redis"],
            db=self.dependencies["db"],
            django=DjangoConfig(
                debug=self.dev is True,
                admin=AdminUser(
                    username=setup.admin_username,
                    email=setup.admin_email,
                    password=setup.admin_password,
                )
            ),
            minio=self.dependencies["minio"],
        )

    def create_fakt(self, setup: "Setup") -> Fakt:

        
        base = to_http_base(self.host, self.public_port, internal_port=self.port)
        ws_base = to_ws_base(self.host, self.public_port, internal_port=self.port)
        return FlussFakt(
            base_url=f"{base}/o",
            endpoint_url=f"{base}/graphql",
            healthz=f"{base}/ht",
            ws_endpoint_url=f"{ws_base}/graphql"
        )

    def create_docker_services(self, setup: "Setup") -> List[DockerService]:

        volumes = [create_config_mount(self.name)]

        if self.dev:
            volumes.append(create_dev_mount(self.name))


        ports = [f"{self.public_port}:{self.port}"]
        return [
            DockerService(
                name="fluss", 
                image=self.image, 
                ports=ports, 
                volumes=volumes,  
                depends_on=["redis","db"],
                labels=[f"arkitekt.{setup.name}.service=fluss"]
                )
        ]




class VscodeService(BaseService):
    name: Literal["vscode"]


class MikroConfig(BaseModel):
    lok: LokDepend
    minio: MinioDepend
    redis: RedisDepend 
    django: DjangoConfig
    db: DbDepend

class MikroFakt(BaseModel):
    base_url: str
    endpoint_url: str
    healthz: str
    ws_endpoint_url: str


class MikroService(BaseService):
    name: Literal["mikro"]
    required_buckets: List[Bucket] = Field(default_factory=lambda: [Bucket(name="zarr"), Bucket(name="parquet"), Bucket(name="mikromedia")])
    required_policies: List[str] =  Field(default_factory=lambda: ["readwrite"])

    host: str = "mikro"
    port: int = 8080
    public_port: int = 8080

    def create_config(self, setup: "Setup") -> BaseModel:

        return MikroConfig(
            lok=self.dependencies["lok"],
            redis=self.dependencies["redis"],
            minio=self.dependencies["minio"],
            db=self.dependencies["db"],
            django=DjangoConfig(
                debug=self.dev is True,
                admin=AdminUser(
                    username=setup.admin_username,
                    email=setup.admin_email,
                    password=setup.admin_password,
                )
            )
        )

    def create_fakt(self, setup: "Setup") -> Fakt:
        base = to_http_base(self.host, self.public_port, internal_port=self.port)
        ws_base = to_ws_base(self.host, self.public_port, internal_port=self.port)
        return MikroFakt(
            base_url=f"{base}/o",
            endpoint_url=f"{base}/graphql",
            healthz=f"{base}/ht",
            ws_endpoint_url=f"{ws_base}/graphql"
        )

    def create_docker_services(self, setup: "Setup") -> List[DockerService]:

        volumes = [create_config_mount(self.name)]

        if self.dev:
            volumes.append(create_dev_mount(self.name))

        ports = [f"{self.public_port}:{self.port}"]
        return [
            DockerService(
                name="mikro", 
                image=self.image, 
                ports=ports, 
                volumes=volumes,  
                depends_on=["redis","db", "minio"],
                labels=[f"arkitekt.{setup.name}.service=mikro"]
                )
        ]







Service = Union[RekuestService, HubService, MinioService, MikroService, RedisService, PostgresService, PortService, FlussService, VscodeService, LokService, RabbitMQService, OrkestratorService]


class Setup(BaseModel):
    name: str
    admin_username: str
    admin_email: EmailStr
    admin_password: str
    network: Optional[str] = None

    services: List[Service] = Field(default_factory=list)

    groups: List[Group] = Field(default_factory=list)
    users: List[User] = Field(default_factory=list)
    apps: List[App]  = Field(default_factory=list)

    
    @root_validator()
    def validate_loks_and_apps(cls, values):
        available_users = [user.username for user in values.get("users", [])]

        for app in values.get("apps", []):
            if app.tenant == values["admin_username"]:
                raise ValueError("App should not be hold by admin account")

            if app.tenant is None:
                assert len(available_users) > 0 , "You need to have at least one user installed"
                app.tenant = available_users[0]

            if app.tenant not in available_users:

                raise ValueError(f"{app} has unknown tenant dd are {available_users}")

        return values

    @root_validator()
    def validate_admin_not_in_loks(cls, values):
        available_users = [user.username for user in values.get("loks", [])]

        if values["admin_username"] in available_users:
            raise ValueError("Admin can't be a lok user")

        return values

    def to_yaml(self, path, dict):
        with open(path, "w") as f:
            yaml.dump(remove_none(json.loads(json.dumps(dict))), f)

    def resolve(self):
        os.makedirs("init/configs", exist_ok=True)

        for service in self.services:
            service.resolve(self)


    def generate_configs(self):
        os.makedirs("init/configs", exist_ok=True)
        
        for service in self.services:
            try:
                config = service.create_config(self)
            except Exception as e:
                raise Exception(f"Error configuring {service.name}") from e


            if config:
                self.to_yaml(f"init/configs/{service.name}.yaml", config.dict())

        
    def generate_fakts(self):
        os.makedirs("init/fakts/linkers", exist_ok=True)
        os.makedirs("init/fakts/templates", exist_ok=True)

        fakts = { service.name: service.create_fakt(self) for service in self.services}

        # TODO configure internal
        wrapped = {"self": {"name": "{{deployment_name}}"}}
        services = {key: value.dict() for key,value in fakts.items() if value is not None}
    
        wrapped.update(services)

        x = yaml.dump(remove_none(json.loads(json.dumps(wrapped))))
        raw_fakts =[service.create_raw_fakt(self) for service in self.services if service.create_raw_fakt(self) is not None]
        print(raw_fakts)
        for t in raw_fakts:
           x += t

        with open("init/fakts/templates/generic.yaml", "w") as f:
            f.write(x)


        linker = {
            "name": "Generic Linker",
            "template": "generic",
            "priority": 0,
            "filters": [{
                "method": "host_is_not",
                "value": "unallowed"
            }]
        }
        self.to_yaml(f"init/fakts/linkers/generic.yaml", linker)




    def generate_dirs(self):

        for service in self.services:
            service.create_dirs(self)

    def generate_dev(self):
        dev_services = [service for service in self.services if service.dev]

        if os.path.exists("init/dev"):
            shutil.rmtree("init/dev")
        if len(dev_services) > 0:
            os.makedirs("init/dev", exist_ok=True)

            for service in dev_services:
                service.create_dev(self)



    def create_docker_services(self) -> Dict :
        return {d.name: d.dict(exclude={"name"}) for d in itertools.chain(*(service.create_docker_services(self) for service in self.services))}

    def create_docker_volumes(self) -> Dict:
        return {d.name: d.dict(exclude={"name"}) for d in itertools.chain(*(service.create_docker_volumes(self) for service in self.services))}
    
    def create_networks(self) -> Dict:
        additional =  {d.name: d.dict(exclude={"name"}) for d in itertools.chain(*(service.create_docker_networks(self) for service in self.services))}
        additional.update({"default": {"name": self.name}})
        return additional
    

    def bake(self):

        self.resolve()
        self.generate_dirs()
        self.generate_configs()
        self.generate_fakts()
        self.generate_dev()


        docker_compose = DockerCompose(services=self.create_docker_services(), volumes=self.create_docker_volumes(), networks=self.create_networks()
            , secrets={})
        
        self.to_yaml("init/docker-compose.yaml", docker_compose.dict()) 

