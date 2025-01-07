"""Hello unit test module."""

from python_api.hello import hello


def test_hello():
    """Test the hello function."""
    assert hello() == "Hello python-api"
