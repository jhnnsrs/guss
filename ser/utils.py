

from ser.setup import Setup


def create_config_mount(service: str):
    return f"./configs/{service}.yaml:/workspace/config.yaml"

def create_fakts_mount():
    return f"./fakts:/workspace/fakts"


def create_dev_mount(service: str, setup: Setup):
    if service in setup.dev_services:
        return f"./dev/{service}:/workspace/"
    return None


def create_docker_mount():
    return f"/var/run/docker.sock:/var/run/docker.sock"