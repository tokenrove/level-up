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

class ConnectHandler(util.RequestHandler):
    def post(self):
        job = self.request.get('job')
        metric = data.Metric.get(self.request.get('key'))
        metric.connected_to = job and data.Job.get(job) or None
        metric.put()
        self.redirect_back()

    def get(self):
        self.handle_with_template('connect.html',
                                  { 'me': data.Character.by_user(users.get_current_user()).get(),
                                    'jobs': data.Job.by_user(users.get_current_user()).order('-level').fetch(max_results),
                                    'metric' : data.Metric.get(self.request.get('key')) })

class AddHandler(util.RequestHandler):
    def post(self):
        user=users.get_current_user()
        type = self.request.get('type')
        assert type in ['manual','client','server']
        metric = data.Metric(owner=user,
                             name=self.request.get('name'),
                             unit=self.request.get('unit'),
                             type=type)
        job = self.request.get('job') and data.Job.get(self.request.get('job'))
        if job: metric.connected_to = job
        metric.put()
        self.redirect_back()

    def get(self):
        user=users.get_current_user()
        self.handle_with_template('add.html',
                                  { 'me': data.Character.by_user(user).get(),
                                    'jobs': data.Job.by_user(user).order('-level').fetch(max_results),
                                    'default_job': self.request.get('default_job') })

class DeleteHandler(util.RequestHandler):
    def get(self):
        metric = data.Metric.get(self.request.get('key'))
        assert metric.owner == users.get_current_user()
        metric.delete()
        self.redirect_back()

class TxnsHandler(util.RequestHandler):
    def get(self):
        key = self.request.get('key')
        metric = data.Metric.get(key)
        self.handle_with_template('txns.html',
                                  { 'metric': metric,
                                    'txns': data.MetricTxn.by_user(users.get_current_user()).filter('metric =',metric).order('-created').fetch(max_results) })


class ViewHandler(util.RequestHandler):
    def get(self):
        self.handle_with_template('metrics.html',
                                  { 'metrics': data.Metric.by_user(users.get_current_user()).fetch(max_results),
                                    'count': data.Metric.by_user(users.get_current_user()).count(1000) })



class GathererHandler(util.RequestHandler):
    def post(self):
        character = data.Character.by_code(self.request.get('code')).get()
        if character == None: return self.error(403)

        value = int(self.request.get('value'))
        unit = self.request.get('unit')
        metric = character.register_metric(self.request.get('metric'))
        metric.log(value, unit)

        self.handle_with_template('accepted.html',
                                  { 'metric': metric,
                                    'character': character,
                                    'value': value,
                                    'unit': unit })

class ManualHandler(util.RequestHandler):
    def post(self):
        value = int(self.request.get('value'))
        metric = data.Metric.get(self.request.get('key'))
        metric.log(value, metric.unit)
        self.redirect_back()

    def get(self):
        user=users.get_current_user()
        self.handle_with_template('manual.html',
                                  { 'metric': data.Metric.get(self.request.get('key')) })


class RollbackHandler(util.RequestHandler):
    def get(self):
        self.response.out.write('Not here yet, but eventually this will let you undo and repeat transactions.')

def main():
    application = webapp.WSGIApplication([('/me/metrics', ViewHandler),
                                          ('/me/metrics/connect', ConnectHandler),
                                          ('/me/metrics/txns', TxnsHandler),
                                          ('/me/metrics/delete', DeleteHandler),
                                          ('/me/metrics/add', AddHandler),
                                          ('/me/metrics/rollback', RollbackHandler),
                                          ('/me/metrics/manual', ManualHandler),
                                          ('/metric', GathererHandler)],
                                         debug=True)
    run_wsgi_app(application)

if __name__ == '__main__':
    main()

