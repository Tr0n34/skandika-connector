from box import Box
import yaml


def load_config(path='configuration/configuration.yml'):
    with open(path, 'r') as f:
        config_dict = yaml.safe_load(f)
    return Box(config_dict)
