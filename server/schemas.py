from marshmallow import Schema, ValidationError, fields, validate, validates_schema

from models import VALID_CATEGORIES


class ExerciseSchema(Schema):
    id = fields.Integer(dump_only=True)
    name = fields.String(required=True, validate=validate.Length(min=1, max=100))
    category = fields.String(required=True, validate=validate.OneOf(VALID_CATEGORIES))
    equipment_needed = fields.Boolean(load_default=False)


class WorkoutSchema(Schema):
    id = fields.Integer(dump_only=True)
    date = fields.Date(required=True)
    duration_minutes = fields.Integer(required=True, validate=validate.Range(min=1, max=600))
    notes = fields.String(allow_none=True, validate=validate.Length(max=1000))


class WorkoutExerciseSchema(Schema):
    id = fields.Integer(dump_only=True)
    workout_id = fields.Integer(dump_only=True)
    exercise_id = fields.Integer(dump_only=True)
    reps = fields.Integer(allow_none=True, validate=validate.Range(min=1))
    sets = fields.Integer(allow_none=True, validate=validate.Range(min=1))
    duration_seconds = fields.Integer(allow_none=True, validate=validate.Range(min=1))

    @validates_schema
    def validate_reps_sets_or_duration(self, data, **kwargs):
        has_reps_and_sets = data.get("reps") is not None and data.get("sets") is not None
        has_duration = data.get("duration_seconds") is not None
        if not has_reps_and_sets and not has_duration:
            raise ValidationError(
                "Provide either both reps and sets, or a duration_seconds value."
            )


class WorkoutExerciseWithExerciseSchema(WorkoutExerciseSchema):
    exercise = fields.Nested(ExerciseSchema, dump_only=True)


class WorkoutExerciseWithWorkoutSchema(WorkoutExerciseSchema):
    workout = fields.Nested(WorkoutSchema, dump_only=True)


class WorkoutDetailSchema(WorkoutSchema):
    workout_exercises = fields.List(
        fields.Nested(WorkoutExerciseWithExerciseSchema), dump_only=True
    )


class ExerciseDetailSchema(ExerciseSchema):
    workout_exercises = fields.List(
        fields.Nested(WorkoutExerciseWithWorkoutSchema), dump_only=True
    )
