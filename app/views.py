from flask import render_template, flash, redirect, session, url_for, request, g
from flask.ext.login import login_user, logout_user, current_user, login_required
from app import app, db, lm
from .forms import LoginForm, CreateUserForm, ChangeAdminPasswordForm, LogAccessForm, EditUserForm, CreateGuestForm, ManualCheckInForm
from .models import User, Reader
import json
import datetime
import time
import random

navigation = [{"name": "Home", "link": "index"}, {"name": "Card Readers", "link": "readers"}, {"name": "Personnel", "link": "users"}, {"name": "Reception", "link": "reception"}, {"name": "Settings", "link": "settings"}]
#accessLevels = [("0","Guest"), ("1","User"), ("2","Security"), ("3","Priority User"), ("99","Admin")]
accessLevels = ["Guest", "User", "Security", "Priority User", "Reception"]
# ^^ Also defined identically in forms.py, unsure how to make a global declaration of this array

def logUser():
	while True:
		reader = Reader.query.get(int(g.user.receptionCurrentReader))
		readerLogArray = json.loads(reader.log)

		user = User.query.filter_by(username="admin").first()
		
		readerLogArray.append({"user": user.id, "time": str(datetime.datetime.now())})
		reader.log = json.dumps(readerLogArray)
		db.session.commit()
		time.sleep(5)

@app.before_request
def before_request():
	g.user = current_user

@lm.user_loader
def load_user(id):
	return User.query.get(int(id))

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
		user = User.query.filter_by(username=form.username.data).first()
		if user is None:
			flash("Couldn't find that user.", "error")
			return redirect("/index")
		remember_me = False
		if "remember_me" in session:
			remember_me = session["remember_me"]
			session.pop("remember_me", None)
		else:
			session["remember_me"] = form.remember_me.data
		if form.password.data == user.password:
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
	users = User.query.all()
	userList = []
	for user in users:
		userList.append({"id": user.id, "username": user.username, "access": user.access, "facid": user.facid, "cardid": user.cardid})

	return json.dumps(userList)

@app.route("/getReaders")
@login_required
def getReaders():
	readers = Reader.query.all()
	readerList = []
	for reader in readers:
		readerList.append({"id": reader.id, "name": reader.name, "status": reader.status, "users": reader.users})

	return json.dumps(readerList)

@app.route("/readers")
@login_required
def readers():
	readers = Reader.query.all()
	users = User.query.all()

	for reader in readers:
		if reader.status == 2:
			flash("There are one or more readers with status: TAMPER, please confirm.", "warning")
			break

	if g.user.access != 99:
		flash("You are not logged in as a user capable of viewing settings. Please log in as admin.")
		return redirect("/index")

	return render_template("readers.html", title="Card Readers", readers=readers, users=users, user=g.user, accessLevels=accessLevels, navigation=navigation)

@app.route("/readerChangeUserList", methods=["POST"])
def readerChangeUserList():
	requestObject = request.get_json()
	readerID = requestObject["readerID"];
	readerUserList = requestObject["readerUserList"];
	readerUserListString = json.dumps(readerUserList)
	reader = Reader.query.get(int(readerID))
	if reader is not None:
		Reader.query.filter_by(id=int(readerID)).update(dict(users=readerUserListString))
		db.session.commit()
		return json.dumps({"status": "OK", "readerName": reader.name, "readerUserList": readerUserListString})
	else:
		return json.dumps({"status": "ERROR"})

@app.route("/readerEnable", methods=["POST"])
@login_required
def readerEnable():
	readerID = request.form["readerID"]
	reader = Reader.query.get(int(readerID))

	return json.dumps({"status": "OK", "readerName": reader.name})

@app.route("/readerDisable", methods=["POST"])
@login_required
def readerDisable():
	readerID = request.form["readerID"]
	reader = Reader.query.get(int(readerID))

	return json.dumps({"status": "OK", "readerName": reader.name})

@app.route("/users", methods=["GET", "POST"])
@login_required
def users():
	createUserForm = CreateUserForm()
	editUserForm = EditUserForm()

	if g.user.access == 99:
		if createUserForm.validate_on_submit():
			existing_user = User.query.filter_by(username=createUserForm.username.data).first()
			if existing_user is None:
				facid = str(int(random.random() * 9999))
				cardid = str(int(random.random() * 9999))
				newuser = User(createUserForm.username.data, int(createUserForm.access.data), cardid, facid, createUserForm.password.data)
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
		
	users = User.query.all()
	return render_template("users.html", title="Personnel", users=users, user=g.user, accessLevels=accessLevels, createUserForm=createUserForm, editUserForm=editUserForm, navigation=navigation)

@app.route("/reception", methods=["GET", "POST"])
@login_required
def reception():
	readers = Reader.query.all()
	users = User.query.all()

	createGuestForm = CreateGuestForm()
	manualCheckInForm = ManualCheckInForm()

	if manualCheckInForm.validate_on_submit():
		username = manualCheckInForm.username.data
		facid = manualCheckInForm.facid.data
		cardid = manualCheckInForm.cardid.data

		reader = Reader.query.get(int(g.user.receptionCurrentReader))
		readerLogArray = json.loads(reader.log)

		user = User.query.filter_by(username=username, facid=facid, cardid=cardid).first()
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

	reader = Reader.query.get(int(readerID))

	return json.dumps({"status": "OK", "readerName": reader.name, "readerID": int(readerID)})

@app.route("/receptionUpdateLog", methods=["GET"])
@login_required
def receptionUpdateLog():
	user = g.user
	reader = Reader.query.get(int(user.receptionCurrentReader))

	logString = reader.log
	logArray = json.loads(logString)

	for log in logArray:
		curUser = User.query.get(int(log["user"]))
		log["username"] = curUser.username

	return json.dumps({"status": "OK", "log": logArray})

@app.route("/receptionCheckIn", methods=["POST"])
@login_required
def receptionCheckIn():
	username = request.form["username"]
	facid = request.form["facid"]
	cardid = request.form["cardid"]

	user = User.query.filter_by(username=username, facid=facid, cardid=cardid)

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
				User.query.filter_by(access=99).update(dict(password=adminPasswordForm.password.data))
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

