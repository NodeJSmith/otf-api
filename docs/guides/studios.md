# Studios

The studios API lets you search for OrangeTheory studios by location, get detailed studio
information, and manage your list of favorite studios. All studio operations are accessed
through `otf.studios`.

## Searching Studios by Location

Use `search_studios_by_geo` to find studios near a geographic location:

```python
# Search near your home studio (default)
studios = otf.studios.search_studios_by_geo()

# Search near specific coordinates
studios = otf.studios.search_studios_by_geo(
    latitude=39.7392,
    longitude=-104.9903,
)

# Adjust search radius (default is 50 miles)
studios = otf.studios.search_studios_by_geo(
    latitude=39.7392,
    longitude=-104.9903,
    distance=25,
)
```

Each result is a `StudioDetail` object containing the studio name, address, contact info,
status, and geographic coordinates.

!!! tip
    When called with no arguments, `search_studios_by_geo` uses your home studio's
    coordinates and returns studios within 50 miles.

## Getting Studio Details

Retrieve detailed information about a specific studio:

```python
# Your home studio (default)
studio = otf.studios.get_studio_detail()

# A specific studio by UUID
studio = otf.studios.get_studio_detail("c9e81931-6845-4ab5-ba06-6479d63553ae")

print(f"Name: {studio.name}")
print(f"Email: {studio.contact_email}")
print(f"Address: {studio.location.address_line1}, {studio.location.city}")
print(f"Status: {studio.status}")
print(f"Time Zone: {studio.time_zone}")
```

!!! note
    If a studio UUID does not exist, `get_studio_detail` returns a placeholder object with
    `name="Studio Not Found"` and `status="Unknown"` rather than raising an exception. This
    allows downstream code to continue without null checks.

## Studio Services

View pricing and service packages available at a studio:

```python
services = otf.studios.get_studio_services()

for svc in services:
    print(f"{svc.name} - ${svc.price} (qty: {svc.qty})")
```

Pass a `studio_uuid` argument to check services at a different studio. Defaults to your
home studio.

## Managing Favorites

Add and remove studios from your favorites list:

```python
# Get your current favorites
favorites = otf.studios.get_favorite_studios()
for studio in favorites:
    print(f"  {studio.name}")

# Add a studio to favorites
otf.studios.add_favorite_studio("c9e81931-6845-4ab5-ba06-6479d63553ae")

# Add multiple studios at once
otf.studios.add_favorite_studio(["uuid-1", "uuid-2"])

# Remove a studio from favorites
otf.studios.remove_favorite_studio("c9e81931-6845-4ab5-ba06-6479d63553ae")
```

!!! tip
    Your home studio UUID is accessible via `otf.home_studio_uuid`, making it easy to
    add your home studio to favorites:
    ```python
    otf.studios.add_favorite_studio(otf.home_studio_uuid)
    ```
