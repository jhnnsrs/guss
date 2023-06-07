


def create_config_mount(service: str):
    return f"./configs/{service}.yaml:/workspace/config.yaml"

def create_fakts_mount():
    return f"./fakts:/workspace/fakts"


def create_dev_mount(service: str):
    return f"./dev/{service}:/workspace/"


def create_docker_mount():
    return f"/var/run/docker.sock:/var/run/docker.sock"


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
