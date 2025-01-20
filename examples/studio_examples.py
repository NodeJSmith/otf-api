from otf_api import Otf


def main():
    otf = Otf()

    # if you need to figure out what studios are in an area, you can call `search_studios_by_geo`
    # which takes latitude, longitude, distance, page_index, and page_size as arguments
    # but you'll generally just need the first 3
    # same as with classes, you can leave it blank and get the studios within 50 miles of your home studio
    studios_by_geo = otf.search_studios_by_geo()
    print(studios_by_geo[0].model_dump_json(indent=4))

    """
        {
            "studio_uuid": "c9e81931-6845-4ab5-ba06-6479d63553ae",
            "contact_email": "studioemailaddressexample@orangetheoryfitness.com",
            "distance": 0.0,
            "location": {
                "address_line1": "2835 N Sandbank Rd.",
                "address_line2": null,
                "city": "AnyTown",
                "postal_code": "11111",
                "state": "OH",
                "country": "United States",
                "phone_number": "1234567890",
                "latitude": 92.73407745,
                "longitude": 3.46269226
            },
            "name": "AnyTown OH - East",
            "status": "Active",
            "time_zone": "America/NewYork"
        }
    """

    # if you need to get detailed information about a studio, you can call `get_studio_detail`
    # which takes a studio_uuid as an argument, but you can leave it blank to get details about your home studio
    # the return type is also StudioDetail, so the same format as the above
    studio_detail = otf.get_studio_detail()
    print(studio_detail.model_dump_json(indent=4))

    """
        {
            "studio_uuid": "c9e81931-6845-4ab5-ba06-6479d63553ae",
            "contact_email": "studioemailaddressexample@orangetheoryfitness.com",
            "distance": 0.0,
            "location": {
                "address_line1": "2835 N Sandbank Rd.",
                "address_line2": null,
                "city": "AnyTown",
                "postal_code": "11111",
                "state": "OH",
                "country": "United States",
                "phone_number": "1234567890",
                "latitude": 92.73407745,
                "longitude": 3.46269226
            },
            "name": "AnyTown OH - East",
            "status": "Active",
            "time_zone": "America/NewYork"
        }
    """

    # you can get studio services, although I'm not sure if anyone would ever need this
    services = otf.get_studio_services(studio_detail.studio_uuid)
    for svc in services:
        print(svc.model_dump_json(indent=4))

        """
        {
            "service_uuid": "ded53a03-aa7c-4382-bdf8-d427002545ab",
            "name": "10 Session Pack - $199",
            "price": "199.0000",
            "qty": 10,
            "online_price": "199.0000",
            "tax_rate": "0.075000",
            "current": true,
            "is_deleted": false,
            "created_date": "2018-12-27T18:04:48Z",
            "updated_date": "2025-01-20T19:39:23Z"
        }

        """
        break

    # you can get you favorite studios and add/remove studios from your favorites
    # this returns a list of StudioDetail, so the same format as the above
    faves = otf.get_favorite_studios()
    if faves:
        print(faves[0].model_dump_json(indent=4))

    # you can add a studio to your favorites by calling `add_favorite_studio` with a studio_uuid
    otf.add_favorite_studio(otf.home_studio_uuid)

    # you can remove a studio from your favorites by calling `remove_favorite_studio` with a studio_uuid
    otf.remove_favorite_studio(otf.home_studio_uuid)


if __name__ == "__main__":
    main()
