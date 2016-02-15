from flask import render_template, flash, redirect, session, url_for, request, g
from flask.ext.login import login_user, logout_user, current_user, login_required
from app import app, db, lm
from .forms import LoginForm, CreateUserForm
from .models import User

navigation = [{"name": "Home", "link": "index"}, {"name": "Card Readers", "link": "readers"}, {"name": "Personnel", "link": "users"}]

@app.before_request
def before_request():
	g.user = current_user

@lm.user_loader
def load_user(id):
	return User.query.get(int(id))

@app.route("/logout")
def logout():
	logout_user()
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
	return render_template("index.html", title="Home", form=form, navigation=navigation)

@app.route("/readers")
@login_required
def readers():
	users = User.query.all()
	return render_template("readers.html", title="Readers", users=users, user=g.user, navigation=navigation)

@app.route("/users", methods=["GET", "POST"])
@login_required
def users():
	form = CreateUserForm()
	if form.validate_on_submit():
		existing_user = User.query.filter_by(username=form.username.data).first()
		if existing_user is None:
			newuser = User(form.username.data, 1, form.password.data)
			db.session.add(newuser)
			db.session.commit()
			flash("Successfully added user %s to the system." % form.username.data)
			return redirect("/users")
		else:
			flash("A user exists already with that username.", "error")
			return redirect("/users")
		
	users = User.query.all()
	return render_template("users.html", title="Personnel", users=users, user=g.user, form=form, navigation=navigation)



