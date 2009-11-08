import os
from google.appengine.ext.webapp import template

def handle_with_template(response, file, values):
    response.out.write(template.render(os.path.join(os.path.dirname(__file__), file),
                                       values))

## XXX eventually this will do more, like communicating status back to the client-side
def complain_and_redirect(obj):
    obj.redirect('/me')
