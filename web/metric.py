

import os
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app

import data

class GathererHandler(webapp.RequestHandler):
    def get(self):
        self.error(405)

    def post(self):
        character = data.Character.by_code(self.request.get('code')).get()
        if character == None: return self.error(403)

        metric = character.register_metric(self.request.get('metric'))
        metric.log(self.request.get('value'), self.request.get('unit'))

        path = os.path.join(os.path.dirname(__file__), 'accepted.html')
        self.response.out.write(template.render(path,
                                                { 'metric': self.request.get('metric'),
                                                  'character': character,
                                                  'value': self.request.get('value'),
                                                  'unit': self.request.get('unit') }))

def main():
    application = webapp.WSGIApplication([('/metric', GathererHandler)], debug=True)
    run_wsgi_app(application)

if __name__ == '__main__':
    main()
