from typing import List
from pydantic import BaseModel
from ser.docker import DockerService, DockerVolume
from ser.setup import Setup


class ServiceFactory:
    name: str = "U"

    def __init__(self, setup: Setup) -> None:
        self.setup = setup

    def create_dirs(self):
        pass


    def create_fakt(self, host):
        return None
    
    def create_config(self) -> BaseModel:
        """Also the place for validation

        Raises:
            NotImplementedError: _description_

        Returns:
            BaseModel: _description_
        """
        raise NotImplementedError()

    def create_docker_services(self) -> List[DockerService]:
        return []

    def create_docker_volumes(self) -> List[DockerVolume]:
        return []


