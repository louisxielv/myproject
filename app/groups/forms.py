from flask_pagedown.fields import PageDownField
from flask_wtf import FlaskForm
from wtforms import TextAreaField, SubmitField
from wtforms.validators import DataRequired, InputRequired, Optional, Length


class GroupForm(FlaskForm):
    title = TextAreaField('Give group a name', validators=[InputRequired(), Length(1, 64)])
    about_group = TextAreaField('Tell me about this group', validators=[Optional()])
    submit = SubmitField('Create my group')


