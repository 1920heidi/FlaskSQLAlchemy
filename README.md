# Workout Tracker API

A Flask + SQLAlchemy + Marshmallow API for tracking workouts and exercises. Trainers can log workouts, build a reusable exercise library, and attach exercises to a workout with reps/sets or duration.

## Installation

Requires Python 3.12 and [Pipenv](https://pipenv.pypa.io/).

```bash
pipenv install
pipenv shell
cd server
export FLASK_APP=app.py
flask db upgrade head
python seed.py
```

## Running

```bash
cd server
python app.py
```

- API: `http://localhost:5555`
- Web UI: `http://localhost:5555/app`

Run tests with `cd server && pytest`.

## Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/workouts` | List all workouts |
| GET | `/workouts/<id>` | Show a workout with its exercises (reps/sets/duration) |
| POST | `/workouts` | Create a workout — `{ date, duration_minutes, notes }` |
| DELETE | `/workouts/<id>` | Delete a workout (and its exercise entries) |
| GET | `/exercises` | List all exercises |
| GET | `/exercises/<id>` | Show an exercise with the workouts it's used in |
| POST | `/exercises` | Create an exercise — `{ name, category, equipment_needed }` |
| DELETE | `/exercises/<id>` | Delete an exercise (and its workout entries) |
| POST | `/workouts/<workout_id>/exercises/<exercise_id>/workout_exercises` | Add an exercise to a workout — `{ reps, sets }` and/or `{ duration_seconds }` |

Errors are returned as JSON: `{ "error": "..." }` (404) or `{ "errors": {...} }` (400).
