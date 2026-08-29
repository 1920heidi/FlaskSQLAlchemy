from datetime import date

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from models import Exercise, Workout, WorkoutExercise, db


# ---------- model validations ----------

def test_exercise_name_cannot_be_blank(app):
    with pytest.raises(ValueError):
        Exercise(name="   ", category="strength", equipment_needed=False)


def test_exercise_category_must_be_valid(app):
    with pytest.raises(ValueError):
        Exercise(name="Burpee", category="not-a-category", equipment_needed=False)


def test_exercise_name_is_stripped_and_saved(app):
    exercise = Exercise(name="  Lunge  ", category="strength", equipment_needed=False)
    db.session.add(exercise)
    db.session.commit()
    assert exercise.name == "Lunge"


def test_workout_duration_must_be_positive(app):
    with pytest.raises(ValueError):
        Workout(date=date(2026, 1, 1), duration_minutes=-10)


def test_workout_exercise_reps_must_be_positive(app):
    with pytest.raises(ValueError):
        WorkoutExercise(reps=-1)


def test_workout_exercise_sets_must_be_positive(app):
    with pytest.raises(ValueError):
        WorkoutExercise(sets=0)


def test_workout_exercise_duration_seconds_must_be_positive(app):
    with pytest.raises(ValueError):
        WorkoutExercise(duration_seconds=-5)


# ---------- relationships ----------

def test_workout_has_many_exercises_through_workout_exercise(app):
    workout = Workout(date=date(2026, 1, 1), duration_minutes=30)
    exercise = Exercise(name="Squat", category="strength", equipment_needed=False)
    db.session.add_all([workout, exercise])
    db.session.commit()

    db.session.add(WorkoutExercise(workout=workout, exercise=exercise, sets=3, reps=10))
    db.session.commit()

    assert exercise in workout.exercises
    assert workout in exercise.workouts


def test_deleting_workout_cascades_workout_exercises(app):
    workout = Workout(date=date(2026, 1, 1), duration_minutes=30)
    exercise = Exercise(name="Squat", category="strength", equipment_needed=False)
    db.session.add_all([workout, exercise])
    db.session.commit()

    db.session.add(WorkoutExercise(workout=workout, exercise=exercise, sets=3, reps=10))
    db.session.commit()
    assert WorkoutExercise.query.count() == 1

    db.session.delete(workout)
    db.session.commit()
    assert WorkoutExercise.query.count() == 0


def test_deleting_exercise_cascades_workout_exercises(app):
    workout = Workout(date=date(2026, 1, 1), duration_minutes=30)
    exercise = Exercise(name="Squat", category="strength", equipment_needed=False)
    db.session.add_all([workout, exercise])
    db.session.commit()

    db.session.add(WorkoutExercise(workout=workout, exercise=exercise, sets=3, reps=10))
    db.session.commit()
    assert WorkoutExercise.query.count() == 1

    db.session.delete(exercise)
    db.session.commit()
    assert WorkoutExercise.query.count() == 0


# ---------- table (CHECK) constraints, enforced independently of the ORM ----------

def test_db_rejects_non_positive_duration_minutes_at_the_constraint_level(app):
    with pytest.raises(IntegrityError):
        db.session.execute(
            text(
                "INSERT INTO workouts (date, duration_minutes) VALUES (:date, :duration)"
            ),
            {"date": "2026-01-01", "duration": -5},
        )
        db.session.commit()
    db.session.rollback()


def test_db_rejects_invalid_category_at_the_constraint_level(app):
    with pytest.raises(IntegrityError):
        db.session.execute(
            text(
                "INSERT INTO exercises (name, category, equipment_needed) "
                "VALUES (:name, :category, :equipment_needed)"
            ),
            {"name": "Mystery Move", "category": "invalid", "equipment_needed": 0},
        )
        db.session.commit()
    db.session.rollback()
