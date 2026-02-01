from flask_wtf import FlaskForm
from flask_babel import _, lazy_gettext as _l
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo
import sqlalchemy as sa
from app import db
from app.models import Caregiver


class LoginForm(FlaskForm):
    caregiver_name = StringField(_l('Caregiver_name'), validators=[DataRequired()])
    password = PasswordField(_l('Password'), validators=[DataRequired()])
    remember_me = BooleanField(_l('Remember Me'))
    submit = SubmitField(_l('Sign In'))
    

class RegistrationForm(FlaskForm):
    caregiver_name = StringField(_l('Caregiver_name'), validators=[DataRequired()])
    email = StringField(_l('Email'), validators=[DataRequired(), Email()])
    password = PasswordField(_l('Password'), validators=[DataRequired()])
    password2 = PasswordField(
        _l('Repeat Password'), validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField(_l('Register'))

    def validate_caregiver_name(self, caregiver_name):
        caregiver = db.session.scalar(sa.select(Caregiver).where(
            Caregiver.caregiver_name == caregiver_name.data))
        if caregiver is not None:
            raise ValidationError(_('Please use a different caregiver_name.'))

    def validate_email(self, email):
        caregiver = db.session.scalar(sa.select(Caregiver).where(
            Caregiver.email == email.data))
        if caregiver is not None:
            raise ValidationError(_('Please use a different email address.'))
        

class ResetPasswordRequestForm(FlaskForm):
    email = StringField(_l('Email'), validators=[DataRequired(), Email()])
    submit = SubmitField(_l('Request Password Reset'))


class ResetPasswordForm(FlaskForm):
    password = PasswordField(_l('Password'), validators=[DataRequired()])
    password2 = PasswordField(
        _l('Repeat Password'), validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField(_l('Request Password Reset'))