# Usage

## Overview

To use the API, you need to create an instance of the `Otf` class, providing your email address and password. This will authenticate you with the API and allow you to make requests. When the `Otf` object is created it automatically grabs your member details and home studio, to simplify the process of making requests.

### Data

All of the endpoints return Pydantic models. The endpoints that return lists will generally be encapsulated in a list model, so that the top level data can still be dumped by Pydantic. For example, `get_workouts()` returns a `WorkoutList` which has a `workouts` attribute that contains the individual `Workout` items.

Below are some examples of how to use the API.

## Examples

### Get Upcoming Classes

```python
{% include "../examples/class_bookings_examples.py" %}

```


### Challenge Tracker Data

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
