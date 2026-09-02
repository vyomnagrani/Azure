from .errors import AuthorizationError
from .models import Operation


class OperationPolicy:
    def __init__(self, allowed: frozenset[Operation]):
        self._allowed = allowed

    def require(self, operation: Operation) -> None:
        if operation not in self._allowed:
            raise AuthorizationError(f"operation '{operation.value}' is not allowed")

