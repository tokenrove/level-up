

import os
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app

class MainHandler(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()

        template_values = {
            'name': user or 'unnamed',
            'login_url': (user and users.create_logout_url("/") or users.create_login_url("/me")),
            'login_text': (user and 'Sign-out' or 'Login'),
            'adminp': users.is_current_user_admin()
            }
        path = os.path.join(os.path.dirname(__file__), 'index.html')
        self.response.out.write(template.render(path, template_values))

def main():
    application = webapp.WSGIApplication([('/', MainHandler)], debug=True)
    run_wsgi_app(application)

if __name__ == '__main__':
    main()

