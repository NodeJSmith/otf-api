# Challenges & Benchmarks

The challenges API provides access to your benchmark results and challenge tracker data.
OrangeTheory periodically runs benchmark challenges (like the 2000m row or 1-mile run) and
tracks your personal records over time. All challenge operations are accessed through
`otf.workouts`.

## Challenge Tracker

Get an overview of all your challenge participation:

```python
tracker = otf.workouts.get_challenge_tracker()
```

The tracker contains a summary of your challenge history across all categories and
equipment types.

## Benchmarks by Equipment

Query your benchmark results filtered by equipment type:

```python
from otf_api.models.workouts import EquipmentType

# Get all rower benchmarks
rower_benchmarks = otf.workouts.get_benchmarks_by_equipment(EquipmentType.Rower)

for benchmark in rower_benchmarks:
    print(f"{benchmark.challenge_name}")
    print(f"  Best: {benchmark.best_record}")
    print(f"  Last: {benchmark.last_record}")
    print(f"  Attempts: {len(benchmark.challenge_histories)}")
```

**Available equipment types:**

| EquipmentType | Description |
|---------------|-------------|
| `EquipmentType.Treadmill` | Treadmill challenges (1-mile run, 12-minute distance, etc.) |
| `EquipmentType.Rower` | Rower challenges (200m, 500m, 2000m row, etc.) |
| `EquipmentType.Other` | Other equipment or bodyweight challenges |

Each benchmark includes:

- `challenge_name` - The name of the benchmark (e.g., "2000 METER Row")
- `best_record` - Your personal best result
- `last_record` - Your most recent result
- `previous_record` - Your result before the most recent
- `equipment_name` - The equipment used
- `metric_entry` - Details about the measurement (time, distance, etc.)
- `challenge_histories` - A list of all your attempts with dates and results

## Benchmarks by Challenge Category

Query benchmarks by their category ID using the `ChallengeCategory` enum:

```python
from otf_api.models.workouts import ChallengeCategory

for category in ChallengeCategory:
    benchmarks = otf.workouts.get_benchmarks_by_challenge_category(category)
    if not benchmarks:
        continue
    print(f"\n{category.name}: {len(benchmarks)} benchmark(s)")
    for b in benchmarks:
        print(f"  {b.challenge_name} - Best: {b.best_record} {b.unit or ''}")
```

## Challenge History Detail

Each benchmark contains a `challenge_histories` list with your individual attempts:

```python
benchmarks = otf.workouts.get_benchmarks_by_equipment(EquipmentType.Rower)
benchmark = benchmarks[0]

for history in benchmark.challenge_histories:
    print(f"Date: {history.start_date.date()}")
    print(f"Studio: {history.studio_name}")
    print(f"Result: {history.total_result}")
    print(f"Finished: {history.is_finished}")

    # Each history can have multiple sub-entries (e.g., split times)
    for entry in history.benchmark_histories:
        print(f"  Class: {entry.class_name} with {entry.coach_name}")
        print(f"  Result: {entry.result}")
```

## Challenge Detail

Get detailed information about a specific challenge category:

```python
detail = otf.workouts.get_challenge_tracker_detail(challenge_category_id=17)
print(f"Challenge: {detail.challenge_name}")
print(f"Equipment: {detail.equipment_name}")
print(f"Metric: {detail.metric_entry.entry_type}")
```

!!! tip
    The `metric_entry.entry_type` field tells you whether the challenge measures "Time"
    (lower is better) or "Distance" (higher is better), which is useful for comparing
    your results over time.

!!! note
    Challenge category IDs and equipment IDs are internal OTF identifiers. Use the
    `ChallengeCategory` and `EquipmentType` enums rather than raw integers for clarity
    and forward compatibility.
