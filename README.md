# Workout Tracker API

## Description

A backend API for a workout tracking application used by personal trainers, built with Flask, Flask-SQLAlchemy, Flask-Migrate, and Marshmallow.

The API tracks **Workouts** and reusable **Exercises**. A workout can include many exercises, and each exercise can appear in many workouts. The `WorkoutExercise` join model records the reps, sets, and/or duration for a given exercise within a given workout.

### Data model

- **Exercise**: `id`, `name` (unique), `category` (one of `cardio`, `strength`, `flexibility`, `balance`), `equipment_needed` (boolean)
- **Workout**: `id`, `date`, `duration_minutes`, `notes`
- **WorkoutExercise** (join table): `id`, `workout_id`, `exercise_id`, `reps`, `sets`, `duration_seconds`

### Relationships

- A `WorkoutExercise` belongs to a `Workout` and belongs to an `Exercise`.
- A `Workout` has many `WorkoutExercise`s and has many `Exercise`s through `WorkoutExercise`.
- An `Exercise` has many `WorkoutExercise`s and has many `Workout`s through `WorkoutExercise`.
- Deleting a `Workout` or `Exercise` cascades to delete its associated `WorkoutExercise` rows.

### Validations

**Table constraints** (`server/models.py`):
- `exercises.name` cannot be blank, `exercises.category` must be a valid category (CHECK constraints)
- `workouts.duration_minutes` must be greater than 0 (CHECK constraint)
- `workout_exercises.reps`, `.sets`, `.duration_seconds` must be `NULL` or greater than 0 (CHECK constraints)

**Model validations** (`@validates` in `server/models.py`):
- `Exercise.name` cannot be blank
- `Exercise.category` must be one of the allowed categories
- `Workout.duration_minutes` must be a positive integer
- `Workout.date` is required
- `WorkoutExercise.reps` / `.sets` / `.duration_seconds` must be positive integers when present

**Schema validations** (`server/schemas.py`):
- `Exercise.name`: required, length 1-100
- `Exercise.category`: required, must be one of the allowed categories
- `Workout.duration_minutes`: required, must be between 1 and 600
- `WorkoutExercise`: cross-field validation requiring either both `reps` and `sets`, or a `duration_seconds` value

## Installation

Requires Python 3.12 and [Pipenv](https://pipenv.pypa.io/).

```bash
# from the project root
pipenv install
pipenv shell
```

Set up the database (run from inside the `server/` directory):

```bash
cd server
export FLASK_APP=app.py
flask db upgrade head
python seed.py
```

## Running the API

```bash
cd server
python app.py
```

The API runs at `http://localhost:5555`. A browsable web UI is served at `http://localhost:5555/app` (see [Frontend](#frontend) below).

## Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/workouts` | List all workouts |
| GET | `/workouts/<id>` | Get a single workout, including its exercises with reps/sets/duration |
| POST | `/workouts` | Create a workout. Body: `{ "date": "YYYY-MM-DD", "duration_minutes": int, "notes": "string" (optional) }` |
| DELETE | `/workouts/<id>` | Delete a workout and its associated `WorkoutExercise` rows |
| GET | `/exercises` | List all exercises |
| GET | `/exercises/<id>` | Get a single exercise, including the workouts it's used in |
| POST | `/exercises` | Create an exercise. Body: `{ "name": "string", "category": "cardio\|strength\|flexibility\|balance", "equipment_needed": bool }` |
| DELETE | `/exercises/<id>` | Delete an exercise and its associated `WorkoutExercise` rows |
| POST | `/workouts/<workout_id>/exercises/<exercise_id>/workout_exercises` | Add an exercise to a workout. Body: `{ "reps": int, "sets": int }` and/or `{ "duration_seconds": int }` |

All error responses are returned as JSON, e.g. `{ "error": "Workout not found" }` (404) or `{ "errors": {...} }` (400 validation errors).

## Frontend

A single-page vanilla HTML/CSS/JS UI is served by Flask itself at `/app` (same origin as the API, so no CORS setup is needed). It lets you browse workouts and exercises, log a new workout, add an exercise to your library, expand a workout to add exercises with reps/sets or duration, and delete workouts/exercises. It talks to the same REST endpoints listed above — there's no separate backend for it.

Source: `server/static/index.html`, `server/static/css/style.css`, `server/static/js/app.js`.

## Tests

A pytest suite covers model validations, table constraints, relationships/cascades, and every endpoint (success and error paths). Each test runs against a fresh in-memory SQLite database.

```bash
cd server
pytest
```

## Project structure

```
ass2/
├── Pipfile
├── Pipfile.lock
├── README.md
├── .gitignore
└── server/
    ├── app.py          # Flask app, routes
    ├── models.py        # SQLAlchemy models, table constraints, model validations
    ├── schemas.py        # Marshmallow schemas, schema validations
    ├── seed.py          # Seed script
    ├── conftest.py       # Pytest fixtures (in-memory test database)
    ├── tests/           # Pytest suite
    ├── static/          # Frontend (index.html, css/, js/), served at /app
    └── migrations/        # Flask-Migrate migration history
```
