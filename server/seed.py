#!/usr/bin/env python3

from datetime import date, timedelta

from app import app
from models import Exercise, Workout, WorkoutExercise, db

with app.app_context():
    print("Clearing existing data...")
    WorkoutExercise.query.delete()
    Exercise.query.delete()
    Workout.query.delete()
    db.session.commit()

    print("Seeding exercises...")
    push_up = Exercise(name="Push Up", category="strength", equipment_needed=False)
    squat = Exercise(name="Squat", category="strength", equipment_needed=False)
    deadlift = Exercise(name="Deadlift", category="strength", equipment_needed=True)
    running = Exercise(name="Running", category="cardio", equipment_needed=False)
    jump_rope = Exercise(name="Jump Rope", category="cardio", equipment_needed=True)
    plank = Exercise(name="Plank", category="strength", equipment_needed=False)
    hamstring_stretch = Exercise(
        name="Hamstring Stretch", category="flexibility", equipment_needed=False
    )
    single_leg_stand = Exercise(
        name="Single Leg Stand", category="balance", equipment_needed=False
    )

    exercises = [
        push_up,
        squat,
        deadlift,
        running,
        jump_rope,
        plank,
        hamstring_stretch,
        single_leg_stand,
    ]
    db.session.add_all(exercises)
    db.session.commit()

    print("Seeding workouts...")
    strength_day = Workout(
        date=date.today() - timedelta(days=2),
        duration_minutes=45,
        notes="Focus on form over speed.",
    )
    cardio_day = Workout(
        date=date.today() - timedelta(days=1),
        duration_minutes=30,
        notes="Steady state cardio.",
    )
    recovery_day = Workout(
        date=date.today(),
        duration_minutes=20,
        notes="Light stretching and balance work.",
    )

    workouts = [strength_day, cardio_day, recovery_day]
    db.session.add_all(workouts)
    db.session.commit()

    print("Linking exercises to workouts...")
    workout_exercises = [
        WorkoutExercise(workout=strength_day, exercise=push_up, sets=3, reps=15),
        WorkoutExercise(workout=strength_day, exercise=squat, sets=4, reps=10),
        WorkoutExercise(workout=strength_day, exercise=deadlift, sets=3, reps=8),
        WorkoutExercise(workout=strength_day, exercise=plank, duration_seconds=60),
        WorkoutExercise(workout=cardio_day, exercise=running, duration_seconds=1200),
        WorkoutExercise(workout=cardio_day, exercise=jump_rope, duration_seconds=300),
        WorkoutExercise(
            workout=recovery_day, exercise=hamstring_stretch, duration_seconds=120
        ),
        WorkoutExercise(
            workout=recovery_day, exercise=single_leg_stand, duration_seconds=60
        ),
    ]
    db.session.add_all(workout_exercises)
    db.session.commit()

    print("Seeding complete!")
