from otf_api import models
from otf_api.api.booking_api import BookingApi
from otf_api.api.compat import LegacyCompatMixin
from otf_api.api.member_api import MemberApi
from otf_api.api.studio_api import StudioApi
from otf_api.api.workout_api import WorkoutApi
from otf_api.auth import OtfUser

from .client import OtfClient


class Otf(LegacyCompatMixin):
    """The main OTF API client.

    This class handles serialization and enrichment of data from the OTF API. The actual requests to the OTF API are\
    handled by separate client classes. This class provides methods to get bookings, classes, member details, and more.
    It also provides methods to book and cancel classes, get member stats, and manage favorite studios.

    It is designed to be used with an authenticated user, which can be provided as an `OtfUser` object. If no user is\
    provided, the `OtfClient` class will attempt to use cached credentials, environment variables, or prompt the user\
    for credentials.
    """

    def __init__(self, user: OtfUser | None = None):
        """Initialize the OTF API client.

        Args:
            user (OtfUser): The user to authenticate as.
        """
        client = OtfClient(user)

        self.bookings = BookingApi(self, client)
        self.members = MemberApi(self, client)
        self.workouts = WorkoutApi(self, client)
        self.studios = StudioApi(self, client)

        self.member_uuid = client.member_uuid
        self._member: models.MemberDetail | None = None

    @property
    def member(self) -> models.MemberDetail:
        """Get the member details.

        This will lazily load the member details if they have not been loaded yet.
        """
        if self._member is None:
            self._member = self.members.get_member_detail()
        return self._member

    @property
    def home_studio(self) -> models.StudioDetail:
        """Get the home studio details.

        This will lazily load the home studio details if they have not been loaded yet.
        """
        return self.member.home_studio

    @property
    def home_studio_uuid(self) -> str:
        """Get the home studio UUID.

        This will lazily load the home studio UUID if it has not been loaded yet.
        """
        return self.home_studio.studio_uuid

    def refresh_member(self) -> models.MemberDetail:
        """Refresh the member details.

        This will reload the member details from the OTF API.

        Returns:
            MemberDetail: The refreshed member details.
        """
        self._member = self.members.get_member_detail()
        return self._member
