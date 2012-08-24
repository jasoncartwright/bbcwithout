import webapp2, re, os

from google.appengine.api import urlfetch
from google.appengine.ext.webapp import template

import BeautifulSoup
from BeautifulSoup import Comment

BBC_URL = "http://www.bbc.co.uk"

class MainHandler(webapp2.RequestHandler):

    def get(self):

        words = self.request.GET.get("words",None)

        if words:

            blacklist_words = words.split(",")

            # Handle root
            if self.request.path == "/":
                url = BBC_URL + "/news/"
            else:
                url = BBC_URL + self.request.path

            result = urlfetch.fetch(url)

            if result.status_code == 200:

                # Doctype confuses BeautifulSoup
                html = result.content.replace(
                    '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML+RDFa 1.0//EN" "http://www.w3.org/MarkUp/DTD/xhtml-rdfa-1.dtd">',
                    ''
                )

                soup = BeautifulSoup.BeautifulSoup(html)

                # Get rid of the EU cookie nonsense
                cookie_nonsense = soup.find("script", {"id":"blq-bbccookies-tmpl"})
                if cookie_nonsense:
                    cookie_nonsense.extract()

                # Get the comments out of the way
                comments = soup.findAll(text=lambda text:isinstance(text, Comment))
                for comment in comments:
                    comment.extract()

                # Rewrite links, and pass words
                for node in soup.findAll('a', href=True):
                    url = node['href']
                    url = url.replace(BBC_URL, "")
                    node['href'] = url + "?words=" + words
 
                # Remove containers containing blacklisted words
                for blacklist_word in blacklist_words:
                    if blacklist_word:
                        mentions = soup.findAll(text=re.compile(blacklist_word, re.IGNORECASE))

                        for mention in mentions:
                            mention.parent.parent.extract()

                self.response.out.write(soup)

        else:
            # Form to add words if none are specified
            path = os.path.join(os.path.dirname(__file__), 'form.html')
            self.response.out.write(template.render(path, {}))



app = webapp2.WSGIApplication([('/.*', MainHandler)], debug=True)