from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from flask_admin.menu import MenuLink
from .models import User, Reader

class AdminIndex(AdminIndexView):
	@expose("/")
	def index(self):
		return self.render("admin/index.html")

class UserModelView(ModelView):
	column_exclude_list = ("password")
	column_display_pk = False
	page_size = 40
	can_export = True

class ReaderModelView(ModelView):
	column_display_pk = False

def start_admin(app, db):
	admin = Admin(app, name="Console", index_view=AdminIndex(), template_mode="bootstrap3")
	admin.add_view(UserModelView(User, db.session))
	admin.add_view(ReaderModelView(Reader, db.session))
	admin.add_link(MenuLink(name="Back to Console", url="/index"))
