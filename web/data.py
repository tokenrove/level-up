import os
import base64
import math
from google.appengine.ext import db

class OwnedModel(db.Model):
    owner = db.UserProperty(required=True)

    @classmethod
    def by_user(cls, user):
        return cls.all().filter('owner =', user)


def calculate_xp_percentage(jobs):
    xp_total = sum(map(lambda x: x.xp, jobs))
    return xp_total != 0 and map(lambda x: int(100.0*x.xp/xp_total), jobs) or []

# per http://code.activestate.com/recipes/576563/
def cached_property(f):
    """returns a cached property that is calculated by function f"""
    def get(self):
        try:
            return self._property_cache[f]
        except AttributeError:
            self._property_cache = {}
            x = self._property_cache[f] = f(self)
            return x
        except KeyError:
            x = self._property_cache[f] = f(self)
            return x
        
    return property(get)


class Archetype(db.Model):
    name = db.StringProperty(required=True)

    @cached_property
    def _static(self):
        #path = os.path.join(os.path.dirname(__file__), 'static/class/%s.json' % self.name)
        return {
            'programmer': {
                'sprite': '/images/fighter.gif'
                },
            'musician': {
                'sprite': '/images/mage.gif'
                }
            }.get(self.name, lambda: {})


class Job(OwnedModel):
    archetype = db.ReferenceProperty(Archetype, required=True)
    level = db.IntegerProperty(default=1)
    xp = db.IntegerProperty(default=0)
    xp_to_next_level = db.IntegerProperty(default=1000)

    def gain_xp(self, value):
        self.xp += value
        while(self.xp >= self.xp_to_next_level):
            self.xp -= self.xp_to_next_level
            self.xp_to_next_level = int(self.xp_to_next_level + math.ceil(self.xp_to_next_level * 1.3))
            self.level_up()
        self.put()

    def level_up(self):
        self.level += 1
        self.put()
        FeedEvent(owner=self.owner, type='level up', value=str(self.level), job=self).put()

class FeedEvent(OwnedModel):
    type = db.StringProperty(required=True)
    value = db.StringProperty()
    job = db.ReferenceProperty(Job)
    created = db.DateTimeProperty(auto_now_add=True)

class Metric(OwnedModel):
    name = db.StringProperty(required=True)
    type = db.StringProperty(default='client') # may be client, server, or manual
    ratio_n = db.IntegerProperty(default=1)
    ratio_d = db.IntegerProperty(default=1)
    unit = db.StringProperty()
    connected_to = db.ReferenceProperty(Job)

    def log(self, value):
        txn = MetricTxn(owner=self.owner,
                        metric=self,
                        value=int((value*self.ratio_n)/self.ratio_d),
                        job=self.connected_to)
        txn.put()
        txn.apply()

class MetricTxn(OwnedModel):
    metric = db.ReferenceProperty(Metric, required=True)
    created = db.DateTimeProperty(auto_now_add=True)
    value = db.IntegerProperty(required=True)
    job = db.ReferenceProperty(Job)

    def apply(self):
        if self.job: self.job.gain_xp(self.value)

class VisualProperties(db.Model):
    height_in_cm = db.FloatProperty()
    weight_in_kg = db.FloatProperty()
    skin_color = db.StringProperty()
    hair_color = db.StringProperty()
    eye_color = db.StringProperty()
    favorite_color = db.StringProperty()

class Character(OwnedModel):
    # decoration
    heroic_alias = db.StringProperty()
    sex = db.StringProperty(choices=set(["male","female","other"])) # not bool in case a third sex joins
    visual_properties = VisualProperties()
    location = db.GeoPtProperty()
    # metrics
    gatherer_code = db.StringProperty(required=True)

    def register_metric(self, name, unit, ratio='1:1', type='client'):
        metric = Metric.all().filter('owner =', self.owner).filter('name =', name).get();
        if metric == None:
            (ratio_n, ratio_d) = map(int, ratio.split(':'))
            metric = Metric(owner=self.owner, name=name, unit=unit, ratio_n=ratio_n, ratio_d=ratio_d, type=type)
            metric.put()
        return metric

    @classmethod
    def by_code(cls, code):
        return cls.all().filter('gatherer_code =', code)

def fresh_gatherer_code():
    r = base64.urlsafe_b64encode(os.urandom(8))
    assert Character.by_code(r).count(1) == 0 # XXX not the right thing, but better than nothing.
    return r
