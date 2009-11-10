

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
import xml.etree.ElementTree

import data
import util

max_results = 50

class MainHandler(util.RequestHandler):
    def generate_hall_of_heroes(self):
        jobs = data.Job.all().order('-level').fetch(max_results)
        return map(lambda x: { 'character': data.Character.by_user(x.owner).get(),
                               'archetype': x.archetype._static,
                               'primary_class': x,
                               'secondary_classes': filter(lambda y: y.key() != x.key(),
                                                           data.Job.by_user(x.owner).order('-level').fetch(max_results)) },
                   util.unique(jobs,key_fn=lambda x: x.owner)[0:10])

    def get(self):
        user = users.get_current_user()
        top_job = data.Job.by_user(user).order('-level').get()

        self.handle_with_template('index.html',
                                  { 'user': user,
                                    'archetype': top_job and top_job.archetype._static,
                                    'hall_of_heroes': self.generate_hall_of_heroes(),
                                    'login_url': user and users.create_logout_url("/") or
                                                          users.create_login_url("/me"),
                                    'adminp': users.is_current_user_admin()
                                    })


class NewClassHandler(util.RequestHandler):
    def post(self):
        name = self.request.get('name')
        if len(name) < 2: return self.complain_and_redirect()
        if users.is_current_user_admin() and data.Archetype.all().filter('name =', name).count(1) == 0:
            data.Archetype(name=name).put()
        self.redirect_back()


class FeedHandler(util.RequestHandler):
    def get(self):
        user = data.Character.get(self.request.get('key')).owner
        events = data.FeedEvent.all().filter('owner =',user).order('-created').fetch(max_results)
        self.response.out.write(str(map(lambda x: x.type, events)))

def main():
    application = webapp.WSGIApplication([('/', MainHandler),
                                          ('/admin/new-class', NewClassHandler),
                                          ('/feed', FeedHandler)],
                                         debug=True)
    run_wsgi_app(application)

if __name__ == '__main__':
    main()

