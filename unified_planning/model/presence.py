class Presence:
    def __init__(self, container: str):
        self._container = container

    @property
    def container(self) -> str:
        return self._container

    def __eq__(self, other):
        if not isinstance(other, Presence):
            return False
        return self._container == other._container

    def __hash__(self):
        return hash(self._container)

    def __str__(self):
        return f"present({self._container})"

    def __repr__(self):
        return f"present({self._container})"
