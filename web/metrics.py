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

class ConnectHandler(webapp.RequestHandler):
    def get(self):
        util.handle_with_template(self.response, 'connect.html',
                                  { 'me': data.Character.by_user(users.get_current_user()).get(),
                                    'jobs': data.Job.by_user(users.get_current_user()).fetch(max_results),
                                    'metric' : data.Metric.get(self.request.get('key')) })

class DeleteHandler(webapp.RequestHandler):
    def get(self):
        metric = data.Metric.get(self.request.get('key'))
        assert metric.owner == users.get_current_user()
        metric.delete()
        self.redirect('/me')

class TxnsHandler(webapp.RequestHandler):
    def get(self):
        util.handle_with_template(self.response, 'txns.html',
                                  { 'txns': data.MetricTxn.by_user(users.get_current_user()).filter('metric =',self.request.get('key')).order('-created').fetch(max_results) })


class ViewHandler(webapp.RequestHandler):
    def get(self):
        util.handle_with_template(self.response, 'metrics.html',
                                  { 'metrics': data.Metric.by_user(users.get_current_user()).fetch(max_results),
                                    'count': data.Metric.by_user(users.get_current_user()).count(1000) })



class GathererHandler(webapp.RequestHandler):
    def get(self):
        self.error(405)

    def post(self):
        character = data.Character.by_code(self.request.get('code')).get()
        if character == None: return self.error(403)

        metric = character.register_metric(self.request.get('metric'))
        metric.log(self.request.get('value'), self.request.get('unit'))

        util.handle_with_template(self.response, 'accepted.html',
                                  { 'metric': self.request.get('metric'),
                                    'character': character,
                                    'value': self.request.get('value'),
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

