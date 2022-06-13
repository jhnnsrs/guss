import itertools
from typing import Dict, List, Optional, Type
from pydantic import BaseModel, Field, SecretStr
import yaml
from jwcrypto import jwk
import secrets
import string
from ser.baker import Baker
from ser.services.arkitekt import ArkitektServiceFactory
from ser.services.fluss import FlussServiceFactory
from ser.services.herre import HerreServiceFactory
from ser.services.hub import HubServiceFactory
from ser.services.mikro import MikroServiceFactory
from ser.services.port import PortServiceFactory
from ser.services.shared import SharedServiceFactory

from ser.setup import Setup



    
if __name__ == "__main__":

    
    with open("init/setup.yaml", "r") as f:
        extended_config = yaml.load(f, yaml.BaseLoader)


    setup = Setup(**extended_config)

    baker = Baker()
    baker.register_factory("mikro", MikroServiceFactory)
    baker.register_factory("arkitekt", ArkitektServiceFactory)
    baker.register_factory("fluss", FlussServiceFactory)
    baker.register_factory("herre", HerreServiceFactory)
    baker.register_factory("port", PortServiceFactory)
    baker.register_factory("hub", HubServiceFactory)
    baker.register_factory("shared", SharedServiceFactory)
    baker.init(setup)

    baker.bake()
    print("Sucessfully baked the project")



