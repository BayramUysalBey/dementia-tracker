from flask import request
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, SelectField
from wtforms.validators import ValidationError, DataRequired, Length
import sqlalchemy as sa
from flask_babel import _, lazy_gettext as _l
from app import db
from app.models import Caregiver, get_severity_options


class EditProfileForm(FlaskForm):
    caregiver_name = StringField(_l('Caregiver_name'), validators=[DataRequired()])
    about_me = TextAreaField(_l('About me'), validators=[Length(min=0, max=140)])
    submit = SubmitField(_l('Submit'))

    def __init__(self, original_caregiver_name, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_caregiver_name = original_caregiver_name

    def validate_caregiver_name(self, caregiver_name):
        if caregiver_name.data != self.original_caregiver_name:
            caregiver = db.session.scalar(sa.select(Caregiver).where(
                Caregiver.caregiver_name == caregiver_name.data))
            if caregiver is not None:
                raise ValidationError(_('Please use a different caregiver_name.'))
            

class EmptyForm(FlaskForm):
    submit = SubmitField(_l('Submit'))
    

class SymptomLogForm(FlaskForm):
    symptomlog = TextAreaField(_l('Write a notes'), validators=[
        DataRequired(), Length(min=1, max=140)])
    severity = SelectField('Severity', 
                         choices=get_severity_options(), 
                         coerce=int,
                         default=1)
    submit = SubmitField(_l('Submit'))
    

class SearchForm(FlaskForm):
    q = StringField(_l('Search'), validators=[DataRequired()])

    def __init__(self, *args, **kwargs):
        if 'formdata' not in kwargs:
            kwargs['formdata'] = request.args
        if 'meta' not in kwargs:
            kwargs['meta'] = {'csrf': False}
        super(SearchForm, self).__init__(*args, **kwargs)
    

class EditSymptomlogForm(FlaskForm):
    symptomlog = TextAreaField(_l('Symptom'), validators=[DataRequired(), Length(min=1, max=140)])
    severity = SelectField(_l('Severity'), 
                         choices=get_severity_options(), 
                         coerce=int)
    submit = SubmitField(_l('Update'))
    

class MessageForm(FlaskForm):
    message = TextAreaField(_l('Message'), validators=[
        DataRequired(), Length(min=1, max=140)])
    submit = SubmitField(_l('Submit'))
