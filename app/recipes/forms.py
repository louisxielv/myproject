from flask_pagedown.fields import PageDownField
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, SelectField, SubmitField, \
    IntegerField, SelectMultipleField, FloatField
from wtforms import ValidationError
from wtforms.validators import DataRequired, Length, Email, Regexp, url
from flask import current_app
from ..models import Role, User
from werkzeug.utils import secure_filename
from flask_wtf.file import FileField


class RecipeForm(FlaskForm):
    # recipe
    title = StringField('Title', validators=[DataRequired(), Length(1, 64)])
    serving = SelectField('The Number of Serving', coerce=int, validators=[DataRequired()])
    body = TextAreaField("How to make your favourite food?", validators=[DataRequired()])
    # ingredients
    name = StringField('Ingredient Name', validators=[DataRequired(), Length(1, 64)])
    unit = SelectField('Unit', coerce=str, validators=[DataRequired()])
    quantity = FloatField('Quantity', validators=[DataRequired()])

    links = StringField('Put a relevant link', default='https://www.google.com/1', validators=[url()])

    tags = SelectMultipleField('Choose some tags')

    submit = SubmitField('Submit')

    def __init__(self, *args, **kwargs):
        super(RecipeForm, self).__init__(*args, **kwargs)
        self.serving.choices = [(_, _) for _ in range(1, 6)]   # (value, label) pairs
        self.unit.choices = [(_, _) for _ in current_app.config['INGREDIENT_CONVERSION'].keys()]
        self.tags.choices = [(str(i), _) for i, _ in enumerate(current_app.config['RECIPE_TAGS'], 1)]
        self.tags.default = ['1']


class PhotoForm(FlaskForm):
    photo = FileField('Your photo')
    submit = SubmitField('Up')
