#coding=utf-8
#
import uuid

__author__ = u'王健'
#import os,webapp2
import os,webapp2,jinja2
#from django.template import loader
from setting import TEMPLATE_DIR
#from google.appengine.ext.webapp import template


class Page(webapp2.RequestHandler):
    def obj2str(self, template_file, template_value):
        jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(TEMPLATE_DIR))
        template = jinja_environment.get_template(template_file)
        return template.render(template_value)
    def flashhtml(self,html):
        self.response.out.write(html)
    def render(self, template_file, template_value):
        self.flashhtml(self.obj2str(template_file,template_value))
#        path = os.path.join(TEMPLATE_DIR, template_file)
#        self.response.out.write(template.render(path,template_value))
#
def getUUID():
    return str(uuid.uuid4()).replace('-','')


