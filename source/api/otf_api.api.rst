OrangeTheory API
====================

.. py:class:: otf_api.api.api.Otf

    The main OTF API client.

    This class handles serialization and enrichment of data from the OTF API. The actual requests to the OTF API are\
    handled by separate client classes. This class provides methods to get bookings, classes, member details, and more.
    It also provides methods to book and cancel classes, get member stats, and manage favorite studios.

    It is designed to be used with an authenticated user, which can be provided as an `OtfUser` object. If no user is\
    provided, the `OtfClient` class will attempt to use cached credentials, environment variables, or prompt the user\
    for credentials.

   .. autoattribute:: bookings

      The interface to the bookings API, which allows you to search for classes and manage bookings.

   .. autoattribute:: members

        The interface to the members API, which allows you to get your member details, purchases, and services.
        There are also a few methods to update your information, such as your name and email/sms preferences.

   .. autoattribute:: studios

        The interface to the studios API, which allows you to get studio details and add/remove studios from your favorites.

   .. autoattribute:: workouts

        The interface to the workouts API, which allows you to get your workout history, challenge participation, heart
        rate data, etc.

   .. autoproperty:: member
   .. autoproperty:: home_studio
   .. autoproperty:: member_uuid
   .. autoproperty:: home_studio_uuid
   .. automethod:: refresh_member

.. toctree::
   :maxdepth: 3
   :hidden:

   otf_api.api.bookings
   otf_api.api.members
   otf_api.api.studios
   otf_api.api.workouts
