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
