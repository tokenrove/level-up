import os
import base64
import math
import datetime
import random
from google.appengine.ext import db

class OwnedModel(db.Model):
    owner = db.UserProperty(required=True)

    @classmethod
    def by_user(cls, user):
        return cls.all().filter('owner =', user)


# XXX rework to calculate xp of metrics contributing to a level up
def calculate_xp_percentage(metrics):
    subtotals = map(lambda m: sum([x.value for x in MetricTxn.all().filter('metric = ', m)]), metrics)
    total = sum(subtotals)
    return total != 0 and map(lambda x: int(100.0*x/total), subtotals) or []

def calculate_level_percentage(jobs):
    total = sum(map(lambda x: x.level, jobs))
    return total != 0 and map(lambda x: int(100.0*x.level/total), jobs) or []

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
        # XXX eventually, load from /static
        #path = os.path.join(os.path.dirname(__file__), 'static/class/%s.json' % self.name)
        return {
            'programmer': {
                'sprite': '/images/bmage.png',
                'stats': {'constitution':-1, 'charisma':-1, 'intellect':1, 'perception':1, 'patience':1 } },
            'musician': {
                'sprite': '/images/thief.png',
                'stats': {'dexterity':1, 'charisma':1, 'wisdom':-1} },
            'writer': {
                'sprite': '/images/rmage.png',
                'stats': {'intellect':1, 'wisdom':1, 'charisma':1, 'might':-1, 'constitution':-1} },
            'artist': {
                'sprite': '/images/wmage.png',
                'stats': {'dexterity':1, 'wisdom':-1, 'perception':1, 'charisma':1} },
            'trainer' : {
                'sprite': '/images/ninja.png',
                'stats': {'might':1, 'constitution':1, 'charisma':1, 'intellect':-1, 'wisdom':-1, 'perception':-1} },
            'scholar' : {
                'sprite': '/images/sage.png',
                'stats': {'intellect':1, 'wisdom':1, 'charisma':-1, 'perception':-1 } }
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
            self.xp_to_next_level = int(self.xp_to_next_level + self.level*1000)
            self.level_up()
        self.put()

    def level_up(self):
        self.level += 1
        self.put()
        char = Character.by_user(self.owner).get()
        char.gain_stats(self.archetype._static['stats'])
        FeedEvent(owner=self.owner, type='level up', value=str(self.level),
                  xp_to_next_level=self.xp_to_next_level-self.xp, job=self).put()

class FeedEvent(OwnedModel):
    type = db.StringProperty(required=True)
    value = db.StringProperty()
    xp_to_next_level = db.IntegerProperty()
    job = db.ReferenceProperty(Job)
    created = db.DateTimeProperty(auto_now_add=True)

class SiteNews(db.Model):
    title = db.StringProperty(required=True)
    body = db.TextProperty(required=True)
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

attributes = ['might', 'dexterity', 'constitution', 'intellect', 'wisdom', 'charisma', 'perception', 'patience']

class Character(OwnedModel):
    # decoration
    heroic_alias = db.StringProperty()
    sex = db.StringProperty(choices=set(["male","female","other"])) # not bool in case a third sex joins
    visual_properties = VisualProperties()
    location = db.GeoPtProperty()
    created = db.DateProperty(auto_now_add=True)
    # metrics
    gatherer_code = db.StringProperty(required=True)
    # stats
    might = db.IntegerProperty(default=1)
    dexterity = db.IntegerProperty(default=1)
    constitution = db.IntegerProperty(default=1)
    intellect = db.IntegerProperty(default=1)
    wisdom = db.IntegerProperty(default=1)
    charisma = db.IntegerProperty(default=1)
    perception = db.IntegerProperty(default=1)
    patience = db.IntegerProperty(default=1)

    def register_metric(self, name, unit, ratio='1:1', type='client'):
        metric = Metric.all().filter('owner =', self.owner).filter('name =', name).get();
        if metric == None:
            (ratio_n, ratio_d) = map(int, ratio.split(':'))
            metric = Metric(owner=self.owner, name=name, unit=unit, ratio_n=ratio_n, ratio_d=ratio_d, type=type)
            metric.put()
        return metric

    def gain_stats(self, bonuses):
        for stat in attributes:
            v = random.random() + (bonuses.get(stat, 0) * 0.2)
            if v > 0.7: self.__setattr__(stat, 1+getattr(self, stat))
        self.put()
        return

    @classmethod
    def by_code(cls, code):
        return cls.all().filter('gatherer_code =', code)

def fresh_gatherer_code():
    r = base64.urlsafe_b64encode(os.urandom(8))
    assert Character.by_code(r).count(1) == 0 # XXX not the right thing, but better than nothing.
    return r


# XXX this is what a lack of usable lambdas has done to us, you fools!
def character_created(out):
    out.write("<pre>\n")
    for char in Character.all():
        #out.write("%s (%s) created %s\n" % (char.key(), char.heroic_alias, char.created))
        if not char.created:
            char.created = datetime.datetime.now()
            char.put()
            out.write("Updated %s (%s)\n" % (char.key(), char.heroic_alias))
    out.write("\n</pre>\n")

migration_fns = { 'character_created': character_created }
