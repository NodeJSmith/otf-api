from importlib.metadata import PackageNotFoundError, version  # pragma: no cover

from . import classes_api, member_api, studios_api, telemetry_api
from .api import Api
from .models.auth import User

try:
    # Change here if project is renamed and does not equal the package name
    dist_name = __name__
    __version__ = version(dist_name)
except PackageNotFoundError:  # pragma: no cover
    __version__ = "unknown"
finally:
    del version, PackageNotFoundError


__all__ = ["Api", "User", "classes_api", "member_api", "studios_api", "telemetry_api"]
