from flask_wtf import FlaskForm
from wtforms import TextAreaField, SubmitField, StringField
from wtforms.validators import DataRequired, InputRequired, Optional, Length
from wtforms.fields.html5 import DateField


class EventForm(FlaskForm):
    title = TextAreaField('Give event a name', validators=[InputRequired(), Length(1, 64)])
    timestamp = DateField('Choose a date', validators=[InputRequired()])
    location = StringField('Location', validators=[Optional(), Length(0, 64)])
    about_event = TextAreaField('Tell everyone about this event', validators=[Optional()])
    submit = SubmitField('Create my event')


class ReportForm(FlaskForm):
    title = TextAreaField('Give report a title', validators=[InputRequired(), Length(1, 64)])
    body = TextAreaField('Tell everyone about this group', validators=[Optional()])
    submit = SubmitField('Finish my report')
