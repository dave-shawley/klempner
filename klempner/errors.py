class KlempnerError(Exception):
    """Library root exception class."""
    pass


class ServiceNotFoundError(KlempnerError):
    """Requested service was not found."""

    def __init__(self, service_name, *args, **kwargs):
        self.service_name = service_name
        super(ServiceNotFoundError, self).__init__(service_name, *args,
                                                   **kwargs)
