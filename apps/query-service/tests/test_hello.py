"""Hello unit test module."""

from query_service.hello import hello


def test_hello():
    """Test the hello function."""
    assert hello() == "Hello query-service"
