
from typing import Dict, List, Optional
from pydantic import BaseModel, Field



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
    environment: Optional[Dict]
    depends_on: List[str] = Field(default_factory=list)





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

