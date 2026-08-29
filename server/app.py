from flask import Flask, jsonify, request
from flask_migrate import Migrate
from marshmallow import ValidationError

from models import Exercise, Workout, WorkoutExercise, db
from schemas import (
    ExerciseDetailSchema,
    ExerciseSchema,
    WorkoutDetailSchema,
    WorkoutExerciseSchema,
    WorkoutExerciseWithExerciseSchema,
    WorkoutSchema,
)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

migrate = Migrate(app, db)

db.init_app(app)

workout_schema = WorkoutSchema()
workouts_schema = WorkoutSchema(many=True)
workout_detail_schema = WorkoutDetailSchema()

exercise_schema = ExerciseSchema()
exercises_schema = ExerciseSchema(many=True)
exercise_detail_schema = ExerciseDetailSchema()

workout_exercise_input_schema = WorkoutExerciseSchema()
workout_exercise_output_schema = WorkoutExerciseWithExerciseSchema()


# ---------- error handlers ----------

@app.errorhandler(404)
def not_found(_error):
    return jsonify({"error": "Resource not found"}), 404


@app.errorhandler(400)
def bad_request(_error):
    return jsonify({"error": "Bad request"}), 400


# ---------- index ----------

@app.route('/', methods=['GET'])
def index():
    return jsonify({
        "message": "Workout Tracker API",
        "endpoints": {
            "GET /workouts": "List all workouts",
            "GET /workouts/<id>": "Show a workout with its exercises",
            "POST /workouts": "Create a workout",
            "DELETE /workouts/<id>": "Delete a workout",
            "GET /exercises": "List all exercises",
            "GET /exercises/<id>": "Show an exercise with its workouts",
            "POST /exercises": "Create an exercise",
            "DELETE /exercises/<id>": "Delete an exercise",
            "POST /workouts/<workout_id>/exercises/<exercise_id>/workout_exercises":
                "Add an exercise to a workout",
        },
    }), 200


# ---------- Workout routes ----------

@app.route('/workouts', methods=['GET'])
def get_workouts():
    workouts = Workout.query.all()
    return jsonify(workouts_schema.dump(workouts)), 200


@app.route('/workouts/<int:id>', methods=['GET'])
def get_workout(id):
    workout = db.session.get(Workout, id)
    if workout is None:
        return jsonify({"error": "Workout not found"}), 404
    return jsonify(workout_detail_schema.dump(workout)), 200


@app.route('/workouts', methods=['POST'])
def create_workout():
    json_data = request.get_json(silent=True) or {}
    try:
        data = workout_schema.load(json_data)
    except ValidationError as err:
        return jsonify({"errors": err.messages}), 400

    workout = Workout(**data)
    try:
        db.session.add(workout)
        db.session.commit()
    except ValueError as err:
        db.session.rollback()
        return jsonify({"errors": [str(err)]}), 400

    return jsonify(workout_schema.dump(workout)), 201


@app.route('/workouts/<int:id>', methods=['DELETE'])
def delete_workout(id):
    workout = db.session.get(Workout, id)
    if workout is None:
        return jsonify({"error": "Workout not found"}), 404

    # cascade="all, delete-orphan" on Workout.workout_exercises removes
    # associated WorkoutExercise rows automatically.
    db.session.delete(workout)
    db.session.commit()
    return '', 204


# ---------- Exercise routes ----------

@app.route('/exercises', methods=['GET'])
def get_exercises():
    exercises = Exercise.query.all()
    return jsonify(exercises_schema.dump(exercises)), 200


@app.route('/exercises/<int:id>', methods=['GET'])
def get_exercise(id):
    exercise = db.session.get(Exercise, id)
    if exercise is None:
        return jsonify({"error": "Exercise not found"}), 404
    return jsonify(exercise_detail_schema.dump(exercise)), 200


@app.route('/exercises', methods=['POST'])
def create_exercise():
    json_data = request.get_json(silent=True) or {}
    try:
        data = exercise_schema.load(json_data)
    except ValidationError as err:
        return jsonify({"errors": err.messages}), 400

    exercise = Exercise(**data)
    try:
        db.session.add(exercise)
        db.session.commit()
    except ValueError as err:
        db.session.rollback()
        return jsonify({"errors": [str(err)]}), 400
    except Exception:
        db.session.rollback()
        return jsonify({"errors": ["An exercise with that name already exists."]}), 400

    return jsonify(exercise_schema.dump(exercise)), 201


@app.route('/exercises/<int:id>', methods=['DELETE'])
def delete_exercise(id):
    exercise = db.session.get(Exercise, id)
    if exercise is None:
        return jsonify({"error": "Exercise not found"}), 404

    # cascade="all, delete-orphan" on Exercise.workout_exercises removes
    # associated WorkoutExercise rows automatically.
    db.session.delete(exercise)
    db.session.commit()
    return '', 204


# ---------- WorkoutExercise routes ----------

@app.route(
    '/workouts/<int:workout_id>/exercises/<int:exercise_id>/workout_exercises',
    methods=['POST'],
)
def add_exercise_to_workout(workout_id, exercise_id):
    workout = db.session.get(Workout, workout_id)
    if workout is None:
        return jsonify({"error": "Workout not found"}), 404

    exercise = db.session.get(Exercise, exercise_id)
    if exercise is None:
        return jsonify({"error": "Exercise not found"}), 404

    json_data = request.get_json(silent=True) or {}
    try:
        data = workout_exercise_input_schema.load(json_data)
    except ValidationError as err:
        return jsonify({"errors": err.messages}), 400

    workout_exercise = WorkoutExercise(workout_id=workout.id, exercise_id=exercise.id, **data)
    try:
        db.session.add(workout_exercise)
        db.session.commit()
    except ValueError as err:
        db.session.rollback()
        return jsonify({"errors": [str(err)]}), 400

    return jsonify(workout_exercise_output_schema.dump(workout_exercise)), 201


if __name__ == '__main__':
    app.run(port=5555, debug=True)
