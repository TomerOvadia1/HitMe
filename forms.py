from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, DateField
from wtforms.validators import DataRequired, Length, Email, EqualTo


class RegistrationForm(FlaskForm):
    """
    Registration form for sign up page
    """
    from datetime import date
    username = StringField('Username', validators=[DataRequired(),
                                                   Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    birth_date = DateField('Date of birth', format='%Y-%m-%d', default=date.today(),
                           validators=[DataRequired()])
    password = PasswordField('Password',
                             validators=[DataRequired(), Length(min=6, max=10)])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')


class LoginForm(FlaskForm):
    """
    Login form for login page
    """
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password',
                             validators=[DataRequired(), Length(min=6, max=10)])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')
