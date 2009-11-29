from trac.core import *
from trac.ticket.api import ITicketChangeListener
from trac.config import Option, ListOption
import os
import urllib
import urllib2

class LevelUpBugFixGathererPlugin(Component):
    implements(ITicketChangeListener)

    url = Option('level_up', 'submit_url', default='https://level-up.appspot.com/metric',
                 doc='The URL to which metrics should be posted.')
    authors = ListOption('level_up', 'authors', default=['tek'],
                         doc='The author names to match -- in the same order as gatherer_codes.')
    resolution = Option('level_up', 'resolution', default='fixed',
                        doc='Resolution state to match.')
    gatherer_codes = ListOption('level_up', 'gatherer_codes', default=['~/.level-up-code'],
                                doc='The gatherer codes (or paths from which they should be read) corresponding to authors.')
    metric_name = Option('level_up', 'metric_name')
    unit = Option('level_up', 'unit', default='bugs fixed')
    ratio = Option('level_up', 'ratio', default='50:1')
    value = Option('level_up', 'value', default='1')

    def resolve_gatherer_code(self, code):
        path = os.path.expanduser(code)
        if not os.path.exists(path): return path

        f = open(path)
        code = f.read().strip()
        f.close()
        return code

    def ticket_changed(self, ticket, comment, author, old_values):
        if (ticket['status'] == 'closed' and old_values.get('status',None) != 'closed' and
            ticket['resolution'] == self.resolution and
            author in self.authors):
            self.log.debug('%s scores points' % author)
            self.post_metric(self.resolve_gatherer_code(self.gatherer_codes[self.authors.index(author)]))

    def ticket_created(self, ticket): return
    def ticket_deleted(self, ticket): return

    def post_metric(self, code):
        post = urllib.urlencode({'code':code,
                                 'metric':self.metric_name or ('%s trac' % (self.config['project'].get('name'))),
                                 'unit':self.unit,
                                 'ratio':self.ratio,
                                 'value':self.value })
        u = urllib2.urlopen(self.url, post)
        u.close()
