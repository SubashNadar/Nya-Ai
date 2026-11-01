"""Errors raised by services. app.main turns each into a JSON response with its status code."""


class ServiceError(Exception):
    status_code = 400

    def __init__(self, detail: str) -> None:
        super().__init__(detail)
        self.detail = detail


class BadRequest(ServiceError):
    status_code = 400


class Forbidden(ServiceError):
    status_code = 403


class NotFound(ServiceError):
    status_code = 404


class Invalid(ServiceError):
    status_code = 422


class BadGateway(ServiceError):
    status_code = 502


class Unavailable(ServiceError):
    status_code = 503
