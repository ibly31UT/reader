from app import db
User.query.delete()

#admin = User("admin")
admin = User("admin", 2, "password")
regularuser = User("user", 1, "wordpass")
db.session.add(admin)
db.session.add(regularuser)
db.session.commit()