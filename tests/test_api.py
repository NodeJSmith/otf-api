import pytest

from otf_api.api import Otf


def test_api_raises_error_if_no_username_password():
    with pytest.raises(ValueError):
        Otf()

