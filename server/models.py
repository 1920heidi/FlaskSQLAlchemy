from datetime import date as date_type

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import CheckConstraint
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import validates

db = SQLAlchemy()

VALID_CATEGORIES = ("cardio", "strength", "flexibility", "balance")


class Exercise(db.Model):
    __tablename__ = "exercises"

    __table_args__ = (
        CheckConstraint("length(trim(name)) > 0", name="exercise_name_not_blank"),
        CheckConstraint(
            "category in ('cardio', 'strength', 'flexibility', 'balance')",
            name="exercise_category_valid",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)
    category = db.Column(db.String, nullable=False)
    equipment_needed = db.Column(db.Boolean, nullable=False, default=False)

    workout_exercises = db.relationship(
        "WorkoutExercise", back_populates="exercise", cascade="all, delete-orphan"
    )
    workouts = association_proxy("workout_exercises", "workout")

    @validates("name")
    def validate_name(self, key, value):
        if not value or not value.strip():
            raise ValueError("Exercise name cannot be blank.")
        return value.strip()

    @validates("category")
    def validate_category(self, key, value):
        if value not in VALID_CATEGORIES:
            raise ValueError(f"category must be one of {VALID_CATEGORIES}.")
        return value

    def __repr__(self):
        return f"<Exercise {self.id}: {self.name}>"


class Workout(db.Model):
    __tablename__ = "workouts"

    __table_args__ = (
        CheckConstraint("duration_minutes > 0", name="workout_duration_positive"),
    )

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, default=date_type.today)
    duration_minutes = db.Column(db.Integer, nullable=False)
    notes = db.Column(db.Text, nullable=True)

    workout_exercises = db.relationship(
        "WorkoutExercise", back_populates="workout", cascade="all, delete-orphan"
    )
    exercises = association_proxy("workout_exercises", "exercise")

    @validates("duration_minutes")
    def validate_duration_minutes(self, key, value):
        if value is None or value <= 0:
            raise ValueError("duration_minutes must be a positive integer.")
        return value

    @validates("date")
    def validate_date(self, key, value):
        if value is None:
            raise ValueError("date is required.")
        return value

    def __repr__(self):
        return f"<Workout {self.id} on {self.date}>"


class WorkoutExercise(db.Model):
    __tablename__ = "workout_exercises"

    __table_args__ = (
        CheckConstraint("reps IS NULL OR reps > 0", name="workout_exercise_reps_positive"),
        CheckConstraint("sets IS NULL OR sets > 0", name="workout_exercise_sets_positive"),
        CheckConstraint(
            "duration_seconds IS NULL OR duration_seconds > 0",
            name="workout_exercise_duration_positive",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    workout_id = db.Column(db.Integer, db.ForeignKey("workouts.id"), nullable=False)
    exercise_id = db.Column(db.Integer, db.ForeignKey("exercises.id"), nullable=False)
    reps = db.Column(db.Integer, nullable=True)
    sets = db.Column(db.Integer, nullable=True)
    duration_seconds = db.Column(db.Integer, nullable=True)

    workout = db.relationship("Workout", back_populates="workout_exercises")
    exercise = db.relationship("Exercise", back_populates="workout_exercises")

    @validates("reps", "sets", "duration_seconds")
    def validate_positive(self, key, value):
        if value is not None and value <= 0:
            raise ValueError(f"{key} must be a positive integer.")
        return value

    def __repr__(self):
        return f"<WorkoutExercise workout={self.workout_id} exercise={self.exercise_id}>"
