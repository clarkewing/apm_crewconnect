import sys

sys.path.append("./src")

import json
from typing import Optional

from apm_crewconnect.interfaces import TokenManagerInterface


class FileTokenManager(TokenManagerInterface):
    def __init__(self, path=".storage/tokens.json") -> None:
        self.path = path
        self._retrieve()

    def set(self, **kwargs) -> None:
        if "key" in kwargs:
            self._tokens[kwargs["key"]] = kwargs["value"]
        else:
            self._tokens = kwargs["value"]

        self._store()

    def get(self, key: Optional[str] = None) -> dict[str, str | int] | None:
        if key == None:
            return self._tokens

        return self._tokens.get(key)

    def has(self, key: str) -> bool:
        return self.get(key) != None

    def _store(self) -> None:
        with open(self.path, "w+") as file:
            file.write(json.dumps(self._tokens))

    def _retrieve(self) -> None:
        try:
            with open(self.path, "r") as file:
                self._tokens = json.loads(file.read())
        except (FileNotFoundError, json.JSONDecodeError):
            self._tokens = {}
