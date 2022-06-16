
import itertools
import json
import os
import shutil

import yaml

from ser.docker import DockerCompose
from .factories import ServiceFactory
from .setup import Setup
from typing import Dict, Type
from git import Repo



def guard_empty(obj):
    return not ((obj is None) or (isinstance(obj, (dict, list, tuple, set)) and len(obj) == 0))


def remove_none(obj):
  if isinstance(obj, (list, tuple, set)):
    return type(obj)(remove_none(x) for x in obj if guard_empty(x))
  elif isinstance(obj, dict):
    return type(obj)((k, remove_none(v))
      for k, v in obj.items() if k and guard_empty(v))
  else:
    return obj




class Baker:

    def __init__(self):
        self.factoryClasses = {}

    def register_factory(self, name, service: Type[ServiceFactory]):
        self.factoryClasses[name] = service

    def init(self, setup: Setup):
        self.setup = setup
        self.factories = {name: factory(setup) for name, factory in self.factoryClasses.items() if name in setup.services}


    def to_yaml(self, path, dict):
        with open(path, "w") as f:
            yaml.dump(remove_none(json.loads(json.dumps(dict))), f)

    def generate_configs(self):
        os.makedirs("init/configs", exist_ok=True)

        for service_name, factory in self.factories.items():
            config = factory.create_config()

            if config:
                self.to_yaml(f"init/configs/{service_name}.yaml", config.dict())

    def generate_fakts(self):
        os.makedirs("init/fakts", exist_ok=True)

        fakts = { service_name: factory.create_fakt(service_name) for service_name, factory in self.factories.items()}

        wrapped = {"info": {"name": "internal", "host": "herre"}, "services": {key: value.dict() for key,value in fakts.items() if value is not None}}
        self.to_yaml(f"init/fakts/internal.yaml", wrapped)


        for host in self.setup.hosts:
            fakts = { service_name: factory.create_fakt(host) for service_name, factory in self.factories.items()}

            wrapped = {"info": {"name": host, "host": host}, "services": {key: value.dict() for key,value in fakts.items() if value is not None}}
            self.to_yaml(f"init/fakts/{host}.yaml", wrapped) 




    def generate_dirs(self):
        os.makedirs("init/data", exist_ok=True)

        for service_name, factory in self.factories.items():
            config = factory.create_dirs()

    def generate_dev(self):
        if os.path.exists("init/dev"):
            shutil.rmtree("init/dev")
        if len(self.setup.dev_services) > 0:
            os.makedirs("init/dev", exist_ok=True)

            for key, value in self.setup.dev_services.items():
                Repo.clone_from(value, f"init/dev/{key}")


    def create_docker_services(self) -> Dict :
        return {d.name: d.dict(exclude={"name"}) for d in itertools.chain(*(service.create_docker_services() for service in self.factories.values()))}

    def create_docker_volumes(self) -> Dict:
        return {d.name: d.dict(exclude={"name"}) for d in itertools.chain(*(service.create_docker_volumes() for service in self.factories.values()))}

    def bake(self):

        self.generate_dirs()
        self.generate_configs()
        self.generate_fakts()
        self.generate_dev()

        docker_compose = DockerCompose(services=self.create_docker_services(), volumes=self.create_docker_volumes(), networks={}, secrets={})

        self.to_yaml("init/docker-compose.yaml", docker_compose.dict()) 



