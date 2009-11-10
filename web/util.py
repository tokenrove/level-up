import os
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template

# XXX would love for this to be list.unique, but you can't extend list...
def unique(list, key_fn=lambda x: x):
    return reduce(lambda x,y: key_fn(y) in [key_fn(z) for z in x] and x or (x.append(y),x)[1],
                  list, [])

class RequestHandler(webapp.RequestHandler):
    ## XXX eventually this will do more, like communicating status back to the client-side
    def complain_and_redirect(self):
        self.redirect_back()

    def redirect_back(self):
        self.redirect(self.request.get('back') or '/me')

    def handle_with_template(self, file, values):
        self.response.out.write(template.render(os.path.join(os.path.dirname(__file__), file),
                                                values))
