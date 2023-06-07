import yaml
import json
from setup import Setup



    
if __name__ == "__main__":

    # t
    with open("init/setup.yaml", "r") as f:
        extended_config = yaml.load(f, yaml.BaseLoader)


    setup = Setup(**extended_config)


    print("Validating")
    with open("init/validated.yaml", "w") as f:
        yaml.safe_dump(json.loads(setup.json()), f)



    setup.bake()

    print("Sucessfully baked the project")



