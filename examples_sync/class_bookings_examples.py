import os
from datetime import datetime
from getpass import getpass

from otf_api import OtfSync
from otf_api.models.classes import DoW

USERNAME = os.getenv("OTF_EMAIL") or input("Enter your OTF email: ")
PASSWORD = os.getenv("OTF_PASSWORD") or getpass("Enter your OTF password: ")


def main():
    with OtfSync(USERNAME, PASSWORD) as otf:
        resp = otf.get_bookings(start_date=datetime.today().date())
        print(resp.model_dump_json(indent=4))

        studios = otf.search_studios_by_geo(40.7831, 73.9712, distance=100)

        studio_uuids = [studio.studio_uuid for studio in studios.studios]

        # To get upcoming classes you can call the `get_classes` method
        # You can pass a list of studio_uuids or, if you want to get classes from your home studio, leave it empty
        # this also takes a start date, end date, and limit - these are not sent to the API, they are used in the
        # client to filter the results
        classes = otf.get_classes(studio_uuids, day_of_week=[DoW.TUESDAY, DoW.THURSDAY, DoW.SATURDAY])

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

        bookings = otf.get_bookings()

        print("Latest Upcoming Class:")
        print(bookings.bookings[-1].model_dump_json(indent=4))

        """
        {
            "class_booking_id": 870700285,
            "class_booking_uuid": "a36d76b1-0a55-4143-b96b-646e7520ca39",
            "studio_id": 1234,
            "class_id": 376344282,
            "is_intro": false,
            "member_id": 234488148,
            "status": "Booked",
            "booked_date": "2024-09-10T04:26:11Z",
            "checked_in_date": null,
            "cancelled_date": null,
            "created_date": "2024-09-10T04:26:11Z",
            "updated_date": "2024-09-10T04:26:13Z",
            "is_deleted": false,
            "waitlist_position": null,
            "otf_class": {
                "starts_at_local": "2024-09-28T10:30:00",
                "ends_at_local": "2024-09-28T11:20:00",
                "name": "Tread 50",
                "class_uuid": "82ec9b55-950a-484f-818f-cd2344ce83fd",
                "is_available": true,
                "is_cancelled": false,
                "program_name": "Group Fitness",
                "coach_id": 1204786,
                "studio": {
                    "studio_uuid": "49e360d1-f8ef-4091-a23f-61b321cb283c",
                    "studio_name": "AnyTown OH - East",
                    "description": "",
                    "status": "Active",
                    "time_zone": "America/Chicago",
                    "studio_id": 1267,
                    "allows_cr_waitlist": true
                },
                "coach": {
                    "coach_uuid": "973516a8-0c6b-41ec-916c-1da9913b9a16",
                    "name": "Friendly",
                    "first_name": "Friendly",
                    "last_name": "Coach"
                },
                "location": {
                    "address_one": "123 S Main St",
                    "address_two": null,
                    "city": "AnyTown",
                    "country": null,
                    "distance": null,
                    "latitude": 91.73407745,
                    "location_name": null,
                    "longitude": -80.92264626,
                    "phone_number": "2042348963",
                    "postal_code": "11111",
                    "state": "Ohio"
                },
                "virtual_class": null
            },
            "is_home_studio": true
        }
        """


if __name__ == "__main__":
    main()
