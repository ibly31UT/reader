# Copyright (c) 2016 William Connolly, Tyler Rocha, Justin Baiko

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
# the Software, and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all copies
# or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, 
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR 
# PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE 
# FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, 
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


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
	cardid = IntegerField("Card ID")	

class CreateGuestForm(Form):
	username = StringField("Guest Name", [validators.Length(min=3, max=28)])
	expires = BooleanField("Guest Expires", default=True)

class ManualCheckInForm(Form):
	username = StringField("Username", [validators.Length(min=3, max=28)])
	cardid = IntegerField("Card ID")