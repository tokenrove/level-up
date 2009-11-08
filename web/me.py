
import os
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app

import data

class CharacterHandler(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        character = data.Character.by_user(user).get()
        if character == None: return self.redirect("/me/create")

        path = os.path.join(os.path.dirname(__file__), 'profile.html')
        self.response.out.write(template.render(path, { 'me': character,
                                                        'metrics': data.Metric.by_user(user).fetch(50) }))


class CreatorHandler(webapp.RequestHandler):
    def get(self):
        path = os.path.join(os.path.dirname(__file__), 'create.html')
        self.response.out.write(template.render(path, { 'user': users.get_current_user() }))

    def post(self):
        user = users.get_current_user()
        character = data.Character.by_user(user).get()
        if character == None:
            character = data.Character(owner=user, gatherer_code=data.fresh_gatherer_code())
        character.heroic_alias = self.request.get('heroic_alias')
        character.sex = self.request.get('sex')
        character.put()
        self.redirect('/me')


class InvalidateHandler(webapp.RequestHandler):
    def get(self):
        character = data.Character.by_user(users.get_current_user()).get()
        if character == None: return self.redirect("/me/create")
        character.gatherer_code = data.fresh_gatherer_code()
        character.put()
        self.redirect('/me')


def main():
    application = webapp.WSGIApplication([('/me', CharacterHandler),
                                          ('/me/invalidate', InvalidateHandler),
                                          ('/me/create', CreatorHandler)],
                                         debug=True)
    run_wsgi_app(application)

if __name__ == '__main__':
    main()

