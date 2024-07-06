Simple API client for interacting with the OrangeTheory Fitness APIs.


This library allows access to the OrangeTheory API to retrieve workouts and performance data, class schedules, studio information, and bookings. It is a work in progress, currently only allowing access to GET calls, but my goal is to expand it to include POST, PUT, and DELETE calls as well.

## Installation
```bash
pip install otf-api
```

## Overview

To use the API, you need to create an instance of the `Api` class, providing your email address and password. This will authenticate you with the API and allow you to make requests. When the `Api` object is created it automatically grabs your member details and home studio, to simplify the process of making requests.


See the [examples](./examples) for more information on how to use the API.

Disclaimer:
This project is in no way affiliated with OrangeTheory Fitness.
