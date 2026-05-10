# Changelog

## [0.19.0](https://github.com/NodeJSmith/otf-api/compare/otf-api-v0.18.0...otf-api-v0.19.0) (2026-05-10)


### ⚠ BREAKING CHANGES

* cancel_booking no longer accepts BookingV2 objects and cancel_booking_new no longer accepts Booking objects.

### Code Refactoring

* comprehensive code quality cleanup from WTF audit ([#130](https://github.com/NodeJSmith/otf-api/issues/130)) ([2271881](https://github.com/NodeJSmith/otf-api/commit/227188160e4226aa3fb8786104d4d28ba2c06b2b))

## [0.18.0](https://github.com/NodeJSmith/otf-api/compare/otf-api-v0.17.0...otf-api-v0.18.0) (2026-05-10)


### ⚠ BREAKING CHANGES

* TotalBodyWeight renamed to TotalBodyWater, total_body_weight field renamed to total_body_water, total_body_weight_details renamed to total_body_water_details, OutsideSchedulingWindowError now inherits from BookingError instead of OtfError

### Documentation

* complete documentation overhaul with MkDocs-Material ([#127](https://github.com/NodeJSmith/otf-api/issues/127)) ([daef89e](https://github.com/NodeJSmith/otf-api/commit/daef89ededff7a6d59d1d42a24afbd0983f08136))

## [0.17.0](https://github.com/NodeJSmith/otf-api/compare/otf-api-v0.16.0...otf-api-v0.17.0) (2026-05-09)


### Features

* add diagnostic logging for silent failures and empty API responses ([#119](https://github.com/NodeJSmith/otf-api/issues/119)) ([bc4e853](https://github.com/NodeJSmith/otf-api/commit/bc4e853e5a08cf5b7f0ed48924f505e625296e34))
* **bookings:** detect waitlisted V2 bookings via waitlist_position field ([#125](https://github.com/NodeJSmith/otf-api/issues/125)) ([461b517](https://github.com/NodeJSmith/otf-api/commit/461b517658cb9661a3acf5769b1e61f91631a003))


### Bug Fixes

* cancel_booking crash on BookingV2 and missing class_uuid in get_workout_from_booking ([#124](https://github.com/NodeJSmith/otf-api/issues/124)) ([f525d1a](https://github.com/NodeJSmith/otf-api/commit/f525d1a1defb3e7c454c87a98e8e267471d9f0ce))

## [0.16.0](https://github.com/NodeJSmith/otf-api/compare/otf-api-v0.15.4...otf-api-v0.16.0) (2026-04-28)


### ⚠ BREAKING CHANGES

* removed deprecated flat methods on Otf class (e.g., otf.book_class()). Use the domain-scoped API instead (e.g., otf.bookings.book_class()).

### Features

* add field validators and relative descriptor properties to BodyCompositionData ([0c1b489](https://github.com/NodeJSmith/otf-api/commit/0c1b4898eb52cd9066c8926160af27534cc6f352))
* add PII anonymization pipeline with real-time capture mode ([#109](https://github.com/NodeJSmith/otf-api/issues/109)) ([c2c381e](https://github.com/NodeJSmith/otf-api/commit/c2c381ec02bb5975f3fde7356b726c9683467fd4))
* **api.py, auth.py:** add refresh callback functionality to handle token refresh events ([e4dacc2](https://github.com/NodeJSmith/otf-api/commit/e4dacc270285254f97a74ea28972d8bf029841ba))
* **api.py:** add exclude_checkedin parameter to get_bookings method to filter out checked-in bookings ([d7fcf32](https://github.com/NodeJSmith/otf-api/commit/d7fcf32f029b1939636a86d7dfa2527f20f1b3c5))
* **api.py:** add filtering by day of week and start time for class retrieval ([96d20e0](https://github.com/NodeJSmith/otf-api/commit/96d20e0fc8db0e6565ac5e77af6f5bcf650c0610))
* **api.py:** add home_studio_uuid parameter to Otf class for better user context management ([f03b6a5](https://github.com/NodeJSmith/otf-api/commit/f03b6a5f9b135e6334f9cb5a94334b0d98eb5014))
* **api.py:** add hydrate method to Otf class to create instances from a dictionary ([8577ad1](https://github.com/NodeJSmith/otf-api/commit/8577ad154a1e46764a422ddc0478abdd15d0719b))
* **api.py:** add logging and print statement when starting background token refresh task ([12b6f9f](https://github.com/NodeJSmith/otf-api/commit/12b6f9fed343db8974237728e63829a3a81fc068))
* **api.py:** add main function to initialize Otf instance using env vars ([c1d9315](https://github.com/NodeJSmith/otf-api/commit/c1d931555e6b6e96018e0235c972e766ad2ab3fe))
* **api.py:** add methods to get booking by class and booking UUID for better booking management ([6094072](https://github.com/NodeJSmith/otf-api/commit/60940725a8c6c6501934b8230128d9c26b2004f0))
* **api.py:** add new exceptions for booking errors to improve error handling ([6094072](https://github.com/NodeJSmith/otf-api/commit/60940725a8c6c6501934b8230128d9c26b2004f0))
* **api.py:** add optional device_key parameter to hydrate method to allow more flexible instantiation ([c5e2560](https://github.com/NodeJSmith/otf-api/commit/c5e25605eb2b3f2beba8b5929fc9a221c71801f0))
* **api.py:** add print statement to debug background task for refreshing token ([a8f04ac](https://github.com/NodeJSmith/otf-api/commit/a8f04acb39255d297f9d7cc41f56ed0cc28890c9))
* **api.py:** add retry logic to _get_performance_summary_raw to handle intermittent None responses ([82e9fb0](https://github.com/NodeJSmith/otf-api/commit/82e9fb0bbb6730b3a7e24caa86b9fc9f8f6ec29c))
* **api.py:** add support for refresh_token and device_key in Otf class initialization ([04c4294](https://github.com/NodeJSmith/otf-api/commit/04c429468f45a9023c3c9cae2fe595f63d7d88cd))
* **api.py:** add support for token-based authentication and background token refresh ([554e968](https://github.com/NodeJSmith/otf-api/commit/554e96847fff851193f1a1cf5dce5640d4733aef))
* **api.py:** add support for user object and refresh callback in Otf class ([a081fe2](https://github.com/NodeJSmith/otf-api/commit/a081fe2c38c738c1be6d7015d3b2be264e5c44ac))
* **api.py:** add user parameter to Otf class constructor to allow passing a user object ([7508b09](https://github.com/NodeJSmith/otf-api/commit/7508b09c1aa33fe5d138874557db65c805210847))
* **api.py:** enhance class booking and cancellation with additional checks and error handling ([6094072](https://github.com/NodeJSmith/otf-api/commit/60940725a8c6c6501934b8230128d9c26b2004f0))
* **api.py:** extend Api.create method to support token-based authentication ([85185eb](https://github.com/NodeJSmith/otf-api/commit/85185eb5d62ae37dbb443c90b362524126b00541))
* **api:** add class and coach rating functionality ([1032df1](https://github.com/NodeJSmith/otf-api/commit/1032df1ca0e050617361a9bc1d427fc60a100499))
* **api:** implement async context manager methods in Otf class to automatically handle session lifecycle ([ed4f287](https://github.com/NodeJSmith/otf-api/commit/ed4f2877d5792e3ba97339daa373edb16410f4f0))
* **api:** implement get_studios_by_geo as alias for search_studios_by_geo ([ed4f287](https://github.com/NodeJSmith/otf-api/commit/ed4f2877d5792e3ba97339daa373edb16410f4f0))
* **auth.py, user.py:** add has_cached_credentials method to check for cached credentials ([ed4f287](https://github.com/NodeJSmith/otf-api/commit/ed4f2877d5792e3ba97339daa373edb16410f4f0))
* **auth.py:** add check_token method to verify and optionally renew access tokens ([30faeb6](https://github.com/NodeJSmith/otf-api/commit/30faeb6267a0bb1850798785badf8bc501437fdd))
* **auth.py:** add class methods for creating OtfCognito instances from tokens and login credentials ([80a64ac](https://github.com/NodeJSmith/otf-api/commit/80a64ac567cdcc7a0e42dbc36884ed6acabea0f1))
* **auth.py:** add device key support to OtfCognito class for enhanced security ([a938c06](https://github.com/NodeJSmith/otf-api/commit/a938c062ffe63cbb6ad1be291538ae32bfa4b69e))
* **auth.py:** add koji_person_id field to IdClaimsData model to include custom identifier ([0c1b489](https://github.com/NodeJSmith/otf-api/commit/0c1b4898eb52cd9066c8926160af27534cc6f352))
* **auth.py:** add logging for token refresh to improve debugging and monitoring ([1192201](https://github.com/NodeJSmith/otf-api/commit/11922017384864e6c33c9d2034ad789e6f031441))
* **auth.py:** add logging to track token refresh process ([63c2199](https://github.com/NodeJSmith/otf-api/commit/63c21997bbefc7ef5f59b805aea6d6534467e31a))
* **auth.py:** add logging when clearing device key to improve traceability ([101f195](https://github.com/NodeJSmith/otf-api/commit/101f195c7329a4850d22046b84b7a5dd1cf7f578))
* **auth.py:** add method to create User instance from an id token ([554e968](https://github.com/NodeJSmith/otf-api/commit/554e96847fff851193f1a1cf5dce5640d4733aef))
* **auth.py:** add methods to check and retrieve username from cache file ([4647b55](https://github.com/NodeJSmith/otf-api/commit/4647b55790487cda66d641de1aa497e58f917813))
* **auth.py:** add model_config to OtfUser to allow arbitrary types in pydantic model ([11d3869](https://github.com/NodeJSmith/otf-api/commit/11d38691334b855f3f74ddcb0f8943557579e55d))
* **auth.py:** add OtfCognito class to handle device metadata and token renewal ([9e9de81](https://github.com/NodeJSmith/otf-api/commit/9e9de81ff7b08a91118d1e887acd2498b8dd193f))
* **auth.py:** add property and setter for device_key with logging for security ([1538fec](https://github.com/NodeJSmith/otf-api/commit/1538fecc50dfc47366dc96857da5bc6d9e6d8d8a))
* **auth.py:** add validation for refresh_callback to ensure it is a callable function with one argument ([15a4dd4](https://github.com/NodeJSmith/otf-api/commit/15a4dd41e4a2eb1af055555523fa021e55d010a0))
* **auth:** add get_tokens method to OtfUser class to retrieve tokens ([c520e39](https://github.com/NodeJSmith/otf-api/commit/c520e392dc2f219182cdeacd20cde222be4ffbac))
* **base.py:** add item getter methods to OtfBaseModel for flexible key access ([0282e67](https://github.com/NodeJSmith/otf-api/commit/0282e674898a8bd49b3f99e3053c975b484372af))
* **bookings.py:** add book and cancel commands to manage class bookings ([b0f9f70](https://github.com/NodeJSmith/otf-api/commit/b0f9f70886d93ebb94709b25b06d748417c86455))
* **bookings.py:** add BookingStatusCli enum for CLI-friendly booking statuses ([0282e67](https://github.com/NodeJSmith/otf-api/commit/0282e674898a8bd49b3f99e3053c975b484372af))
* **bookings.py:** add interactive booking cancellation feature to improve user experience ([5095e6b](https://github.com/NodeJSmith/otf-api/commit/5095e6bd340ad19fbf2bdf1e4f093d217b5f9fd3))
* **bookings.py:** add interactive booking options for studio UUIDs, date range, class type, day of week, and start time ([96d20e0](https://github.com/NodeJSmith/otf-api/commit/96d20e0fc8db0e6565ac5e77af6f5bcf650c0610))
* **bookings.py:** integrate OtfClassTimeMixin into OtfClass for time-related properties ([0282e67](https://github.com/NodeJSmith/otf-api/commit/0282e674898a8bd49b3f99e3053c975b484372af))
* **bookings.py:** update BookingList to include new class time columns ([0282e67](https://github.com/NodeJSmith/otf-api/commit/0282e674898a8bd49b3f99e3053c975b484372af))
* **bookings:** add methods to BookingStatus and StudioStatus enums for case-insensitive lookups and listing all statuses ([4647b55](https://github.com/NodeJSmith/otf-api/commit/4647b55790487cda66d641de1aa497e58f917813))
* **bookings:** add to_table method to BookingList for rich table representation ([4647b55](https://github.com/NodeJSmith/otf-api/commit/4647b55790487cda66d641de1aa497e58f917813))
* **cancel_booking:** add new response model for cancel booking ([195e4da](https://github.com/NodeJSmith/otf-api/commit/195e4da97cfb9f2ae0e9f0e5387ddaa784e1d014))
* **classes_api:** add class_type and exclude_cancelled filters to get_classes method ([ffc1cee](https://github.com/NodeJSmith/otf-api/commit/ffc1cee14e664ae97b45bbea3d9d8ce7d0888640))
* **classes_api:** add filtering by date range and limit to get_classes method ([76a358a](https://github.com/NodeJSmith/otf-api/commit/76a358a8a43ef40d70713d30d6effa3dc8ec2bbe))
* **classes_api:** integrate booking status to mark classes as booked ([ffc1cee](https://github.com/NodeJSmith/otf-api/commit/ffc1cee14e664ae97b45bbea3d9d8ce7d0888640))
* **classes.py:** add ClassType and ClassTypeCli enums for class type management ([0282e67](https://github.com/NodeJSmith/otf-api/commit/0282e674898a8bd49b3f99e3053c975b484372af))
* **classes.py:** add DoW enum for day of week filtering and case-insensitive matching ([96d20e0](https://github.com/NodeJSmith/otf-api/commit/96d20e0fc8db0e6565ac5e77af6f5bcf650c0610))
* **classes.py:** add OtfClassTimeMixin for time-related properties in OtfClass ([0282e67](https://github.com/NodeJSmith/otf-api/commit/0282e674898a8bd49b3f99e3053c975b484372af))
* **classes.py:** enhance OtfClass with sidebar data and availability properties ([0282e67](https://github.com/NodeJSmith/otf-api/commit/0282e674898a8bd49b3f99e3053c975b484372af))
* **classes.py:** update OtfClassList to include new class time columns ([0282e67](https://github.com/NodeJSmith/otf-api/commit/0282e674898a8bd49b3f99e3053c975b484372af))
* **classes:** add class_name to sidebar_data in OtfClass ([0c1b489](https://github.com/NodeJSmith/otf-api/commit/0c1b4898eb52cd9066c8926160af27534cc6f352))
* **classes:** add table representation for class list ([195e4da](https://github.com/NodeJSmith/otf-api/commit/195e4da97cfb9f2ae0e9f0e5387ddaa784e1d014))
* **cli:** add bookings command to list booking data ([3bf547b](https://github.com/NodeJSmith/otf-api/commit/3bf547b8f1bf87303d7886d6b8b568a9161e00c0))
* **cli:** add classes command to CLI for listing classes ([76a358a](https://github.com/NodeJSmith/otf-api/commit/76a358a8a43ef40d70713d30d6effa3dc8ec2bbe))
* **cli:** add exclude_cancelled option to list_bookings command ([b1de127](https://github.com/NodeJSmith/otf-api/commit/b1de1276233eff0a8ba87ea31ed95c38ba3b7bff))
* **cli:** add interactive booking command to book classes interactively ([b1de127](https://github.com/NodeJSmith/otf-api/commit/b1de1276233eff0a8ba87ea31ed95c38ba3b7bff))
* **cli:** add prompts module for user input and selection ([b1de127](https://github.com/NodeJSmith/otf-api/commit/b1de1276233eff0a8ba87ea31ed95c38ba3b7bff))
* **cli:** add utility functions for CLI exception handling and async support ([3bf547b](https://github.com/NodeJSmith/otf-api/commit/3bf547b8f1bf87303d7886d6b8b568a9161e00c0))
* **cli:** implement CLI structure with AsyncTyper and command handling ([3bf547b](https://github.com/NodeJSmith/otf-api/commit/3bf547b8f1bf87303d7886d6b8b568a9161e00c0))
* **deps:** add httpx version 0.27.0 for HTTP requests ([b7f8f91](https://github.com/NodeJSmith/otf-api/commit/b7f8f9197679c9095aadd4f2a5ea4bba56e35ef2))
* **examples:** add class bookings example script to demonstrate API usage ([292c987](https://github.com/NodeJSmith/otf-api/commit/292c987ffedae9104952de66cd1c0009a7c22956))
* **examples:** add favorite studio management to studio_examples.py ([ed4f287](https://github.com/NodeJSmith/otf-api/commit/ed4f2877d5792e3ba97339daa373edb16410f4f0))
* **exceptions.py:** add original_exception attribute to OtfRequestError for better error context ([e3cb63a](https://github.com/NodeJSmith/otf-api/commit/e3cb63ad02c79dec83f8cc22be67a469139a414c))
* **exceptions.py:** introduce ConflictingBookingError to handle booking conflicts ([ed4f287](https://github.com/NodeJSmith/otf-api/commit/ed4f2877d5792e3ba97339daa373edb16410f4f0))
* **filters.py:** add filter_classes method to ClassFilter to encapsulate filtering logic and enhance reusability ([ed4f287](https://github.com/NodeJSmith/otf-api/commit/ed4f2877d5792e3ba97339daa373edb16410f4f0))
* **lifetime_stats.py:** add new model for lifetime statistics response ([0c1b489](https://github.com/NodeJSmith/otf-api/commit/0c1b4898eb52cd9066c8926160af27534cc6f352))
* **member_api.py:** add book_class and cancel_booking methods to handle booking operations ([b0f9f70](https://github.com/NodeJSmith/otf-api/commit/b0f9f70886d93ebb94709b25b06d748417c86455))
* **member_api:** add exclude_cancelled parameter to filter out cancelled bookings ([60366bc](https://github.com/NodeJSmith/otf-api/commit/60366bcb86764da273536306641e41816c28e072))
* **member_detail.py:** add MemberReferrer class to handle member referrer data ([1f8e2d2](https://github.com/NodeJSmith/otf-api/commit/1f8e2d2f164cb30be731a6cda057d9bf59ce78fa))
* **models:** add _columns method to BookingList for table headers ([0c1b489](https://github.com/NodeJSmith/otf-api/commit/0c1b4898eb52cd9066c8926160af27534cc6f352))
* **models:** add attr_to_column_header method to OtfClass and Booking classes for dynamic column header mapping ([2376c94](https://github.com/NodeJSmith/otf-api/commit/2376c94eb51a9cff2cbf79df0feee1cbdd2d5369))
* **models:** add BetterDumperMixin for enhanced Pydantic model dumping ([812bf72](https://github.com/NodeJSmith/otf-api/commit/812bf72bfb042f8848d61e95e347964ef6e8c505))
* **models:** add BodyCompositionData model to handle body composition responses ([0c1b489](https://github.com/NodeJSmith/otf-api/commit/0c1b4898eb52cd9066c8926160af27534cc6f352))
* **models:** add book_class response models to handle booking data ([195e4da](https://github.com/NodeJSmith/otf-api/commit/195e4da97cfb9f2ae0e9f0e5387ddaa784e1d014))
* **models:** add BookClass and CancelBooking to response models ([195e4da](https://github.com/NodeJSmith/otf-api/commit/195e4da97cfb9f2ae0e9f0e5387ddaa784e1d014))
* **models:** add new Pydantic models for handling booking and client data ([195e4da](https://github.com/NodeJSmith/otf-api/commit/195e4da97cfb9f2ae0e9f0e5387ddaa784e1d014))
* **models:** add properties to Booking for id_val and sidebar_data ([0c1b489](https://github.com/NodeJSmith/otf-api/commit/0c1b4898eb52cd9066c8926160af27534cc6f352))
* **models:** add Telemetry model to handle telemetry data ([63feb5f](https://github.com/NodeJSmith/otf-api/commit/63feb5f9109a5af06f5716a2aab011e0fa3b755c))
* **models:** start updating models to handle missing data, exclude data, remove unnecessary sub models ([d671bc2](https://github.com/NodeJSmith/otf-api/commit/d671bc2c39c32058e26421b9208ccd31e3bfe5ec))
* **otf_api:** introduce OtfSync class for synchronous API interactions ([ed4f287](https://github.com/NodeJSmith/otf-api/commit/ed4f2877d5792e3ba97339daa373edb16410f4f0))
* **pyproject.toml:** add CLI script entry point for otf_api ([3bf547b](https://github.com/NodeJSmith/otf-api/commit/3bf547b8f1bf87303d7886d6b8b568a9161e00c0))
* **pyproject.toml:** add new development dependencies for testing and code quality ([b55df47](https://github.com/NodeJSmith/otf-api/commit/b55df47fe825a9e1fac253f463667e7caf535765))
* **pyproject.toml:** add pint library to dependencies for unit conversion functionality ([2569dbc](https://github.com/NodeJSmith/otf-api/commit/2569dbcdaf99e0899c808e75904985f1c5df132a))
* **pyproject.toml:** add python-box and inflection dependencies to enhance functionality ([06c2980](https://github.com/NodeJSmith/otf-api/commit/06c29804ba949162a695fb997d18c036552d7bdd))
* **pyproject.toml:** add readchar and humanize dependencies for enhanced CLI functionality ([dd6ab5b](https://github.com/NodeJSmith/otf-api/commit/dd6ab5b36ccd0ab8d3f8ba4f9210cefb3f0da481))
* **pyproject.toml:** add typer and pendulum dependencies for CLI support ([06a11d6](https://github.com/NodeJSmith/otf-api/commit/06a11d66520237e543bfddf69090f98fb1ae78dd))
* **pyproject.toml:** update aiohttp from 3.8.6 to 3.10.5 to work with Python 3.11+ ([fed9073](https://github.com/NodeJSmith/otf-api/commit/fed9073a3789b24217b0b7bc3c8073b0e571036d))
* **python_package.yml:** add create-release job to automate GitHub release creation after publishing to PyPI ([2b481b6](https://github.com/NodeJSmith/otf-api/commit/2b481b63fa6ab8040e8d0b325008989874db787e))
* **tox.ini:** add pipx install poetry in commands_pre to ensure poetry is installed ([eefb5b3](https://github.com/NodeJSmith/otf-api/commit/eefb5b3320f658550b0c7a353fda2ecdc8dbb059))
* **utils.py:** enable environment variable support for username and password to facilitate automated authentication ([ed4f287](https://github.com/NodeJSmith/otf-api/commit/ed4f2877d5792e3ba97339daa373edb16410f4f0))


### Bug Fixes

* **api.py:** add **kwargs to API request methods to allow additional parameters ([308e9c5](https://github.com/NodeJSmith/otf-api/commit/308e9c5b203d052853aad6a0aa6057a4156263a7))
* **api.py:** add check for session attribute before attempting to close it ([84faff4](https://github.com/NodeJSmith/otf-api/commit/84faff488527bb7c09ce2c0c34693adc1012e86d))
* **api.py:** add hasattr check for _refresh_task in shutdown method to prevent attribute error ([264fc8a](https://github.com/NodeJSmith/otf-api/commit/264fc8a2a7467a9108488bc59683ef6f7bd2fdfd))
* **api.py:** add synchronous member details retrieval to avoid async initialization issues ([04c4294](https://github.com/NodeJSmith/otf-api/commit/04c429468f45a9023c3c9cae2fe595f63d7d88cd))
* **api.py:** allow multiple class types for class retrieval ([96d20e0](https://github.com/NodeJSmith/otf-api/commit/96d20e0fc8db0e6565ac5e77af6f5bcf650c0610))
* **api.py:** change User method from load_from_disk to login for clarity ([84faff4](https://github.com/NodeJSmith/otf-api/commit/84faff488527bb7c09ce2c0c34693adc1012e86d))
* **api.py:** clear cache after rating a class to ensure updated data is returned ([2fb5b3c](https://github.com/NodeJSmith/otf-api/commit/2fb5b3cb58589e42430f890d1fbe2e35c1061744))
* **api.py:** deprecate limit argument in get_performance_summaries to simplify API ([2fb5b3c](https://github.com/NodeJSmith/otf-api/commit/2fb5b3cb58589e42430f890d1fbe2e35c1061744))
* **api.py:** enhance error message to include provided authentication kwargs ([ecae909](https://github.com/NodeJSmith/otf-api/commit/ecae9094f2b30b0791f8fc28f5dcfe7dd061fea7))
* **api.py:** ensure distance does not exceed 250 miles in _get_studios_by_geo to adhere to API constraints ([ed4f287](https://github.com/NodeJSmith/otf-api/commit/ed4f2877d5792e3ba97339daa373edb16410f4f0))
* **api.py:** improve error handling by logging response text on exceptions ([308e9c5](https://github.com/NodeJSmith/otf-api/commit/308e9c5b203d052853aad6a0aa6057a4156263a7))
* **api.py:** initialize _ref attribute to None to avoid potential attribute errors ([82baf91](https://github.com/NodeJSmith/otf-api/commit/82baf91c0bdf54390d9208adef7133810a2d0602))
* **api.py:** initialize aiohttp.ClientSession with authorization headers to ensure authenticated requests ([d7fcf32](https://github.com/NodeJSmith/otf-api/commit/d7fcf32f029b1939636a86d7dfa2527f20f1b3c5))
* **api.py:** update type hints and docstrings for consistency and clarity ([2fb5b3c](https://github.com/NodeJSmith/otf-api/commit/2fb5b3cb58589e42430f890d1fbe2e35c1061744))
* **api.py:** wrap signal handling in try-except block to prevent crashes on unsupported platforms ([b55df47](https://github.com/NodeJSmith/otf-api/commit/b55df47fe825a9e1fac253f463667e7caf535765))
* **api:** correct page size limit in search_studios_by_geo to 100 ([ed4f287](https://github.com/NodeJSmith/otf-api/commit/ed4f2877d5792e3ba97339daa373edb16410f4f0))
* **api:** update telemetry method to use performance_summary_id instead of class_history_uuid ([a1ce303](https://github.com/NodeJSmith/otf-api/commit/a1ce3031ed0d390b550f554769b43bbbdc66caa4))
* **auth.py:** add check for existing device key before clearing to avoid unnecessary log entries ([e131c66](https://github.com/NodeJSmith/otf-api/commit/e131c6629025e096114bb0530fe4d8fab7148ef4))
* **auth.py:** add token verification to ensure tokens are valid before creating User instance ([0690fef](https://github.com/NodeJSmith/otf-api/commit/0690fef7c377acd285474344c51e6d04c82e8fda))
* **auth.py:** add type annotations and return types to check_token method for better clarity and type safety ([80a64ac](https://github.com/NodeJSmith/otf-api/commit/80a64ac567cdcc7a0e42dbc36884ed6acabea0f1))
* **auth.py:** change log level from debug to info for token refresh message ([a8f04ac](https://github.com/NodeJSmith/otf-api/commit/a8f04acb39255d297f9d7cc41f56ed0cc28890c9))
* **auth.py:** change refresh_token method to return a boolean indicating success ([a081fe2](https://github.com/NodeJSmith/otf-api/commit/a081fe2c38c738c1be6d7015d3b2be264e5c44ac))
* **auth.py:** correct attribute name from device_metadata to device_key for token generation ([2f9bc99](https://github.com/NodeJSmith/otf-api/commit/2f9bc992f565f7c824410fc20cf568df891ae6d9))
* **auth.py:** ensure refresh callback is called after token refresh ([e4dacc2](https://github.com/NodeJSmith/otf-api/commit/e4dacc270285254f97a74ea28972d8bf029841ba))
* **auth.py:** ensure token properties return values from cognito if available ([ed4f287](https://github.com/NodeJSmith/otf-api/commit/ed4f2877d5792e3ba97339daa373edb16410f4f0))
* **auth.py:** handle TokenVerificationException during access token renewal ([a938c06](https://github.com/NodeJSmith/otf-api/commit/a938c062ffe63cbb6ad1be291538ae32bfa4b69e))
* **auth.py:** move background refresh task to OtfUser class to ensure token refresh logic is encapsulated within the user class ([15a4dd4](https://github.com/NodeJSmith/otf-api/commit/15a4dd41e4a2eb1af055555523fa021e55d010a0))
* **auth.py:** move token refresh log message to correct location and ensure save_to_disk is called only when tokens are refreshed ([f23865e](https://github.com/NodeJSmith/otf-api/commit/f23865ef9b22a3c66ecc3bc9bc9c63d30b53065c))
* **auth.py:** remove optional parameters from load_from_disk method to ensure username and password are always provided for reauthentication ([907f626](https://github.com/NodeJSmith/otf-api/commit/907f6264b7b30c3364f55c7c20a59c0f3aee082e))
* **auth.py:** remove redundant hasattr check before clearing device key ([764a715](https://github.com/NodeJSmith/otf-api/commit/764a715f3e767f586d62eebd5be762eba1b14294))
* **auth.py:** update device_key property to handle None type values ([2503728](https://github.com/NodeJSmith/otf-api/commit/2503728cff9ce7ce252be1d673a2413cdb1a87c2))
* **auth:** update type hints from Cognito to OtfCognito for consistency ([ed4f287](https://github.com/NodeJSmith/otf-api/commit/ed4f2877d5792e3ba97339daa373edb16410f4f0))
* **body_composition_list.py:** remove empty line to make linter happy ([26f1a47](https://github.com/NodeJSmith/otf-api/commit/26f1a476be9eb9b70c2bec1484492db99a554a00))
* **body_composition_list.py:** update member_id type to accept both str and int ([ed4f287](https://github.com/NodeJSmith/otf-api/commit/ed4f2877d5792e3ba97339daa373edb16410f4f0))
* **bookings.py:** make description field optional in Studio model to handle cases where description might be missing ([bba0d5e](https://github.com/NodeJSmith/otf-api/commit/bba0d5eb6b365ff25df288cb14cd913271c29b38))
* **classes_api:** correct variable name from res to classes_resp for clarity ([ffc1cee](https://github.com/NodeJSmith/otf-api/commit/ffc1cee14e664ae97b45bbea3d9d8ce7d0888640))
* **classes.py:** remove usage of Self type hint for compatibility with older Python versions ([d08c643](https://github.com/NodeJSmith/otf-api/commit/d08c64305c99e72bf51d77923bee4b55894181c7))
* **classes.py:** return DoW instead of string from day_of_week_enum ([194f1ff](https://github.com/NodeJSmith/otf-api/commit/194f1ffeeb036370d0eeae9446497ecafcfbbd73))
* **classes:** change "90 min" to "90 minutes" for consistency ([0c1b489](https://github.com/NodeJSmith/otf-api/commit/0c1b4898eb52cd9066c8926160af27534cc6f352))
* **cli:** add help descriptions for book and cancel options ([ce2bccc](https://github.com/NodeJSmith/otf-api/commit/ce2bcccea65f135eb90392dcf8d40444f7d2d7a0))
* **cli:** add missing envvar for OPT_OUTPUT option in app.py ([ce2bccc](https://github.com/NodeJSmith/otf-api/commit/ce2bcccea65f135eb90392dcf8d40444f7d2d7a0))
* **cli:** correct columns method calls in bookings and classes ([ce2bccc](https://github.com/NodeJSmith/otf-api/commit/ce2bcccea65f135eb90392dcf8d40444f7d2d7a0))
* **cliff.toml:** add default value for commit_id to handle undefined cases ([ab5cbdc](https://github.com/NodeJSmith/otf-api/commit/ab5cbdcbd5d77903ab73ad594cf63d5a8281bff0))
* **cliff.toml:** ensure commit_id is present before adding unreleased ([9d2cca5](https://github.com/NodeJSmith/otf-api/commit/9d2cca50adc7690632c83f840a1f93ec7dc7ab63))
* **cli:** remove unused kwargs in list_bookings and list_classes ([ce2bccc](https://github.com/NodeJSmith/otf-api/commit/ce2bcccea65f135eb90392dcf8d40444f7d2d7a0))
* **cli:** update command aliases to name in bookings and classes ([ce2bccc](https://github.com/NodeJSmith/otf-api/commit/ce2bcccea65f135eb90392dcf8d40444f7d2d7a0))
* correct import paths for User and Otf classes ([0ffb313](https://github.com/NodeJSmith/otf-api/commit/0ffb3132172dec639fe7ae9de5eb3579933aeaca))
* **dependencies:** change aiohttp version to 3.8.* for better compatibility ([9845822](https://github.com/NodeJSmith/otf-api/commit/984582231afe8e32016fc69e0640a01ccca354d7))
* **enums.py:** change EquipmentType and ChallengeType to use IntEnum for better integer handling ([ed4f287](https://github.com/NodeJSmith/otf-api/commit/ed4f2877d5792e3ba97339daa373edb16410f4f0))
* **examples:** correct instantiation of `Otf` class in examples to remove async creation method ([3adcd6c](https://github.com/NodeJSmith/otf-api/commit/3adcd6cdda37d9b89ea51d6eddd2be389dd261dc))
* **exceptions:** add specific exceptions for rating errors ([1032df1](https://github.com/NodeJSmith/otf-api/commit/1032df1ca0e050617361a9bc1d427fc60a100499))
* fix the thing i just broke, use .parent ([7c44ac8](https://github.com/NodeJSmith/otf-api/commit/7c44ac83388d5b1df64760d011d63350706f73fb))
* **gen_ref_pages.py:** skip files named __version__ in documentation generation ([4332db8](https://github.com/NodeJSmith/otf-api/commit/4332db86bc74a8bf8162d654660e80cf9739b2bf))
* **imports:** update all references to User to OtfUser to match new class name ([c520e39](https://github.com/NodeJSmith/otf-api/commit/c520e392dc2f219182cdeacd20cde222be4ffbac))
* mask strictness passes through non-PII primitive and structural values ([#112](https://github.com/NodeJSmith/otf-api/issues/112)) ([b57c93b](https://github.com/NodeJSmith/otf-api/commit/b57c93bde0d15fd07c71e70237f27a003a5825b2))
* **member_api:** update sorting key to use starts_at_local instead of start_date_time ([60366bc](https://github.com/NodeJSmith/otf-api/commit/60366bcb86764da273536306641e41816c28e072))
* **member_detail.py:** allow for no homePhone ([7568833](https://github.com/NodeJSmith/otf-api/commit/7568833b08489b87850b577106e6fe4e31297324))
* **member_detail.py:** correct member_address_uuid field to handle None values and unify alias handling ([0c1b489](https://github.com/NodeJSmith/otf-api/commit/0c1b4898eb52cd9066c8926160af27534cc6f352))
* **mixins:** make address_line1 optional in AddressMixin for flexibility ([ed4f287](https://github.com/NodeJSmith/otf-api/commit/ed4f2877d5792e3ba97339daa373edb16410f4f0))
* **models/base.py:** change model_config extra from "forbid" to "allow" to permit additional fields ([2c96d37](https://github.com/NodeJSmith/otf-api/commit/2c96d37bac2d3f0644fff456636dea1dc51f5f3c))
* **models:** exclude sensitive fields from API responses for better security and privacy ([4647b55](https://github.com/NodeJSmith/otf-api/commit/4647b55790487cda66d641de1aa497e58f917813))
* **models:** make created_by and updated_by fields optional ([0c1b489](https://github.com/NodeJSmith/otf-api/commit/0c1b4898eb52cd9066c8926160af27534cc6f352))
* **models:** update __init__.py to include missing imports and reorder ([c1d9315](https://github.com/NodeJSmith/otf-api/commit/c1d931555e6b6e96018e0235c972e766ad2ab3fe))
* **models:** update imports and __all__ to reflect Telemetry changes ([63feb5f](https://github.com/NodeJSmith/otf-api/commit/63feb5f9109a5af06f5716a2aab011e0fa3b755c))
* pass the correct object to models to use in api calls ([80ac6ef](https://github.com/NodeJSmith/otf-api/commit/80ac6efe3eed159b61f5d5dbcbc2a45dd6371448))
* **performance_summary_detail.py:** exclude and hide ratable field due to inaccuracy in reflecting data from PerformanceSummaryEntry ([e48b8b5](https://github.com/NodeJSmith/otf-api/commit/e48b8b57afa6e4b32090cfb529dde2920853139d))
* **performance_summary_list.py:** add type field to Class model ([02d9a08](https://github.com/NodeJSmith/otf-api/commit/02d9a08df310d1c57d5c5874b02e4204acebee59))
* **prompts.py:** handle empty data list in prompt_select_from_table function ([812bf72](https://github.com/NodeJSmith/otf-api/commit/812bf72bfb042f8848d61e95e347964ef6e8c505))
* **prompts.py:** highlight already booked classes in grey in selection table ([96d20e0](https://github.com/NodeJSmith/otf-api/commit/96d20e0fc8db0e6565ac5e77af6f5bcf650c0610))
* **pyproject.toml:** correct typo in pytest configuration section header ([062eb3d](https://github.com/NodeJSmith/otf-api/commit/062eb3da9cec19f347b52526dfaed23b923630f3))
* **pyproject.toml:** pin griffe &lt; 1 to fix mkdocs build ([06ad79d](https://github.com/NodeJSmith/otf-api/commit/06ad79d10236e99afc8ad6261b8d16fcf7fd7dfd))
* **pyproject.toml:** reorder dependencies alphabetically for better readability ([b55df47](https://github.com/NodeJSmith/otf-api/commit/b55df47fe825a9e1fac253f463667e7caf535765))
* **responses:** update __init__.py to include missing imports and reorder ([c1d9315](https://github.com/NodeJSmith/otf-api/commit/c1d931555e6b6e96018e0235c972e766ad2ab3fe))
* **telemetry.py:** add rowData fields to Telemetry model ([74e72f4](https://github.com/NodeJSmith/otf-api/commit/74e72f40be02b51ca431474cb91879bc45c0d6ab))
* **telemetry.py:** allow for no `hr` data in telemetry ([823d57b](https://github.com/NodeJSmith/otf-api/commit/823d57bf0131f1bd47b4fa60a652757374a52e54))
* **telemetry.py:** lowercase `row_spm` ([d54beb4](https://github.com/NodeJSmith/otf-api/commit/d54beb4b259244fa29013bebae40162bde74fd99))
* **tox.ini:** add poetry install command to ensure dev dependencies are installed before running checks ([3f6957f](https://github.com/NodeJSmith/otf-api/commit/3f6957f7cb2cdaa5dbea703d84d39cc64f786b30))
* **tox.ini:** replace poetry with pipx in deps to manage dependencies ([eefb5b3](https://github.com/NodeJSmith/otf-api/commit/eefb5b3320f658550b0c7a353fda2ecdc8dbb059))
* update CLIENT_ID value from newest apk ([f9f3495](https://github.com/NodeJSmith/otf-api/commit/f9f34955aae8d6237231da2c72aba22da9731a8f))
* use correct attribute for cache directory ([eb1356b](https://github.com/NodeJSmith/otf-api/commit/eb1356b9394e1997974fe924c5ed9e5206073dbb))
* use correct attribute for cache directory ([89f5f87](https://github.com/NodeJSmith/otf-api/commit/89f5f874d59ee659b1061c996f6b955bd3b68fa8))
* **workout_examples.py:** remove duplicate assignment of otf variable to prevent redundancy ([1f8e2d2](https://github.com/NodeJSmith/otf-api/commit/1f8e2d2f164cb30be731a6cda057d9bf59ce78fa))


### Performance Improvements

* **api.py:** cache _get_performance_summary_raw to improve performance by reducing redundant API calls ([82e9fb0](https://github.com/NodeJSmith/otf-api/commit/82e9fb0bbb6730b3a7e24caa86b9fc9f8f6ec29c))
* **api.py:** use ThreadPoolExecutor for concurrent fetching of studio and performance summary details ([2fb5b3c](https://github.com/NodeJSmith/otf-api/commit/2fb5b3cb58589e42430f890d1fbe2e35c1061744))


### Documentation

* **api.py, auth.py:** simplify and clarify the description of refresh_callback parameter in docstrings ([afe8959](https://github.com/NodeJSmith/otf-api/commit/afe8959393f56418417853bbe87ba8917ccf1513))
* **api.py:** add docstring to Api.create method to describe new parameters and return type ([85185eb](https://github.com/NodeJSmith/otf-api/commit/85185eb5d62ae37dbb443c90b362524126b00541))
* **api.py:** update docstrings to include home_studio_uuid parameter and new methods ([f03b6a5](https://github.com/NodeJSmith/otf-api/commit/f03b6a5f9b135e6334f9cb5a94334b0d98eb5014))
* **auth_examples:** remove outdated comments related to cache_device_data option ([ed4f287](https://github.com/NodeJSmith/otf-api/commit/ed4f2877d5792e3ba97339daa373edb16410f4f0))
* **auth.py:** update docstrings to reflect changes in token handling and device key usage ([a938c06](https://github.com/NodeJSmith/otf-api/commit/a938c062ffe63cbb6ad1be291538ae32bfa4b69e))
* **auth:** update __all__ to reflect the renamed OtfUser class ([c520e39](https://github.com/NodeJSmith/otf-api/commit/c520e392dc2f219182cdeacd20cde222be4ffbac))
* **CONTRIBUTING.md:** update reference from HISTORY.md to CHANGELOG.md ([d6ca531](https://github.com/NodeJSmith/otf-api/commit/d6ca531d9617f9d99ef08ce60f8943051b15b485))
* **examples:** add example for rating a class ([1032df1](https://github.com/NodeJSmith/otf-api/commit/1032df1ca0e050617361a9bc1d427fc60a100499))
* **examples:** update workout examples to reflect new API methods ([ed4f287](https://github.com/NodeJSmith/otf-api/commit/ed4f2877d5792e3ba97339daa373edb16410f4f0))
* **index.md:** fix include-markdown path to correctly reference usage.md ([d456660](https://github.com/NodeJSmith/otf-api/commit/d4566607dadf111674d6c6b33da00bac2167d7e3))
* **index.md:** replace README.md include with detailed API client description and installation instructions ([082e065](https://github.com/NodeJSmith/otf-api/commit/082e065f075d03e78a2614855e2b720784c1cd2c))
* **mkdocs.yml:** rename 'History' to 'Changelog' for clarity ([435da88](https://github.com/NodeJSmith/otf-api/commit/435da881e41985ff143c2679d107fcc60d12f31d))
* **mkdocs.yml:** update email contact ([435da88](https://github.com/NodeJSmith/otf-api/commit/435da881e41985ff143c2679d107fcc60d12f31d))
* **pyproject.toml:** add documentation URL to project metadata ([062eb3d](https://github.com/NodeJSmith/otf-api/commit/062eb3da9cec19f347b52526dfaed23b923630f3))
* **README.md, pyproject.toml:** update documentation link to stable version ([0139146](https://github.com/NodeJSmith/otf-api/commit/0139146817551fe91320b26ca9f1972a3ec19bb0))
* **README.md, usage.md:** update class name from `Api` to `Otf` for accuracy ([3adcd6c](https://github.com/NodeJSmith/otf-api/commit/3adcd6cdda37d9b89ea51d6eddd2be389dd261dc))
* **README.md:** expand documentation with installation, usage, and examples ([603df75](https://github.com/NodeJSmith/otf-api/commit/603df755934b984de15ec5c71640ca681a35ee61))
* **README.md:** remove extra blank line before disclaimer ([c52a8dd](https://github.com/NodeJSmith/otf-api/commit/c52a8dd08a37b4d90b4639f7b04af4f2335d6d97))
* **README.md:** remove extra blank line before disclaimer ([082e065](https://github.com/NodeJSmith/otf-api/commit/082e065f075d03e78a2614855e2b720784c1cd2c))
* **README.md:** remove outdated information about future goals for API methods ([4b82b38](https://github.com/NodeJSmith/otf-api/commit/4b82b385f0bcea880515cf6446a10b2af892655a))
* **README.md:** replace usage include with overview section and exam… ([de16962](https://github.com/NodeJSmith/otf-api/commit/de16962392da6536378c951bfba244ca36cb4b6d))
* **README.md:** replace usage include with overview section and examples link to provide better guidance on using the API ([2d9390d](https://github.com/NodeJSmith/otf-api/commit/2d9390d84256b4476277a2623708a87118c5feb2))
* remove installation guide from documentation and mkdocs navigation ([0139146](https://github.com/NodeJSmith/otf-api/commit/0139146817551fe91320b26ca9f1972a3ec19bb0))
* rename history.md to changelog.md and update references ([d6ca531](https://github.com/NodeJSmith/otf-api/commit/d6ca531d9617f9d99ef08ce60f8943051b15b485))
* update example scripts to use Otf class instead of Api ([0ffb313](https://github.com/NodeJSmith/otf-api/commit/0ffb3132172dec639fe7ae9de5eb3579933aeaca))
* **workflows:** correct typos in package download URLs in dev and release workflows ([a60c055](https://github.com/NodeJSmith/otf-api/commit/a60c05507b7cd75e0377042e6898c883f368e2f5))


### Code Refactoring

* codebase audit fixes — bugs, legacy removal, model cleanup ([#115](https://github.com/NodeJSmith/otf-api/issues/115)) ([f5d587f](https://github.com/NodeJSmith/otf-api/commit/f5d587f52e1b48420ea2d1d5d7e31756a9f831ca))
