from flask import current_app
from flask_wtf import FlaskForm
from flask_wtf.file import FileField
from wtforms import StringField, TextAreaField, SelectField, SubmitField, \
    SelectMultipleField, FieldList, FormField
from wtforms.validators import DataRequired, Length, Regexp, url, Optional, InputRequired


class PhotoForm(FlaskForm):
    photo = FileField('Your photo')


class IngredientForm(FlaskForm):
    # ingredients
    name = StringField('Ingredient Name', validators=[Optional()])
    unit = SelectField('Unit', coerce=str, validators=[Optional()])
    quantity = StringField('Quantity', validators=[Optional()])

    def __init__(self, *args, **kwargs):
        super(IngredientForm, self).__init__(*args, **kwargs)
        self.unit.choices = [(_, _) for _ in current_app.config['INGREDIENT_CONVERSION'].keys()]


class LinkForm(FlaskForm):
    link = StringField('Put a relevant link', validators=[Optional(), url(require_tld=False)])


class RecipeForm(FlaskForm):
    # recipe
    title = StringField('Give a title', validators=[InputRequired(), Length(1, 64)])
    photo = FileField('Upload a finished image', validators=[DataRequired()])
    serving = SelectField('The Number of Serving', coerce=int, validators=[InputRequired()])
    body = TextAreaField("Tell us how to make it?", validators=[InputRequired()])
    # ingredients
    ingredients = FieldList(FormField(IngredientForm), min_entries=1)
    ingredients_optical = FieldList(FormField(IngredientForm), min_entries=4)

    # links
    links = FieldList(FormField(LinkForm), min_entries=2)

    tags = SelectMultipleField('Choose some tags', validators=[Optional()])

    submit = SubmitField('Submit')

    def __init__(self, *args, **kwargs):
        super(RecipeForm, self).__init__(*args, **kwargs)
        self.serving.choices = [(_, _) for _ in range(1, 6)]  # (value, label) pairs
        self.tags.choices = [(str(i), _) for i, _ in enumerate(current_app.config['RECIPE_TAGS'], 1)]
        self.tags.default = ['1']
