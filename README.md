Simple API client for interacting with the OrangeTheory Fitness APIs.

Review the [documentation](https://otf-api.readthedocs.io/en/stable/).


This library allows access to the OrangeTheory API to retrieve workouts and performance data, class schedules, studio information, and bookings.

## Installation
```bash
pip install otf-api
```

## Overview

To use the API, you need to create an instance of the `Otf` class, providing your email address and password. This will authenticate you with the API and allow you to make requests. When the `Otf` object is created it automatically grabs your member details and home studio, to simplify the process of making requests.


See the [examples](./examples) for more information on how to use the API.

Disclaimer:
This project is in no way affiliated with OrangeTheory Fitness.
