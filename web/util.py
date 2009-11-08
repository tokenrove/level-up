import os
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template

class RequestHandler(webapp.RequestHandler):
    ## XXX eventually this will do more, like communicating status back to the client-side
    def complain_and_redirect(self):
        self.redirect_back()

    def redirect_back(self):
        self.redirect(self.request.get('back') or '/me')

    def handle_with_template(self, file, values):
        self.response.out.write(template.render(os.path.join(os.path.dirname(__file__), file),
                                                values))
