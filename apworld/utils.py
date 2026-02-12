import pkgutil
import json

from . import __name__ as package_name

def load_json(path: str):
    raw = pkgutil.get_data(package_name, path)
    if raw is None:
        raise FileNotFoundError(path)
    return json.loads(raw.decode("utf-8"))