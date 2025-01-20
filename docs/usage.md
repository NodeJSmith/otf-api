# Usage

## Overview

To use the API, you need to create an instance of the `Otf` class. This will authenticate you with the API and allow you to make requests. When the `Otf` object is created it automatically grabs your member details and home studio, to simplify the process of making requests.

You can either pass an `OtfUser` object to the `OtfClass` or you can pass nothing and allow it to prompt you for your username and password.

You can also export environment variables `OTF_EMAIL` and `OTF_PASSWORD` to get these from the environment.

```python
from otf_api import Otf, OtfUser

otf = Otf(user=OtfUser(<email_address>,<password>))

```

### Data
All of the endpoints return Pydantic models or lists of Pydantic models.

Below are some examples of how to use the API.

## Examples

### Get Upcoming Classes

```python
{% include "../examples/class_bookings_examples.py" %}

```

### Get Challenge Data

```python
{% include "../examples/challenge_tracker_examples.py" %}

```

### Get Workout Data

```python
{% include "../examples/workout_examples.py" %}

```

### Get Studio Data

```python
{% include "../examples/studio_examples.py" %}

```
