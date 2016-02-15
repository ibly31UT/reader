from flask.ext.wtf import Form
from wtforms import StringField, BooleanField, PasswordField, RadioField, validators
from wtforms.validators import DataRequired

class LoginForm(Form):
	username = StringField("username", [validators.Length(min=4, max=25)])
	password = PasswordField("password", [validators.Length(min=6, max=25)])
	remember_me = BooleanField("remember_me", default=False)

class CreateUserForm(Form):
	username = StringField("username", [validators.Length(min=4, max=25)])
	password = PasswordField("password", [validators.Length(min=6, max=25), validators.EqualTo("confirm", message="Passwords must match.")])
	confirm = PasswordField("Repeat Password")
	#access = RadioField("Access Level", choices=[(1,"Priority User"), (0,"User")])