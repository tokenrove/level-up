

import os
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app

class VisualProperties(db.Model):
    heightInCm = db.FloatProperty()
    weightInKg = db.FloatProperty()
    skinColor = db.StringProperty()
    hairColor = db.StringProperty()
    eyeColor = db.StringProperty()
    favoriteColor = db.StringProperty()

class Metric(db.Model):
    owner = db.UserProperty(required=True)

class Character(db.Model):
    owner = db.UserProperty(required=True)
    heroicAlias = db.StringProperty()
    visualProperties = VisualProperties()
    location = db.GeoPtProperty()


class MainHandler(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()

        template_values = {
            'name': user or 'unnamed',
            'login_url': (user and users.create_logout_url("/") or users.create_login_url("/")),
            'login_text': (user and 'Sign-out' or 'Login'),
            'adminp': users.is_current_user_admin()
            }
        path = os.path.join(os.path.dirname(__file__), 'index.html')
        self.response.out.write(template.render(path, template_values))

class ProfileHandler(webapp.RequestHandler):
    def get(self):
        template_values = { }
        path = os.path.join(os.path.dirname(__file__), 'profile.html')
        self.response.out.write(template.render(path, template_values))

class GathererHandler(webapp.RequestHandler):
    def get(self):
        self.response.clear()
        self.response.set_status(405)

    def post(self):
        self.response.out.write('Accepted!')

def main():
    application = webapp.WSGIApplication([('/', MainHandler),
                                          ('/profile', ProfileHandler),
                                          ('/gatherer', GathererHandler)],
                                         debug=True)
    run_wsgi_app(application)

if __name__ == '__main__':
    main()

