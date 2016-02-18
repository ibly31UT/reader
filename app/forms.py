from flask.ext.wtf import Form
from wtforms import StringField, BooleanField, PasswordField, RadioField, IntegerField, validators
from wtforms.validators import DataRequired

accessLevels = [("0","Guest"), ("1","User"), ("2","Security"), ("3","Priority User"), ("99","Admin")]
accessLevels.pop()   # delete admin from the end of the list so that all forms don't allow the person to set more than one admin

class LoginForm(Form):
	username = StringField("Username", [validators.Length(min=4, max=28)])
	password = PasswordField("Password", [validators.Length(min=6, max=28)])
	remember_me = BooleanField("Remember Me", default=False)

class CreateUserForm(Form):
	username = StringField("New User Username", [validators.Length(min=4, max=25)])
	password = PasswordField("New User Password", [validators.Length(min=6, max=25), validators.EqualTo("confirm", message="Passwords must match.")])
	confirm = PasswordField("Confirm Password")
	access = RadioField("Access Level", choices=accessLevels, default=1)

class ChangeAdminPasswordForm(Form):
	oldpassword = PasswordField("Old Password", [validators.Length(min=6, max=25)])
	password = PasswordField("New Password", [validators.Length(min=6, max=25), validators.EqualTo("confirm", message="Passwords must match.")])
	confirm = PasswordField("Confirm Password")

class LogAccessForm(Form):
	radio = RadioField("Save", choices=[("1", "Save Access Logs"), ("0", "Don't Save Access Logs")], default=1)

class EditUserForm(Form):
	access = RadioField("Access Level", choices=accessLevels, default=1)
	facid = IntegerField("Facility ID")
	cardid = IntegerField("Card ID")