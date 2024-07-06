import asyncio
import os
from collections import Counter

from otf_api import Api
from otf_api.models.responses.bookings import BookingStatus
from otf_api.models.responses.classes import ClassType

USERNAME = os.getenv("OTF_EMAIL")
PASSWORD = os.getenv("OTF_PASSWORD")


async def main():
    otf = await Api.create(USERNAME, PASSWORD)

    resp = await otf.get_member_purchases()
    print(resp.model_dump_json(indent=4))

    resp = await otf.get_bookings(start_date="2024-06-19", status=BookingStatus.LateCancelled)
    print(resp.model_dump_json(indent=4))

    studios = await otf.search_studios_by_geo(40.7831, 73.9712, distance=100)

    studio_uuids = [studio.studio_uuid for studio in studios.studios]

    # To get upcoming classes you can call the `get_classes` method
    # You can pass a list of studio_uuids or, if you want to get classes from your home studio, leave it empty
    # this also takes a start date, end date, and limit - these are not sent to the API, they are used in the
    # client to filter the results
    classes = await otf.get_classes(studio_uuids)

    # get all statuses
    class_types = dict(
        sorted(
            Counter([c.name for c in classes.classes if c.class_type == ClassType.OTHER]).items(),
            key=lambda x: x[1],
            reverse=True,
        )
    )

    print(class_types)

    print(classes.classes[0].model_dump_json(indent=4))

    """
    {
        "id": "0e39ef70-7403-49c1-8605-4a72643bd201",
        "ot_base_class_uuid": "08cebfdb-e127-48d4-8a7f-e6ea4dd85c18",
        "starts_at": "2024-06-13 10:00:00+00:00",
        "starts_at_local": "2024-06-13 05:00:00",
        "ends_at": "2024-06-13 11:00:00+00:00",
        "ends_at_local": "2024-06-13 06:00:00",
        "name": "Orange 3G",
        "type": "ORANGE_60",
        "studio": ...,
        "coach": ...,
        "max_capacity": 36,
        "booking_capacity": 36,
        "waitlist_size": 0,
        "full": false,
        "waitlist_available": false,
        "canceled": false,
        "mbo_class_id": "30809",
        "mbo_class_schedule_id": "2655",
        "mbo_class_description_id": "102",
        "created_at": "2024-05-14 10:33:32.406000+00:00",
        "updated_at": "2024-06-13 01:58:55.233000+00:00"
    }
    """

    # You can also get the classes that you have booked
    # You can pass a start_date, end_date, status, and limit as arguments

    bookings = await otf.get_bookings()
    print(bookings.bookings[0].model_dump_json(indent=4))


if __name__ == "__main__":
    asyncio.run(main())
