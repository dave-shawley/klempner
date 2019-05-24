import os
import unittest
try:
    import unittest.mock as mock
except ImportError:
    import mock


class EnvironmentMixin(unittest.TestCase):
    """Mix this in to safely manipulate environment variables.

    This mix-in provides methods to manipulate environment variables
    within the test case and restore the original environment in
    ``tearDown``.

    """

    def setUp(self):
        super(EnvironmentMixin, self).setUp()
        self.__environment = {}

    def tearDown(self):
        super(EnvironmentMixin, self).tearDown()
        for name, value in self.__environment.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value

    def setenv(self, name, value):
        """Set the environment variable named `name` to `value`."""
        self.__environment.setdefault(name, os.environ.get(name, None))
        os.environ[name] = value

    def unsetenv(self, name):
        """Clear the environment variable named `name`."""
        self.__environment.setdefault(name, os.environ.get(name, None))
        os.environ.pop(name, None)


class Interceptor(mock.Mock):
    """Mock that intercepts a specific method call and tracks the result.

    This is useful when you want to capture the return value from an
    internal function.  The initial use case was to capture the request
    that was prepared inside of requests.  It turns out that this is
    the easiest way to see exactly which headers are sent short of
    creating a subclass of requests.Session for this purpose.

    This class overwrites `obj.method_name` with itself and uses the
    ``_interceptor`` method as a side effect.  Inside of ``_interceptor``
    it captures the result of calling the original method in ``self.result``
    and returns it.  The outcome is invisible to the inner workings of
    ``obj``, you can inspect the call using the standard mock methods,
    and interrogate the intermediate result as ``self.result``.

    """

    def __init__(self, obj, method_name, *args, **kwargs):
        kwargs['side_effect'] = self._interceptor
        super(Interceptor, self).__init__(*args, **kwargs)
        self.method_name = method_name
        self.obj = obj
        self.result = None
        setattr(obj, method_name, self)

    def _interceptor(self, *args, **kwargs):
        real_method = getattr(self.obj.__class__, self.method_name)
        self.result = real_method(self.obj, *args, **kwargs)
        return self.result

    def _get_child_mock(self, **kwargs):
        # Needed to override this since we do not want to intercept
        # anything for child mocks
        if self._mock_sealed:
            attribute = "." + kwargs["name"] if "name" in kwargs else "()"
            mock_name = self._extract_mock_name() + attribute
            raise AttributeError(mock_name)
        return mock.Mock(**kwargs)
