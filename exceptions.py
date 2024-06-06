class ApmClientException(Exception):
    pass


class OktaClientException(Exception):
    pass


class InvalidTokenException(ApmClientException):
    pass


class UnhandledAircraftTypeException(Exception):
    pass
