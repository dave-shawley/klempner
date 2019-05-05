class KlempnerError(Exception):
    """Library root exception class."""
    pass


class ServiceNotFoundError(KlempnerError):
    """Requested service was not found."""

    def __init__(self, service_name, *args, **kwargs):
        self.service_name = service_name
        super(ServiceNotFoundError, self).__init__(service_name, *args,
                                                   **kwargs)


class ConfigurationError(KlempnerError):
    """Configuration is invalid."""

    def __init__(self, config_option, config_value, *args):
        self.configuration_name = config_option
        self.configuration_value = config_value
        super(ConfigurationError, self).__init__(config_option, config_value,
                                                 *args)
