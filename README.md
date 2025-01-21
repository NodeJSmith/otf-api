Simple API client for interacting with the OrangeTheory Fitness APIs.

Review the [documentation](https://otf-api.readthedocs.io/en/stable/).


This library allows access to the OrangeTheory API to retrieve workouts and performance data, class schedules, studio information, and bookings.

## Installation
```bash
pip install otf-api
```

## Overview

To use the API, you need to create an instance of the `Otf` class. This will authenticate you with the API and allow you to make requests. When the `Otf` object is created it automatically grabs your member details and home studio, to simplify the process of making requests.

You can either pass an `OtfUser` object to the `OtfClass` or you can pass nothing and allow it to prompt you for your username and password.

You can also export environment variables `OTF_EMAIL` and `OTF_PASSWORD` to get these from the environment.

```python
from otf_api import Otf, OtfUser

otf = Otf()

# OR

otf = Otf(user=OtfUser(<email_address>,<password>))

```
