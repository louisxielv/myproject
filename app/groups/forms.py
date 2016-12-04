from flask_pagedown.fields import PageDownField
from flask_wtf import FlaskForm
from wtforms import TextAreaField, SubmitField
from wtforms.validators import DataRequired


class GroupForm(FlaskForm):
    title = TextAreaField('Give group a name')
    about_group = PageDownField('Tell me about this group', validators=[DataRequired()])
    submit = SubmitField('Submit')
