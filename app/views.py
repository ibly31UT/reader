from flask import render_template, flash, redirect, session, url_for, request, g
from flask.ext.login import login_user, logout_user, current_user, login_required
from app import app, db, lm
from .forms import LoginForm, CreateUserForm, ChangeAdminPasswordForm, LogAccessForm, EditUserForm
from .models import User, Reader

navigation = [{"name": "Home", "link": "index"}, {"name": "Card Readers", "link": "readers"}, {"name": "Personnel", "link": "users"}, {"name": "Settings", "link": "settings"}]
#accessLevels = [("0","Guest"), ("1","User"), ("2","Security"), ("3","Priority User"), ("99","Admin")]
accessLevels = ["Guest", "User", "Security", "Priority User", "Admin"]
# ^^ Also defined identically in forms.py, unsure how to make a global declaration of this array

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
		if 'remember_me' in session:
			remember_me = session['remember_me']
			session.pop('remember_me', None)
		if form.password.data == user.password:
			login_user(user, remember = remember_me)
			return redirect("/users")
		else:
			flash("The password you entered is not correct.", "error")
			return redirect("/index")
	elif form.errors:
		flash(form.errors, "error")

	return render_template("index.html", title="Home", form=form, user=g.user, navigation=navigation)

@app.route("/readers")
@login_required
def readers():
	readers = Reader.query.all()
	users = User.query.all()

	if g.user.access != 99:
		flash("You are not logged in as a user capable of viewing settings. Please log in as admin.")
		return redirect("/index")

	return render_template("readers.html", title="Card Readers", readers=readers, users=users, user=g.user, navigation=navigation)

@app.route("/users", methods=["GET", "POST"])
@login_required
def users():
	createUserForm = CreateUserForm()
	editUserForm = EditUserForm()

	if g.user.access == 99:
		if createUserForm.validate_on_submit():
			existing_user = User.query.filter_by(username=form.username.data).first()
			if existing_user is None:
				newuser = User(createUserForm.username.data, int(createUserForm.access.data), createUserForm.password.data)
				db.session.add(newuser)
				db.session.commit()
				flash("Successfully added user %s to the system with access level %s." % (createUserForm.username.data, createUserForm.access.data))
				return redirect("/users")
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

@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
	adminPasswordForm = ChangeAdminPasswordForm()
	logAccessForm = LogAccessForm()
	settings = [{"name": "Change Admin Password", "form": adminPasswordForm}, {"name": "Log Access Times and Locations", "form": logAccessForm}]

	if g.user.access == 99:
		if adminPasswordForm.validate_on_submit():
			if g.user.password == adminPasswordForm.oldpassword.data:
				admin = User.query.filter_by(access=2).update(dict(password=adminPasswordForm.password.data))
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

