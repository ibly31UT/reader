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


from flask import render_template, flash, redirect, session, url_for, request, g
from flask.ext.login import login_user, logout_user, current_user, login_required
from app import app, db, lm
from .forms import LoginForm, CreateUserForm, ChangeAdminPasswordForm, LogAccessForm, EditUserForm, CreateGuestForm, ManualCheckInForm
from .models import User, Reader, GlobalSettings

import json
import datetime
import random

navigation = [{"name": "Home", "link": "index"}, {"name": "Card Readers", "link": "readers"}, {"name": "Personnel", "link": "users"}, {"name": "Reception", "link": "reception"}, {"name": "Settings", "link": "settings"}]

@app.before_request
def before_request():
	g.user = current_user

@lm.user_loader
def load_user(id):
	return db.session.query(User).get(int(id))

@app.route("/logout")
def logout():
	logout_user()
	g.user = None
	return redirect(url_for("index"))

@app.route("/", methods=["GET", "POST"])
@app.route("/index", methods=["GET", "POST"])
def index():
	form = LoginForm()
	if form.validate_on_submit():
		user = db.session.query(User).filter_by(username=form.username.data).first()
		if user is None:
			flash("Couldn't find that user.", "error")
			return redirect("/index")
		remember_me = False
		if "remember_me" in session:
			remember_me = session["remember_me"]
			session.pop("remember_me", None)
		else:
			session["remember_me"] = form.remember_me.data
		if user.check_password(form.password.data):
			login_user(user, remember = remember_me)
			if user.access == 4: # reception user logged in
				return redirect("/reception")
			return redirect("/users")
		else:
			flash("The password you entered is not correct.", "error")
			return redirect("/index")
	elif form.errors:
		flash(form.errors, "error")

	return render_template("index.html", title="Home", form=form, user=g.user, navigation=navigation)

@app.route("/getUsers")
@login_required
def getUsers():
	users = db.session.query(User).all()
	userList = []
	for user in users:
		userList.append({"id": user.id, "username": user.username, "access": user.access, "cardid": user.cardid})

	return json.dumps(userList)

@app.route("/getReaders", methods=["GET"])
@login_required
def getReaders():
	readers = db.session.query(Reader).all()
	readerList = []
	for reader in readers:
		readerList.append({"id": reader.id, "name": reader.name, "status": reader.status, "users": reader.users})

	return json.dumps(readerList)

@app.route("/readers")
@login_required
def readers():
	readers = db.session.query(Reader).all()
	users = db.session.query(User).all()

	for reader in readers:
		if reader.status == 2:
			flash("There are one or more readers with status: TAMPER, please confirm.", "warning")
			break

	if g.user.access != 99:
		flash("You are not logged in as a user capable of viewing settings. Please log in as admin.")
		return redirect("/index")

	globalSettings = db.session.query(GlobalSettings).filter_by().first()
	accessLevels = globalSettings.getSetting("accessLevels")

	return render_template("readers.html", title="Card Readers", readers=readers, users=users, user=g.user, accessLevels=accessLevels, navigation=navigation)

@app.route("/readerChangeUserList", methods=["POST"])
def readerChangeUserList():
	requestObject = request.get_json()
	readerID = requestObject["readerID"];
	readerUserList = requestObject["readerUserList"];
	readerUserListString = json.dumps(readerUserList)
	reader = db.session.query(Reader).get(int(readerID))
	if reader is not None:
		db.session.query(Reader).filter_by(id=int(readerID)).update(dict(users=readerUserListString))
		db.session.commit()
		return json.dumps({"status": "OK", "readerName": reader.name, "readerUserList": readerUserListString})
	else:
		return json.dumps({"status": "ERROR"})

@app.route("/readerEnable", methods=["POST"])
@login_required
def readerEnable():
	requestObject = request.get_json()
	readerID = requestObject["readerID"]
	reader = db.session.query(Reader).get(int(readerID))

	if reader is not None:
		db.session.query(Reader).filter_by(id=int(readerID)).update(dict(status=1))
		db.session.commit()
		return json.dumps({"status": "OK", "readerName": reader.name})
	else:
		return json.dumps({"status": "ERROR"})

@app.route("/readerDisable", methods=["POST"])
@login_required
def readerDisable():
	readerID = request.form["readerID"]
	reader = db.session.query(Reader).get(int(readerID))

	return json.dumps({"status": "OK", "readerName": reader.name})

@app.route("/users", methods=["GET", "POST"])
@login_required
def users():
	createUserForm = CreateUserForm()
	editUserForm = EditUserForm()

	if g.user.access == 99:
		if createUserForm.validate_on_submit():
			existing_user = db.session.query(User).filter_by(username=createUserForm.username.data).first()
			if existing_user is None:
				cardid = str(int(random.random() * 999999))
				newuser = User(createUserForm.username.data, int(createUserForm.access.data), cardid, createUserForm.password.data)
				db.session.add(newuser)
				db.session.commit()
				flash("Successfully added user %s to the system with access level %s." % (createUserForm.username.data, createUserForm.access.data))
			else:
				flash("A user exists already with that username.", "error")
			return redirect("/users")
		elif createUserForm.errors:
			flash(createUserForm.errors, "error")
		elif editUserForm.validate_on_submit():
			flash("Yay")
		elif editUserForm.errors:
			flash(editUserForm.errors, "error")
	else:
		flash("You are not logged in as a user capable of viewing settings. Please log in as admin.")
		return redirect("/index")
		
	users = db.session.query(User).all()
	globalSettings = db.session.query(GlobalSettings).filter_by().first()
	accessLevels = globalSettings.getSetting("accessLevels")

	return render_template("users.html", title="Personnel", users=users, user=g.user, accessLevels=accessLevels, createUserForm=createUserForm, editUserForm=editUserForm, navigation=navigation)

@app.route("/reception", methods=["GET", "POST"])
@login_required
def reception():
	readers = db.session.query(Reader).all()
	users = db.session.query(User).all()

	createGuestForm = CreateGuestForm()
	manualCheckInForm = ManualCheckInForm()

	if manualCheckInForm.validate_on_submit():
		username = manualCheckInForm.username.data
		cardid = manualCheckInForm.cardid.data

		reader = db.session.query(Reader).get(int(g.user.receptionCurrentReader))
		readerLogArray = json.loads(reader.log)

		user = db.session.query(User).filter_by(username=username, cardid=cardid).first()
		if user is None:
			flash("Could not check in user, please ensure the Facility ID and Card ID are correct.", "error")
		else:
			readerLogArray.append({"user": user.id, "time": str(datetime.datetime.now())})
			reader.log = json.dumps(readerLogArray)
			db.session.commit()

	user = g.user
	promptChooseReader = False
	if user.receptionCurrentReader is None:
		user.receptionCurrentReader = 0
		db.session.commit()
		promptChooseReader = True

	currentReader = int(user.receptionCurrentReader) - 1
	# minus one because ID's are 1-indexed whereas the readers array is 0-indexed
	return render_template("reception.html", title="Reception", readers=readers, currentReader=currentReader, promptChooseReader=promptChooseReader, users=users, createGuestForm=createGuestForm, manualCheckInForm=manualCheckInForm, user=g.user, navigation=navigation)

@app.route("/receptionChangeCurrentReader", methods=["POST"])
@login_required
def receptionChangeCurrentReader():
	user = g.user
	readerID = request.form["readerID"]

	user.receptionCurrentReader = readerID
	db.session.commit()

	reader = db.session.query(Reader).get(int(readerID))

	return json.dumps({"status": "OK", "readerName": reader.name, "readerID": int(readerID)})

@app.route("/receptionUpdateLog", methods=["GET"])
@login_required
def receptionUpdateLog():
	user = g.user
	reader = db.session.query(Reader).get(int(user.receptionCurrentReader))

	logString = reader.log
	logArray = json.loads(logString)

	for log in logArray:
		curUser = db.session.query(User).get(int(log["user"]))
		log["username"] = curUser.username

	return json.dumps({"status": "OK", "log": logArray})

@app.route("/receptionCheckIn", methods=["POST"])
@login_required
def receptionCheckIn():
	username = request.form["username"]
	cardid = request.form["cardid"]

	user = db.session.query(User).filter_by(username=username, cardid=cardid)

	if user is not None:
		print "Successful log in"

	return json.dumps({"status": "OK"})

@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
	adminPasswordForm = ChangeAdminPasswordForm()
	logAccessForm = LogAccessForm()
	settings = [{"name": "Change Admin Password", "form": adminPasswordForm}, {"name": "Log Access Times and Locations", "form": logAccessForm}]

	if g.user.access == 99:
		if adminPasswordForm.validate_on_submit():
			if g.user.password == adminPasswordForm.oldpassword.data:
				db.session.query(User).filter_by(access=99).update(dict(password=adminPasswordForm.password.data))
				db.session.commit()
				flash("Successfully changed admin password!")
			else:
				flash("Old admin password that was entered did not match records", "error")
		elif adminPasswordForm.errors:
			flash(adminPasswordForm.errors, "error")
		elif logAccessForm.validate_on_submit():
			flash("Yay!")
		elif logAccessForm.errors:
			flash(logAccessForm.errors, "error")
	else:
		flash("You are not logged in as a user capable of viewing settings. Please log in as admin.")
		return redirect("/index")

	return render_template("settings.html", title="Settings", settings=settings, user=g.user, navigation=navigation)

