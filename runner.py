from module.api import ovalAPI
from pathlib import Path

if __name__ == "__main__":
    path = Path(__file__).parent.absolute()
    api = ovalAPI(path)

    api.load()
    api.convert()
    api.save()