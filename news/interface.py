#coding=utf-8
#author:u'王健'
#Date: 12-7-10
#Time: 下午9:50
from news.models import RSS, Setting
import setting
from tools.page import Page
from google.appengine.api import urlfetch
import urllib
import logging
import datetime
from google.appengine.api import memcache
__author__ = u'王健'



class saveRSS(Page):
    def get(self):
        id=self.request.get('id')
        mod=self.request.get('mod')
        rss=''
        if id:
            rss=RSS.get_by_id(int(id))
            if mod=='del':
                rss.delete()
                self.redirect('/rssList')
                return
        self.render('templates/rssAdd.html',{'rss':rss or {}})
    def post(self):
        id=self.request.get('id')
        rss=''
        if id:
            rss=RSS.get_by_id(int(id))
        if not rss:
            rss=RSS()
        rss.groupname=self.request.get('groupname','')
        rss.type=self.request.get('type','1')
        rss.tag=self.request.get('tag','rss')
        rss.head=self.request.get('GroupHead','0')
        rss.rssUrl=self.request.get('rssUrl','')
        rss.issync=False
        isfilterImg=self.request.get('isfilterImg')
        if isfilterImg=='True':
            rss.isfilterImg=True
        else:
            rss.isfilterImg=False
        rss.put()
        memcache.delete('rsslist')
        self.redirect('/rssList')

class listRSS(Page):
    def get(self):
        self.render('templates/rsslist.html',{'rsslist':RSS.all().order('-updateTime')})


class initRSS(Page):
    def get(self):
        for c in RSS.all():
            c.issync=False
            c.put()
class syncRSS(Page):
    def get(self):
        website=Setting().all().fetch(1)
        if len(website)==0:
            web=Setting()
            web.webSite='http://im.zxxsbook.com'
            web.put()
        else:
            web=website[0]
#        devdate=datetime.datetime.strptime('2012-12-17','%Y-%m-%d')
#        for c in RSS.all().filter('updateTime <',devdate):
#            c.issync=False
#            c.put()
        for c in RSS.all().filter('issync =',False):
            pam={}
            if c.code:
                pam['GroupId']=c.code
            pam['GroupName']=c.groupname.encode('utf-8')
            pam['UserName']=setting.adminname
            pam['GroupType']=c.type
            pam['GroupAppType']= setting.APPCODE_TYPE
            pam['GroupHead']=c.head
            pam['GroupTag']=c.tag.encode('utf-8')
            login_url = web.webSite+'/SyncGroup'
            login_data = urllib.urlencode(pam)
            result = urlfetch.fetch(
            url = login_url,
            payload = login_data,
            method = urlfetch.POST,
            headers = {'Content-Type':'application/x-www-form-urlencoded',
                       'User-Agent':'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.2) Gecko/20100115 Firefox/3.6'},
            follow_redirects = False,deadline=10)
            if result.status_code == 200 and result.content!='0':
                c.code=result.content
                c.issync=True
                c.put()
                memcache.delete('rsslist')
            else:
                logging.error('send news failure !')


