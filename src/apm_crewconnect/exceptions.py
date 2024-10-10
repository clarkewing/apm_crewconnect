class ApmClientException(Exception):
    pass


class OktaClientException(Exception):
    pass


class InvalidAuthRedirectException(OktaClientException):
    pass


class InvalidTokenException(ApmClientException):
    pass


class UnhandledAircraftTypeException(Exception):
    pass


class UnknownActivityTypeException(Exception):
    pass
