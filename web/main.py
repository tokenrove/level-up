

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

import data
import util

class MainHandler(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        util.handle_with_template(self.response, 'index.html',
                                  { 'user': user,
                                    'login_url': user and users.create_logout_url("/") or
                                                          users.create_login_url("/me"),
                                    'adminp': users.is_current_user_admin()
                                    })

class NewClassHandler(webapp.RequestHandler):
    def post(self):
        name = self.request.get('name')
        if users.is_current_user_admin() and data.Archetype.all().filter('name =', name).count(1) == 0:
            data.Archetype(name=name).put()
        self.redirect('/me')

def main():
    application = webapp.WSGIApplication([('/', MainHandler),
                                          ('/admin/new-class', NewClassHandler)],
                                         debug=True)
    run_wsgi_app(application)

if __name__ == '__main__':
    main()

