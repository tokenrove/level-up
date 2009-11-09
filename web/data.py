import os
import base64
import math
from google.appengine.ext import db

class OwnedModel(db.Model):
    owner = db.UserProperty(required=True)

    @classmethod
    def by_user(cls, user):
        return cls.all().filter('owner =', user)


class Archetype(db.Model):
    name = db.StringProperty(required=True)

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
            self.level += 1
        self.put()


class Metric(OwnedModel):
    name = db.StringProperty(required=True)
    type = db.StringProperty(default='client') # may be client, server, or manual
    unit = db.StringProperty()
    connected_to = db.ReferenceProperty(Job)

    def log(self, value, unit):
        txn = MetricTxn(owner=self.owner,
                        metric=self,
                        value=value,
                        unit=unit,
                        job=self.connected_to)
        txn.put()
        txn.apply()

class MetricTxn(OwnedModel):
    metric = db.ReferenceProperty(Metric, required=True)
    created = db.DateProperty(auto_now_add=True)
    value = db.IntegerProperty(required=True)
    unit = db.StringProperty()
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

    def register_metric(self, name):
        metric = Metric.all().filter('owner =', self.owner).filter('name =', name).get();
        if metric == None:
            metric = Metric(owner=self.owner, name=name)
            metric.put()
        return metric

    @classmethod
    def by_code(cls, code):
        return cls.all().filter('gatherer_code =', code)

def fresh_gatherer_code():
    r = base64.urlsafe_b64encode(os.urandom(8))
    assert Character.by_code(r).count(1) == 0 # XXX not the right thing, but better than nothing.
    return r
