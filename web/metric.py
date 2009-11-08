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
        metric.connect_to = data.Job.get(job) or None
        metric.put()
        redirect_back()

    def get(self):
        handle_with_template('connect.html',
                             { 'me': data.Character.by_user(users.get_current_user()).get(),
                               'jobs': data.Job.by_user(users.get_current_user()).fetch(max_results),
                               'metric' : data.Metric.get(self.request.get('key')) })

class DeleteHandler(util.RequestHandler):
    def get(self):
        metric = data.Metric.get(self.request.get('key'))
        assert metric.owner == users.get_current_user()
        metric.delete()
        redirect_back()

class TxnsHandler(util.RequestHandler):
    def get(self):
        key = self.request.get('key')
        util.handle_with_template(self.response, 'txns.html',
                                  { 'metric': data.Metric.get(key),
                                    'txns': data.MetricTxn.by_user(users.get_current_user()).filter('metric =',key).order('-created').fetch(max_results) })


class ViewHandler(webapp.RequestHandler):
    def get(self):
        util.handle_with_template(self.response, 'metrics.html',
                                  { 'metrics': data.Metric.by_user(users.get_current_user()).fetch(max_results),
                                    'count': data.Metric.by_user(users.get_current_user()).count(1000) })



class GathererHandler(webapp.RequestHandler):
    def post(self):
        character = data.Character.by_code(self.request.get('code')).get()
        if character == None: return self.error(403)

        value = int(self.request.get('value'))
        metric = character.register_metric(self.request.get('metric'))
        metric.log(value, self.request.get('unit'))

        util.handle_with_template(self.response, 'accepted.html',
                                  { 'metric': self.request.get('metric'),
                                    'character': character,
                                    'value': value,
                                    'unit': self.request.get('unit') })

                                          
def main():
    application = webapp.WSGIApplication([('/me/metrics', ViewHandler),
                                          ('/me/metrics/connect', ConnectHandler),
                                          ('/me/metrics/txns', TxnsHandler),
                                          ('/me/metrics/delete', DeleteHandler),
                                          ('/metric', GathererHandler)],
                                         debug=True)
    run_wsgi_app(application)

if __name__ == '__main__':
    main()
