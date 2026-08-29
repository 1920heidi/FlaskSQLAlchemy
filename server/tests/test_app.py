from datetime import date

from models import Exercise, Workout, WorkoutExercise, db


def seed_one_workout_and_exercise():
    workout = Workout(date=date(2026, 1, 1), duration_minutes=30, notes="Leg day")
    exercise = Exercise(name="Squat", category="strength", equipment_needed=False)
    db.session.add_all([workout, exercise])
    db.session.commit()
    return workout, exercise


# ---------- workouts ----------

def test_get_workouts_empty(client):
    response = client.get("/workouts")
    assert response.status_code == 200
    assert response.get_json() == []


def test_create_workout(client):
    response = client.post(
        "/workouts", json={"date": "2026-01-01", "duration_minutes": 45, "notes": "Push day"}
    )
    assert response.status_code == 201
    data = response.get_json()
    assert data["duration_minutes"] == 45
    assert Workout.query.count() == 1


def test_create_workout_rejects_non_positive_duration(client):
    response = client.post("/workouts", json={"date": "2026-01-01", "duration_minutes": -1})
    assert response.status_code == 400
    assert "errors" in response.get_json()
    assert Workout.query.count() == 0


def test_get_single_workout_includes_exercises(app, client):
    workout, exercise = seed_one_workout_and_exercise()
    db.session.add(WorkoutExercise(workout=workout, exercise=exercise, sets=3, reps=10))
    db.session.commit()

    response = client.get(f"/workouts/{workout.id}")
    assert response.status_code == 200
    data = response.get_json()
    assert len(data["workout_exercises"]) == 1
    assert data["workout_exercises"][0]["exercise"]["name"] == "Squat"


def test_get_missing_workout_returns_404(client):
    response = client.get("/workouts/999")
    assert response.status_code == 404


def test_delete_workout_cascades_workout_exercises(app, client):
    workout, exercise = seed_one_workout_and_exercise()
    db.session.add(WorkoutExercise(workout=workout, exercise=exercise, sets=3, reps=10))
    db.session.commit()

    response = client.delete(f"/workouts/{workout.id}")
    assert response.status_code == 204
    assert Workout.query.count() == 0
    assert WorkoutExercise.query.count() == 0


# ---------- exercises ----------

def test_get_exercises_empty(client):
    response = client.get("/exercises")
    assert response.status_code == 200
    assert response.get_json() == []


def test_create_exercise(client):
    response = client.post(
        "/exercises", json={"name": "Deadlift", "category": "strength", "equipment_needed": True}
    )
    assert response.status_code == 201
    assert Exercise.query.count() == 1


def test_create_exercise_rejects_invalid_category(client):
    response = client.post(
        "/exercises", json={"name": "Deadlift", "category": "nonsense", "equipment_needed": True}
    )
    assert response.status_code == 400
    assert Exercise.query.count() == 0


def test_create_exercise_rejects_duplicate_name(app, client):
    db.session.add(Exercise(name="Deadlift", category="strength", equipment_needed=True))
    db.session.commit()

    response = client.post(
        "/exercises", json={"name": "Deadlift", "category": "strength", "equipment_needed": True}
    )
    assert response.status_code == 400
    assert Exercise.query.count() == 1


def test_get_single_exercise_includes_workouts(app, client):
    workout, exercise = seed_one_workout_and_exercise()
    db.session.add(WorkoutExercise(workout=workout, exercise=exercise, duration_seconds=60))
    db.session.commit()

    response = client.get(f"/exercises/{exercise.id}")
    assert response.status_code == 200
    data = response.get_json()
    assert len(data["workout_exercises"]) == 1
    assert data["workout_exercises"][0]["workout"]["id"] == workout.id


def test_get_missing_exercise_returns_404(client):
    response = client.get("/exercises/999")
    assert response.status_code == 404


def test_delete_exercise_cascades_workout_exercises(app, client):
    workout, exercise = seed_one_workout_and_exercise()
    db.session.add(WorkoutExercise(workout=workout, exercise=exercise, duration_seconds=60))
    db.session.commit()

    response = client.delete(f"/exercises/{exercise.id}")
    assert response.status_code == 204
    assert Exercise.query.count() == 0
    assert WorkoutExercise.query.count() == 0


# ---------- adding an exercise to a workout ----------

def test_add_exercise_to_workout_with_reps_and_sets(app, client):
    workout, exercise = seed_one_workout_and_exercise()

    response = client.post(
        f"/workouts/{workout.id}/exercises/{exercise.id}/workout_exercises",
        json={"reps": 12, "sets": 3},
    )
    assert response.status_code == 201
    data = response.get_json()
    assert data["reps"] == 12
    assert data["sets"] == 3
    assert data["exercise"]["name"] == "Squat"


def test_add_exercise_to_workout_with_duration(app, client):
    workout, exercise = seed_one_workout_and_exercise()

    response = client.post(
        f"/workouts/{workout.id}/exercises/{exercise.id}/workout_exercises",
        json={"duration_seconds": 90},
    )
    assert response.status_code == 201
    assert response.get_json()["duration_seconds"] == 90


def test_add_exercise_to_workout_requires_reps_sets_or_duration(app, client):
    workout, exercise = seed_one_workout_and_exercise()

    response = client.post(
        f"/workouts/{workout.id}/exercises/{exercise.id}/workout_exercises", json={}
    )
    assert response.status_code == 400
    assert WorkoutExercise.query.count() == 0


def test_add_exercise_to_missing_workout_returns_404(app, client):
    _, exercise = seed_one_workout_and_exercise()
    response = client.post(
        f"/workouts/999/exercises/{exercise.id}/workout_exercises", json={"reps": 5, "sets": 5}
    )
    assert response.status_code == 404


def test_add_missing_exercise_to_workout_returns_404(app, client):
    workout, _ = seed_one_workout_and_exercise()
    response = client.post(
        f"/workouts/{workout.id}/exercises/999/workout_exercises", json={"reps": 5, "sets": 5}
    )
    assert response.status_code == 404
