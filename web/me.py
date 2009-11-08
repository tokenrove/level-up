
import os
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.ext.webapp.util import run_wsgi_app

import data
import util

## XXX at some point this should be carefully tweaked per value,
## preference-ized by user, et cetera.  But for now, this will do.
max_results = 50

class ProfileHandler(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        character = data.Character.by_user(user).get()
        if character == None: return self.redirect("/me/create")

        available_archetypes = data.Archetype.all().fetch(max_results)
        unconnected_metrics = data.Metric.by_user(user).filter('connected_to =',None).fetch(max_results)
        util.handle_with_template(self.response, 'profile.html',
                                  { 'me': character,
                                    'jobs': data.Job.by_user(user).order('-level').fetch(max_results),
                                    'adminp': users.is_current_user_admin(),
                                    'available_archetypes': available_archetypes,
                                    'unconnected_metrics': unconnected_metrics })

class NewJobHandler(webapp.RequestHandler):
    def post(self):
        user = users.get_current_user()
        character = data.Character.by_user(user).get()
        if character == None: return self.redirect("/me/create")

        archetype = data.Archetype.all().filter('name =', self.request.get('archetype')).get()
        if archetype == None: return util.complain_and_redirect(self)
        if data.Job.by_user(user).filter('archetype =', archetype).count(1) != 0:
            return util.complain_and_redirect(self)
        data.Job(owner=user, archetype=archetype).put()
        self.redirect('/me')


class CreatorHandler(webapp.RequestHandler):
    def get(self):
        util.handle_with_template(self.response, 'create.html', { 'user': users.get_current_user() })

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


class JobViewHandler(webapp.RequestHandler):
    def get(self):
        self.response.out.write('Got this path: '+self.request.path)

def main():
    application = webapp.WSGIApplication([('/me', ProfileHandler),
                                          ('/me/invalidate', InvalidateHandler),
                                          ('/me/new-job', NewJobHandler),
                                          ('/me/job', JobViewHandler),
                                          ('/me/create', CreatorHandler)],
                                         debug=True)
    run_wsgi_app(application)

if __name__ == '__main__':
    main()

