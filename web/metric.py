

import os
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app

class GathererHandler(webapp.RequestHandler):
    def get(self):
        self.error(405)

    def post(self):
        self.response.out.write('Accepted!')

def main():
    application = webapp.WSGIApplication([('/metric', GathererHandler)], debug=True)
    run_wsgi_app(application)

if __name__ == '__main__':
    main()
