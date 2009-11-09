
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

class ProfileHandler(util.RequestHandler):
    def get(self):
        user = users.get_current_user()
        character = data.Character.by_user(user).get()
        if character == None: return self.redirect("/me/create")

        jobs = data.Job.by_user(user).order('-level').fetch(max_results)
        available_archetypes = filter(lambda x: x.name not in map(lambda y: y.archetype.name, jobs),
                                      data.Archetype.all().fetch(max_results))
        unconnected_metrics = data.Metric.by_user(user).filter('connected_to =',None).fetch(max_results)
        xp_total = sum(map(lambda x: x.xp, jobs))
        xp_percentage = map(lambda x: int(100.0*x.xp/xp_total), jobs)
        self.handle_with_template('profile.html',
                                  { 'me': character,
                                    'jobs': jobs,
                                    'job_names': map(lambda x: x.archetype.name, jobs),
                                    'xp_percentage': xp_percentage,
                                    'adminp': users.is_current_user_admin(),
                                    'available_archetypes': available_archetypes,
                                    'unconnected_metrics': unconnected_metrics })

class NewJobHandler(util.RequestHandler):
    def post(self):
        user = users.get_current_user()
        character = data.Character.by_user(user).get()
        if character == None: return self.redirect("/me/create")

        archetype = data.Archetype.all().filter('name =', self.request.get('archetype')).get()
        if archetype == None: return self.complain_and_redirect()
        if data.Job.by_user(user).filter('archetype =', archetype).count(1) != 0:
            return self.complain_and_redirect()
        data.Job(owner=user, archetype=archetype).put()
        self.redirect_back()

class JobViewHandler(util.RequestHandler):
    def get(self):
        user = users.get_current_user()
        job = data.Job.get(self.request.get('key'))
        assert(job.owner == user)
        self.handle_with_template('job.html', { 'job': job,
                                                'metrics': data.Metric.by_user(user).filter('connected_to =', job).fetch(max_results) })



class CreatorHandler(util.RequestHandler):
    def get(self):
        self.handle_with_template('create.html', { 'user': users.get_current_user() })

    def post(self):
        user = users.get_current_user()
        character = data.Character.by_user(user).get()
        if character == None:
            character = data.Character(owner=user, gatherer_code=data.fresh_gatherer_code())
        character.heroic_alias = self.request.get('heroic_alias')
        character.sex = self.request.get('sex')
        character.put()
        self.redirect('/me')


class EditHandler(util.RequestHandler):
    def get(self):
        user = users.get_current_user()
        character = data.Character.by_user(user).get()
        self.handle_with_template('edit.html', { 'me': character })

    def post(self):
        user = users.get_current_user()
        character = data.Character.by_user(user).get()
        assert character
        character.heroic_alias = self.request.get('heroic_alias')
        character.sex = self.request.get('sex')
        character.put()
        self.redirect('/me')


class InvalidateHandler(util.RequestHandler):
    def get(self):
        character = data.Character.by_user(users.get_current_user()).get()
        if character == None: return self.redirect("/me/create")
        character.gatherer_code = data.fresh_gatherer_code()
        character.put()
        self.redirect_back()


def main():
    application = webapp.WSGIApplication([('/me', ProfileHandler),
                                          ('/me/edit', EditHandler),
                                          ('/me/invalidate', InvalidateHandler),
                                          ('/me/job/new', NewJobHandler),
                                          ('/me/job', JobViewHandler),
                                          ('/me/create', CreatorHandler)],
                                         debug=True)
    run_wsgi_app(application)

if __name__ == '__main__':
    main()

