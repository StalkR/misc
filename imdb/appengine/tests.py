import os
import StringIO
import unittest
import webapp2

from google.appengine.api import app_identity
from google.appengine.api import mail

import imdb_test

MAIL = 'admin@example.com'


def Mail(details):
    appid = app_identity.get_application_id()
    sender = '%s tests <tests@%s.appspotmail.com>' % (appid, appid)
    subject = '%s: Tests failing' % appid
    mail.send_mail(sender=sender, to=MAIL, subject=subject, body=details)


def Run(modules):
    outputs = []
    success = True
    for module in modules:
        stream = StringIO.StringIO()
        stream.write('Testing: %s\n' % module.__name__)
        runner = unittest.TextTestRunner(stream=stream)
        suite = unittest.TestLoader().loadTestsFromModule(module)
        result = runner.run(suite)
        if not result.wasSuccessful():
            success = False
        stream.seek(0)
        outputs.append(stream.read())
    output = '\n'.join(outputs)
    if not success:
        Mail(output)
    return output


class Handler(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.write(Run([imdb_test]))


app = webapp2.WSGIApplication([
    (r'/tests', Handler),
], debug=os.environ.get('SERVER_SOFTWARE', '').startswith('Dev'))
