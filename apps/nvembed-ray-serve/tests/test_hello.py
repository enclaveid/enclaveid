"""Hello unit test module."""

from nvembed_ray_serve.hello import hello


def test_hello():
    """Test the hello function."""
    assert hello() == "Hello nvembed-ray-serve"
