from flask.ext.wtf import Form
from wtforms import StringField, BooleanField, PasswordField, RadioField, IntegerField, DateTimeField, validators
from wtforms.validators import DataRequired

accessLevels = [("0","Guest"), ("1","User"), ("2","Security"), ("3","Priority User"), ("4","Reception")]

class LoginForm(Form):
	username = StringField("Username", [validators.Length(min=3, max=28)])
	password = PasswordField("Password", [validators.Length(min=6, max=28)])
	remember_me = BooleanField("Remember Me", default=False)

class CreateUserForm(Form):
	username = StringField("New User Username", [validators.Length(min=3, max=25)])
	password = PasswordField("New User Password", [validators.Length(min=6, max=25), validators.EqualTo("confirm", message="Passwords must match.")])
	confirm = PasswordField("Confirm Password")
	access = RadioField("Access Level", choices=accessLevels, default=1)

class ChangeAdminPasswordForm(Form):
	oldpassword = PasswordField("Old Password", [validators.Length(min=6, max=25)])
	password = PasswordField("New Password", [validators.Length(min=6, max=25), validators.EqualTo("confirm", message="Passwords must match.")])
	confirm = PasswordField("Confirm Password")

class LogAccessForm(Form):
	radio = RadioField("Save Access Logs", choices=[("1", "Save Logs"), ("0", "Don't Save Logs")], default=1)

class EditUserForm(Form):
	access = RadioField("Access Level", choices=accessLevels, default=1)
	facid = IntegerField("Facility ID")
	cardid = IntegerField("Card ID")	

class CreateGuestForm(Form):
	username = StringField("Guest Name", [validators.Length(min=3, max=28)])
	expires = BooleanField("Guest Expires", default=True)

class ManualCheckInForm(Form):
	username = StringField("Username", [validators.Length(min=3, max=28)])
	facid = IntegerField("Facility ID")
	cardid = IntegerField("Card ID")