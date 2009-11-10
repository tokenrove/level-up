

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
import xml.etree.ElementTree

import data
import util

max_results = 50

class MainHandler(util.RequestHandler):
    def generate_hall_of_heroes(self):
        # XXX should perhaps be ordered by sum of levels minus number of jobs?
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
                                    'news': data.SiteNews.all().order('-created').fetch(5),
                                    'archetype': top_job and top_job.archetype._static,
                                    'hall_of_heroes': self.generate_hall_of_heroes(),
                                    'login_url': user and users.create_logout_url("/") or
                                                          users.create_login_url("/me"),
                                    'adminp': users.is_current_user_admin()
                                    })


class NewClassHandler(util.RequestHandler):
    def post(self):
        assert users.is_current_user_admin()
        name = self.request.get('name')
        if len(name) < 2: return self.complain_and_redirect()
        if data.Archetype.all().filter('name =', name).count(1) == 0:
            data.Archetype(name=name).put()
        self.redirect_back()


class PostNewsHandler(util.RequestHandler):
    def post(self):
        assert users.is_current_user_admin()
        data.SiteNews(title=self.request.get('title'),
                      body=self.request.get('body')).put()
        self.redirect('/')

class MigrationHandler(util.RequestHandler):
    def post(self):
        assert users.is_current_user_admin()
        fn = self.request.get('fn')
        assert fn in data.migration_fns
        self.response.out.write('''
Eventually this will fork a task instead of doing this here.
However, this is not the case presently, so here's your output:
''')
        data.migration_fns[fn](self.response.out)


class FeedHandler(util.RequestHandler):
    def get(self):
        character = data.Character.get(self.request.get('key'))
        events = data.FeedEvent.all().filter('owner =',character.owner).order('-created').fetch(max_results)
        self.response.headers['content-type'] = 'text/xml; charset="utf-8"'
        self.handle_with_template('feed.xml',
                                  { 'me': character,
                                    'updated': events and events[0].created or 'never',
                                    'events': events })

def main():
    application = webapp.WSGIApplication([('/', MainHandler),
                                          ('/admin/new-class', NewClassHandler),
                                          ('/admin/post-news', PostNewsHandler),
                                          ('/admin/migrate', MigrationHandler),
                                          ('/feed.xml', FeedHandler)],
                                         debug=True)
    run_wsgi_app(application)

if __name__ == '__main__':
    main()

