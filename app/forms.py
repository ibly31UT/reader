from flask.ext.wtf import Form
from wtforms import StringField, BooleanField, PasswordField, RadioField, validators
from wtforms.validators import DataRequired

class LoginForm(Form):
	username = StringField("Username", [validators.Length(min=4, max=25)])
	password = PasswordField("Password", [validators.Length(min=6, max=25)])
	remember_me = BooleanField("Remember Me", default=False)

class CreateUserForm(Form):
	username = StringField("New User Username", [validators.Length(min=4, max=25)])
	password = PasswordField("New User Password", [validators.Length(min=6, max=25), validators.EqualTo("confirm", message="Passwords must match.")])
	confirm = PasswordField("Confirm Password")
	access = RadioField("Access Level", choices=[("1","Priority User"), ("0","User")])

class ChangeAdminPasswordForm(Form):
	oldpassword = PasswordField("Old Password", [validators.Length(min=6, max=25)])
	password = PasswordField("New Password", [validators.Length(min=6, max=25), validators.EqualTo("confirm", message="Passwords must match.")])
	confirm = PasswordField("Confirm Password")

class LogAccessForm(Form):
	radio = RadioField("Save", choices=[("1", "Save Access Logs"), ("0", "Don't Save Access Logs")], default=1)