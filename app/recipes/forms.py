from flask import current_app
from flask_wtf import FlaskForm
from flask_wtf.file import FileField
from wtforms import StringField, TextAreaField, SelectField, SubmitField, \
    SelectMultipleField, FieldList, FormField, widgets, FloatField
from wtforms.validators import Length, url, Optional, InputRequired


class MultiCheckboxField(SelectMultipleField):
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()


class PhotoForm(FlaskForm):
    photo = FileField('Your photo')


class IngredientForm(FlaskForm):
    # ingredients
    name = StringField('Name', validators=[Optional()])
    unit = SelectField('Unit', coerce=str, validators=[Optional()])
    quantity = FloatField('Quantity', validators=[Optional()])

    def __init__(self, *args, **kwargs):
        super(IngredientForm, self).__init__(*args, **kwargs)
        self.unit.choices = [(_, _) for _ in current_app.config['INGREDIENT_CONVERSION'].keys()]


class LinkForm(FlaskForm):
    link = StringField('Put a relevant link', validators=[Optional(), url(require_tld=False)])


class RecipeForm(FlaskForm):
    # recipe
    title = StringField('Give a title', validators=[InputRequired(), Length(1, 64)])
    photo = FileField('Upload a finished image', validators=[Optional()])
    serving = SelectField('The Number of Serving', coerce=int, validators=[Optional()])
    body = TextAreaField("Tell us how to make it?", validators=[Optional()])
    # ingredients
    # ingredients = FieldList(FormField(IngredientForm, label=""), min_entries=1)
    ingredients_optical = FieldList(FormField(IngredientForm, label=""), min_entries=8)

    # links
    links = FieldList(FormField(LinkForm, label=""), min_entries=2)

    tags = MultiCheckboxField('Choose some tags', validators=[Optional()])

    submit = SubmitField('Submit')

    def __init__(self, *args, **kwargs):
        super(RecipeForm, self).__init__(*args, **kwargs)
        self.serving.choices = [(_, _) for _ in range(1, 6)]  # (value, label) pairs
        self.tags.choices = [(str(i), _) for i, _ in enumerate(current_app.config['RECIPE_TAGS'], 1)]
        self.tags.default = ['1']


class ReviewForm(FlaskForm):
    title = StringField('Give a title', validators=[InputRequired(), Length(1, 64)])
    body = TextAreaField("How about the recipe?", validators=[InputRequired()])
    rating = SelectField("How do you like this?", coerce=int, validators=[InputRequired()])
    suggestion = TextAreaField('Give some suggestions', validators=[Optional()])
    submit = SubmitField('Submit')

    def __init__(self, *args, **kwargs):
        super(ReviewForm, self).__init__(*args, **kwargs)
        self.rating.choices = [(_, _ * u"\u2605") for _ in range(5, 0, -1)]  # (value, label) pairs
        self.rating.default = [5]
