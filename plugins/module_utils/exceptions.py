class StackroxApiException(Exception):
    pass

class BundleRevokeFailedException(StackroxApiException):
    def __init__(self, api_error_list):
        super().__init__(self, "Failed to revoke one or more init bundles")
        self.failed_bundles = api_error_list

class UnauthorizedException(StackroxApiException):
    pass
