"""Application-level errors with safe client messages."""


class AppError(Exception):
    status_code = 400


class AuthenticationError(AppError):
    status_code = 401


class AuthorizationError(AppError):
    status_code = 403


class NotFoundError(AppError):
    status_code = 404


class ConfirmationError(AppError):
    status_code = 400


class ConfirmationExpired(ConfirmationError):
    pass


class ConfirmationReplay(ConfirmationError):
    pass


class ConfirmationBindingMismatch(ConfirmationError):
    status_code = 403


class OfflineSendBlocked(AuthorizationError):
    pass


class PreviewIntegrationError(AppError):
    status_code = 503

