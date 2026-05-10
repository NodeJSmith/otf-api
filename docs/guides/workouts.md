# Workouts & Stats

The workouts API provides access to your complete workout history, including performance
summaries, heart rate telemetry, treadmill and rower data, and lifetime statistics. All
workout operations are accessed through `otf.workouts`.

## Getting Workout History

Use `get_workouts` to retrieve your workout history. Each `Workout` object contains the
same rich data shown in the OTF app after a class.

```python
# Last 30 days (default)
workouts = otf.workouts.get_workouts()

# Custom date range
workouts = otf.workouts.get_workouts(
    start_date="2025-01-01",
    end_date="2025-01-31",
)

# Lifetime workouts (from your account creation date)
all_workouts = otf.workouts.get_lifetime_workouts()
```

You can also get a workout from a specific booking:

```python
import pendulum

bookings = otf.bookings.get_bookings_new(
    start_date=pendulum.today().subtract(months=1),
    end_date=pendulum.today(),
)
booking = next(b for b in bookings if b.workout is not None)
workout = otf.workouts.get_workout_from_booking(booking)
```

## Performance Summaries

Each workout includes a performance summary with key metrics:

```python
workout = workouts[0]

print(f"Calories: {workout.calories_burned}")
print(f"Splat Points: {workout.splat_points}")
print(f"Steps: {workout.step_count}")
print(f"Active Time: {workout.active_time_seconds}s")
print(f"Coach: {workout.coach}")
```

## Heart Rate Zones

Zone time is available as minutes spent in each zone:

```python
zones = workout.zone_time_minutes
print(f"Gray: {zones.gray} min")
print(f"Blue: {zones.blue} min")
print(f"Green: {zones.green} min")
print(f"Orange: {zones.orange} min")
print(f"Red: {zones.red} min")
```

Heart rate summary data is also included:

```python
hr = workout.heart_rate
print(f"Max HR: {hr.max_hr}")
print(f"Peak HR: {hr.peak_hr} ({hr.peak_hr_percent}%)")
print(f"Avg HR: {hr.avg_hr} ({hr.avg_hr_percent}%)")
```

## Telemetry Data

Workouts include detailed second-by-second telemetry with heart rate readings and
equipment data (treadmill speed/incline, rower metrics):

```python
telemetry = workout.telemetry

# Zone boundaries (BPM ranges)
print(f"Orange zone: {telemetry.zones.orange.start_bpm}-{telemetry.zones.orange.end_bpm} bpm")

# Individual data points
for point in telemetry.telemetry[:5]:
    print(f"  t={point.relative_timestamp}s  HR={point.hr}  cals={point.agg_calories}")
    if point.tread_data:
        print(f"    Tread: {point.tread_data.tread_speed} mph, {point.tread_data.tread_incline}% incline")
```

## Treadmill and Rower Data

Aggregate equipment data is available on the workout object:

```python
tread = workout.treadmill_data
if tread:
    print(f"Distance: {tread.total_distance.display_value} {tread.total_distance.display_unit}")
    print(f"Max Speed: {tread.max_speed.display_value} {tread.max_speed.display_unit}")
    print(f"Elevation: {tread.elevation_gained.display_value} {tread.elevation_gained.display_unit}")

rower = workout.rower_data
if rower:
    print(f"Distance: {rower.total_distance.display_value} {rower.total_distance.display_unit}")
    print(f"Avg Pace: {rower.avg_pace.display_value} {rower.avg_pace.display_unit}")
    print(f"Avg Power: {rower.avg_power.display_value} {rower.avg_power.display_unit}")
```

## Lifetime Stats

Get aggregated statistics across all your in-studio workouts:

```python
from otf_api.models.workouts import StatsTime

# All-time stats
stats = otf.workouts.get_member_lifetime_stats_in_studio()
print(f"Total Calories: {stats.calories}")
print(f"Total Splat Points: {stats.splat_point}")
print(f"Treadmill Distance: {stats.treadmill_distance}")
print(f"Rower Distance: {stats.rower_distance}")
print(f"Step Count: {stats.step_count}")

# Stats for a specific time period
this_month = otf.workouts.get_member_lifetime_stats_in_studio(StatsTime.ThisMonth)
print(f"This month calories: {this_month.calories}")
```

!!! tip
    `StatsTime` supports `AllTime`, `ThisMonth`, `ThisWeek`, and other time periods for
    scoping your stats query.

## Body Composition Data

```python
body_comp = otf.workouts.get_body_composition_list()
for entry in body_comp:
    print(entry.model_dump_json(indent=2))
```

## Heart Rate History

Track how your heart rate zones have shifted over time:

```python
hr_history = otf.workouts.get_hr_history()
for item in hr_history:
    print(f"Max HR: {item.max_hr_value}, Change: {item.change_from_previous}")
```

!!! note
    Out-of-studio workouts are available via `get_member_lifetime_stats_out_of_studio()`
    and `get_out_of_studio_workout_history()`.
