from flask import render_template, current_app
from flask_babel import _
from app.email import send_email


def send_password_reset_email(caregiver):
    token = caregiver.get_reset_password_token()
    send_email(_('[Dementia Tracker] Reset Your Password'),
               sender=current_app.config['ADMINS'][0],
               recipients=[caregiver.email],
               text_body=render_template('email/reset_password.txt',
                                         caregiver=caregiver, token=token),
               html_body=render_template('email/reset_password.html',
                                         caregiver=caregiver, token=token))