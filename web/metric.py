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
        job = data.Job.get(self.request.get('job')) or None
        metric = data.Metric.get(self.request.get('key'))
        user=users.get_current_user()
        assert metric.owner == user
        txns = data.MetricTxn.by_user(user).filter('metric =',metric).order('created').fetch(max_results)
        map(lambda txn: txn.change_job(job), txns)
        metric.connected_to = job
        metric.put()
        self.redirect_back()

    def get(self):
        self.handle_with_template('metric/connect.html',
                                  { 'me': data.Character.by_user(users.get_current_user()).get(),
                                    'jobs': data.Job.by_user(users.get_current_user()).order('-level').fetch(max_results),
                                    'metric' : data.Metric.get(self.request.get('key')) })

class AddHandler(util.RequestHandler):
    def post(self):
        user=users.get_current_user()
        type = self.request.get('type')
        assert type in ['manual','client','server']
        name = self.request.get('name')
        assert len(name) > 2
        metric = data.Metric(owner=user,
                             name=name,
                             unit=self.request.get('unit'),
                             ratio_n=int(self.request.get('ratio_n')) or 1,
                             ratio_d=int(self.request.get('ratio_d')) or 1,
                             type=type)
        job = self.request.get('job') and data.Job.get(self.request.get('job'))
        if job: metric.connected_to = job
        metric.put()
        self.redirect_back()

    def get(self):
        user=users.get_current_user()
        self.handle_with_template('metric/add.html',
                                  { 'me': data.Character.by_user(user).get(),
                                    'jobs': data.Job.by_user(user).order('-level').fetch(max_results),
                                    'default_job': self.request.get('default_job') })

class EditHandler(util.RequestHandler):
    def post(self):
        metric = data.Metric.get(self.request.get('key'))
        assert metric.owner == users.get_current_user()
        for x in ['name','unit']:
            metric.__setattr__(x, self.request.get(x))
        metric.ratio_n=int(self.request.get('ratio_n')) or 1
        metric.ratio_d=int(self.request.get('ratio_d')) or 1
        metric.put()
        self.redirect_back()

    def get(self):
        user=users.get_current_user()
        self.handle_with_template('metric/edit.html',
                                  { 'me': data.Character.by_user(user).get(),
                                    'metric': data.Metric.get(self.request.get('key')) })


class DeleteHandler(util.RequestHandler):
    def get(self):
        metric = data.Metric.get(self.request.get('key'))
        assert metric.owner == users.get_current_user()
        metric.delete()
        self.redirect_back()


class MergeHandler(util.RequestHandler):
    def post(self):
        metric = data.Metric.get(self.request.get('key'))
        destination = data.Metric.get(self.request.get('destination'))
        user = users.get_current_user()
        assert metric.owner == user and destination.owner == user
        txns = data.MetricTxn.by_user(user).filter('metric =',metric).order('created').fetch(max_results)
        map(lambda txn: txn.change_metric(destination), txns)
        metric.delete()
        self.redirect_back()

    def get(self):
        user=users.get_current_user()
        metric = data.Metric.get(self.request.get('key'))
        self.handle_with_template('metric/merge.html',
                                  { 'me': data.Character.by_user(user).get(),
                                    'metric': metric,
                                    'others': filter(lambda x: x.key() != metric.key(), data.Metric.by_user(users.get_current_user()).fetch(max_results)) })


class TxnsHandler(util.RequestHandler):
    def get(self):
        user = users.get_current_user()
        key = self.request.get('key')
        metric = data.Metric.get(key)
        txns = data.MetricTxn.by_user(user).filter('metric =',metric).order('-created').fetch(max_results)
        txn_values = map(lambda x: (x.value,(x.created-txns[-1].created).seconds), txns)
        txn_values.reverse()
        if len(txn_values) > 0:
            u,v = (min([x[0] for x in txn_values]),max([x[0] for x in txn_values])) or (0,0)
            m,n = (txn_values[0][1],txn_values[-1][1])
        else: u,v,m,n = 0,0,0,0
        self.handle_with_template('metric/txns.html',
                                  { 'metric': metric,
                                    'txn_values': (v > u) and map(lambda x: 100.0*(float(x[0]-u)/(v-u)), txn_values),
                                    'txn_times': (n > m) and map(lambda x: 100.0*(float(x[1]-m)/(n-m)), txn_values) or [],
                                    'txns': txns })


class ViewHandler(util.RequestHandler):
    def get(self):
        self.handle_with_template('metric/view.html',
                                  { 'metrics': data.Metric.by_user(users.get_current_user()).fetch(max_results),
                                    'count': data.Metric.by_user(users.get_current_user()).count(1000) })



class GathererHandler(util.RequestHandler):
    def post(self):
        character = data.Character.by_code(self.request.get('code')).get()
        if character == None: return self.error(403)

        value = int(self.request.get('value'))
        name = self.request.get('metric')
        assert len(name) > 2
        unit = self.request.get('unit')
        ratio = self.request.get('ratio') or '1:1'
        metric = character.register_metric(name, unit, ratio, type='client')
        metric.log(value)

        self.handle_with_template('metric/accepted.html',
                                  { 'metric': metric,
                                    'character': character,
                                    'value': value,
                                    'unit': unit })

class ManualHandler(util.RequestHandler):
    def post(self):
        value = int(self.request.get('value'))
        metric = data.Metric.get(self.request.get('key'))
        metric.log(value)
        self.redirect_back()

    def get(self):
        user=users.get_current_user()
        self.handle_with_template('metric/manual.html',
                                  { 'metric': data.Metric.get(self.request.get('key')) })


class RollbackHandler(util.RequestHandler):
    def get(self):
        txn = data.MetricTxn.get(self.request.get('key'))
        txn.rollback()
        txn.delete()
        self.redirect_back()

def main():
    application = webapp.WSGIApplication([('/me/metric', ViewHandler),
                                          ('/me/metric/connect', ConnectHandler),
                                          ('/me/metric/txns', TxnsHandler),
                                          ('/me/metric/delete', DeleteHandler),
                                          ('/me/metric/merge', MergeHandler),
                                          ('/me/metric/add', AddHandler),
                                          ('/me/metric/edit', EditHandler),
                                          ('/me/metric/rollback', RollbackHandler),
                                          ('/me/metric/manual', ManualHandler),
                                          ('/metric', GathererHandler)],
                                         debug=True)
    run_wsgi_app(application)

if __name__ == '__main__':
    main()

