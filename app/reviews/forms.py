from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, SelectField
from wtforms.validators import Length, InputRequired, Optional, NumberRange


class ReviewForm(FlaskForm):
    title = StringField('Give a title', validators=[InputRequired(), Length(1, 64)])
    body = TextAreaField("How about the recipe?", validators=[InputRequired()])
    rating = SelectField("How do you like this?", coerce=int, validators=[InputRequired()])
    suggestion = TextAreaField('Give some suggestions', validators=[Optional()])
    submit = SubmitField('Submit')

    def __init__(self, *args, **kwargs):
        super(ReviewForm, self).__init__(*args, **kwargs)
        self.rating.choices = [(_, _) for _ in range(1, 6)]  # (value, label) pairs
        self.rating.default = ['5']
