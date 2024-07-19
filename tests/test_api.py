import pytest
from otf_api.api import Otf


@pytest.mark.asyncio
async def test_api_raises_error_if_no_username_password():
    with pytest.raises(TypeError):
        await Otf.create()
