import asyncio
import json
import os

from otf_api import Api

USERNAME = os.getenv("OTF_EMAIL")
PASSWORD = os.getenv("OTF_PASSWORD")


async def main():
    otf = await Api.create(USERNAME, PASSWORD)

    # To get upcoming classes you can call the `get_classes` method
    # You can pass a list of studio_uuids or, if you want to get classes from your home studio, leave it empty
    classes = await otf.classes_api.get_classes()
    print(json.dumps(classes.classes[0].model_dump(), indent=4, default=str))

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

    # if you need to figure out what studios are in an area, you can call `search_studios_by_geo`
    # which takes latitude, longitude, distance, page_index, and page_size as arguments
    # but you'll generally just need the first 3
    # same as with classes, you can leave it blank and get the studios within 50 miles of your home studio
    studios_by_geo = await otf.studios_api.search_studios_by_geo()
    print(json.dumps(studios_by_geo.studios[0].model_dump(), indent=4, default=str))

    """
    {
        "studio_id": 1297,
        "studio_uuid": "8645fb2b-ef66-4d9d-bda1-f508091ec891",
        "mbo_studio_id": 8612481,
        "studio_number": "05414",
        "studio_name": "AnyTown OH - East",
        "studio_physical_location_id": 494,
        "time_zone": "America/Chicago",
        "contact_email": "studiomanager05414@orangetheoryfitness.com",
        "studio_token": "ec2459b2-32b5-4b7e-9759-55270626925a",
        "environment": "PROD",
        "pricing_level": "",
        "tax_rate": "0.000000",
        "accepts_visa_master_card": true,
        "accepts_american_express": true,
        "accepts_discover": true,
        "accepts_ach": false,
        "is_integrated": true,
        "description": "",
        "studio_version": "",
        "studio_status": "Active",
        "open_date": "2017-01-13 00:00:00",
        "re_open_date": "2020-05-26 00:00:00",
        "studio_type_id": 2,
        "sms_package_enabled": false,
        "allows_dashboard_access": false,
        "allows_cr_waitlist": true,
        "cr_waitlist_flag_last_updated": "2020-07-09 02:43:55+00:00",
        "royalty_rate": 0,
        "marketing_fund_rate": 0,
        "commission_percent": 0,
        "is_mobile": null,
        "is_otbeat": null,
        "distance": 0.0,
        "studio_location": ...,
        "studio_location_localized": ...,
        "studio_profiles": {
            "is_web": true,
            "intro_capacity": 1,
            "is_crm": true
        },
        "social_media_links": ...
    }
    """

    # if you need to get detailed information about a studio, you can call `get_studio_detail`
    # which takes a studio_uuid as an argument, but you can leave it blank to get details about your home studio
    # this one has a result structure very much like the previous one
    studio_detail = await otf.studios_api.get_studio_detail()
    print(json.dumps(studio_detail.model_dump(), indent=4, default=str))


if __name__ == "__main__":
    asyncio.run(main())
