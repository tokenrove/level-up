
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
    sex = db.StringProperty() # not bool in case a third sex joins
    visualProperties = VisualProperties()
    location = db.GeoPtProperty()


class CharacterHandler(webapp.RequestHandler):
    def get(self):
        assert users.get_current_user()

        character = Character.all().filter('owner =', users.get_current_user()).get()
        if character == None:
            return self.redirect("/me/create")

        template_values = {
            'me': character
            }
        path = os.path.join(os.path.dirname(__file__), 'profile.html')
        self.response.out.write(template.render(path, template_values))

class CreatorHandler(webapp.RequestHandler):
    def get(self):
        template_values = {
            'user': users.get_current_user()
            }
        path = os.path.join(os.path.dirname(__file__), 'create.html')
        self.response.out.write(template.render(path, template_values))

    def post(self):
        character = Character.all().filter('owner =', users.get_current_user()).get()
        if character == None:
            character = Character(owner=users.get_current_user())
        character.heroicAlias = self.request.get('heroicAlias')
        character.sex = self.request.get('sex')
        character.put()
        self.redirect('/me')

def main():
    application = webapp.WSGIApplication([('/me', CharacterHandler),
                                          ('/me/create', CreatorHandler)],
                                         debug=True)
    run_wsgi_app(application)

if __name__ == '__main__':
    main()

