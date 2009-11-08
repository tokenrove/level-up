import os
import base64
from google.appengine.ext import db

@classmethod
def by_user(cls, user):
    return cls.all().filter('owner =', user)
db.Model.by_user = by_user

class VisualProperties(db.Model):
    height_in_cm = db.FloatProperty()
    weight_in_kg = db.FloatProperty()
    skin_color = db.StringProperty()
    hair_color = db.StringProperty()
    eye_color = db.StringProperty()
    favorite_color = db.StringProperty()

class Metric(db.Model):
    owner = db.UserProperty(required=True)
    name = db.StringProperty(required=True)
    unit = db.StringProperty()

    def log(self, value, unit):
        # do nothing
        return

class Character(db.Model):
    owner = db.UserProperty(required=True)
    # decoration
    heroic_alias = db.StringProperty()
    sex = db.StringProperty(choices=set(["male","female","other"])) # not bool in case a third sex joins
    visual_properties = VisualProperties()
    location = db.GeoPtProperty()
    # metrics
    gatherer_code = db.StringProperty(required=True)
    metrics = db.ListProperty(db.Key)
    # classes
    classes = db.ListProperty(db.Key)

    def register_metric(self, name):
        metric = Metric.all().filter('owner =', self.owner).filter('name =', name).get();
        if metric == None:
            metric = Metric(owner=self.owner, name=name)
            metric.put()
            self.metrics.append(metric.key())
            self.put()
        return metric

    @classmethod
    def by_code(cls, code):
        return cls.all().filter('gatherer_code =', code)

def fresh_gatherer_code():
    r = base64.urlsafe_b64encode(os.urandom(8))
    assert Character.by_code(r) == None # XXX not the right thing, but better than nothing.
    return r
