#coding=utf-8
import logging
import re
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.api import urlfetch
from skin import skinSubOne, skinSubTwo

__author__ = 'Administrator'

class RSS(db.Model):
    code=db.StringProperty()
    rssUrl=db.StringProperty()
    updateTime=db.DateTimeProperty(auto_now=True)
class Setting(db.Model):
    webSite=db.StringProperty()

class Contents(db.Model):
    title=db.StringProperty()
    link=db.LinkProperty()
    desc=db.StringProperty()
    content=db.TextProperty()
    realContent=db.TextProperty()
    realContentResult=db.IntegerProperty()
    realContentBz=db.StringProperty(multiline=True)
    realContent2=db.TextProperty()
    realContent2Result=db.IntegerProperty()
    realContent2Bz=db.StringProperty(multiline=True)
    datetime=db.DateTimeProperty(auto_now_add=True)
    hasRealContent=db.BooleanProperty(default=False)
    rss=db.ReferenceProperty(RSS)
    hasContent=db.BooleanProperty(default=False)

class Img(db.Model):
    url=db.StringProperty()
    content=db.ReferenceProperty(Contents)
    df=db.BlobProperty()
    isDownload=db.BooleanProperty(default=False)
    datetime=db.DateTimeProperty(auto_now_add=True)

class default(webapp.RequestHandler):
    def get(self):
        self.response.out.write(template.render('templates/index.html', {'RSSs':RSS.all()}))
class getWebsiteRSS(webapp.RequestHandler):
    def __init__(self):
        pass
    def get(self):
        website=Setting().all().fetch(1)
        if 0 == len(website):
            w=Setting()
            w.webSite='http://learning2254.appspot.com'
            w.put()
            website.append(w)
        web=website[0]
        self.searchRSS(web.webSite+'/RssSource')
    def searchRSS(self,url):
        rpcs=[]
        rpc=urlfetch.create_rpc(deadline=10)
        rpc.callback=self.rpc_callback(rpc,url)
        urlfetch.make_fetch_call(rpc, url,  headers={'User-Agent':'Mozilla/5.0'},follow_redirects=True)
        rpcs.append(rpc)
        for rpc in rpcs:
            rpc.wait()

#        Search.saveBook(self.bookMaps)
    def rpc_callback(self,rpc,url):
        return lambda:self.handle_result(rpc,url)
    def handle_result(self,rpc,url):
        try:
            result=rpc.get_result()
            if result.status_code ==200:
                rsslist=[]
                realrss=set()
                for rssText in result.content.split('\r\n'):
                    if rssText:
                        rss=RSS()
                        r= rssText.split('$$')
                        if len(r)>=2:
                            rss.code=r[0]
                            realrss.add(rss.code)
                            rss.rssUrl=r[1]
                            if RSS().all().filter('code =',rss.code).filter('rssUrl =',rss.rssUrl).count()==0:
                                rsslist.append(rss)
                db.put(rsslist)
                deleteRss=[]
                for dbrss in RSS().all():
                    if dbrss.code not in realrss:
                        deleteRss.append(dbrss)
                db.delete(deleteRss)
        except Exception,e:
            logging.error('0000'+str(e)+url)
class addRSS(webapp.RequestHandler):
    def post(self):
        rssUrl=self.request.get('rssUrl').strip()
        if RSS.all().filter('rssUrl =',rssUrl).count()==0 and rssUrl:
            rss=RSS()
            rss.rssUrl=rssUrl
            rss.put()
        self.response.out.write(template.render('templates/index.html', {'RSSs':RSS.all()}))

class Look(webapp.RequestHandler):
    def get(self):
        cid=self.request.get('content')
        if cid:
            content=Contents.get_by_id(int(cid))
            self.response.out.write(template.render('templates/look.html', {'content':content,'view':True}))
            return
        rssid=self.request.get('rss')
        if rssid:
            c=Contents.all().filter('realContentResult =',0).filter('rss',RSS.get_by_id(int(rssid))).fetch(1)
        if not rssid or not c:
            c=Contents.all().filter('realContentResult =',0).fetch(1)
        if c:
            content=c[0]
            self.response.out.write(template.render('templates/look.html', {'content':content}))
        else:
            self.redirect('/')
    def post(self):
        link=self.request.get('link')
        c=Contents.all().filter('link =',link).fetch(1)
        if c:
            content=c[0]
            content.realContentResult=int(self.request.get('realContentResult'))
            content.realContentBz=self.request.get('realContentBz')
            content.put()
            self.redirect('/look?rss=%s' %self.request.get('rss'))
            return
        self.redirect('/')
class DetailLook(webapp.RequestHandler):
    def get(self):
        rssid=self.request.get('rss')
        c=Contents.all().filter('rss =',RSS.get_by_id(int(rssid))).filter('realContentResult >',0).filter('realContentResult !=',None)
        self.response.out.write(template.render('templates/detailLook.html', {'content':c}))

class getAnalysis(webapp.RequestHandler):
    def get(self):
        rsslist=[]
        for r in RSS.all():
            r.r0=Contents.all().filter('rss =',r).filter('realContentResult =',0).count()
            r.r1=Contents.all().filter('rss =',r).filter('realContentResult =',1).count()
            r.r2=Contents.all().filter('rss =',r).filter('realContentResult =',2).count()
            r.r3=Contents.all().filter('rss =',r).filter('realContentResult =',3).count()
            r.r4=Contents.all().filter('rss =',r).filter('realContentResult =',4).count()
            r.r5=Contents.all().filter('rss =',r).filter('realContentResult =',5).count()
            r.r6=Contents.all().filter('rss =',r).filter('realContentResult =',None).count()
            rsslist.append(r)
        self.response.out.write(template.render('templates/analysis.html', {'RSSs':rsslist}))

class getRss(webapp.RequestHandler):
    def __init__(self):
        self.saveRssList=[]
    def get(self):
        self.urls=[]
        for url in RSS.all().order('updateTime').fetch(10):
            self.urls.append((url,url.rssUrl))
        self.searchRSS()
#        r=RSS()
#        r.rssUrl='http://news.qq.com/newssh/rss_newssh.xml'
#        r.put()
#        r=RSS()
#        r.rssUrl='http://www.people.com.cn/rss/politics.xml'
#        r.put()
    def searchRSS(self):
        rpcs=[]
        for rss,url in self.urls:
            rpc=urlfetch.create_rpc(deadline=10)
            rpc.callback=self.rpc_callback(rpc,rss,url)
            urlfetch.make_fetch_call(rpc, url,  headers={'User-Agent':'Mozilla/5.0'},follow_redirects=True)
            rpcs.append(rpc)
        for rpc in rpcs:
            rpc.wait()
        if self.saveRssList:
            db.put(self.saveRssList)
#        Search.saveBook(self.bookMaps)
    def rpc_callback(self,rpc,rss,url):
        return lambda:self.handle_result(rpc,rss,url)
    def handle_result(self,rpc,rssSources,url):
        try:
            result=rpc.get_result()
            if result.status_code ==200:
                html=result.content.replace('\n','').replace('<![CDATA[','').replace(']]>','')
                start=html.find('<item>')
                if start!=-1:
                    html=html[start:]
                titleList=re.findall('<title>(.*?)</title>',html)
                linkList=re.findall('<link>(.*?)</link>',html)
                descList=re.findall('<description>(.*?)<',html)
                alist=[]
                if len(titleList)==len(linkList)==len(descList) :#
                    for i in range(len(titleList)):
                        alist.append((titleList[i],linkList[i],descList[i]))
                else:
                    alist=self.getItemList(html)
                rssSaveList=[]
                for title,link,desc in alist:
                    if title.find('微博')!=-1 and link.find('blog')!=-1:
                        continue
                    if not 0 != Contents.all().filter('link =', link.strip()).count():
                        c=Contents()
                        c.rss=rssSources
                        c.title=title.decode('utf-8').strip()
                        c.link=link.strip()
                        c.desc=desc.decode('utf-8').strip()
#                        c.content=''
#                        c.realContent=''
#                        c.realContent2=''
#                        c.realContent2Bz=''
#                        c.realContent2Result=0
#                        c.realContentBz=''
#                        c.realContentResult=0
                        rssSaveList.append(c)
                db.put(rssSaveList)
                self.saveRssList.append(rssSources)
        except Exception,e:
            logging.error('0000'+str(e)+url)
    def getItemList(self,html):
        rsslist=re.findall('<item>(.*?)</item>',html)
        alist=[]
        for rss in rsslist:
            title=re.findall('<title>(.*?)</title>',rss)
            link=re.findall('<link>(.*?)</link>',rss)
            description=re.findall('<description>(.*?)<',rss)
            if len(title)==len(link)==len(description)==1:
                alist.append((title[0],link[0],description[0]))
        return alist

####收集原始html文件
class getContent(webapp.RequestHandler):
    def get(self,limit):
        self.urls=[]
        for url in Contents.all().filter('content =',None).fetch(int(limit)):
            self.urls.append((url,url.link))
        self.searchRSS()
    def searchRSS(self):
        rpcs=[]
        for rss,url in self.urls:
            rpc=urlfetch.create_rpc(deadline=10)
            rpc.callback=self.rpc_callback(rpc,rss,url)
            urlfetch.make_fetch_call(rpc, url,  headers={'User-Agent':'Mozilla/5.0'},follow_redirects=True)
            rpcs.append(rpc)
        for rpc in rpcs:
            rpc.wait()
#        Search.saveBook(self.bookMaps)
    def rpc_callback(self,rpc,rss,url):
        return lambda:self.handle_result(rpc,rss,url)
    def handle_result(self,rpc,content,url):
        try:
            result=rpc.get_result()
            if result.status_code ==200:
                html=result.content
                headEnd=html.find('</head>')
                if headEnd==-1:
                    headEnd=html.find('</HEAD>')
                if headEnd==-1:
                    return
                if -1<html.find('charset=UTF-8')<headEnd or -1<html.find('charset=utf-8')<headEnd:
                    content.content=result.content.decode('utf-8').strip()
                else:
                    content.content=result.content.decode('gbk').strip()
                content.hasContent=True
                content.put()
        except Exception,e:
            logging.error('1111'+str(e)+url)

class getNewsSubOne(webapp.RequestHandler):
    def get(self):
        newsHtmlList=Contents.all().filter('hasContent =',True).filter('hasRealContent  =',False).fetch(1)
        if newsHtmlList:
#            '''
#            接下来就是要处理原始材料了。这是第一个版本的剥皮程序。
#            1.找寻所有的<p></p> 之间的内容。
#                （根据我的观察，能发布新闻RSS的网站都是大型网站，有优化html代码的习惯。使得新闻html很简化。因此我觉得这个方法有一定的可行性。）
#          '''
            newsHtmlList=Contents.all().filter('hasContent =',True).filter('hasRealContent =',False).filter('rss =',newsHtmlList[0].rss).fetch(20)
            oldHtmlList=Contents.all().filter('hasRealContent =',True).filter('rss =',newsHtmlList[0].rss).order('-datetime').fetch(10)
#            content=newsHtmlList[0]
#            news=skinSubOne(content.content)
            skinSubTwo(oldHtmlList,newsHtmlList)
            
#            content.realContent=news
#            content.realContentResult=0
#            content.put()
class detailSkin1(webapp.RequestHandler):
    def get(self):
        self.response.out.write(template.render('templates/detailSkin1.html', {}))
    def post(self):
        content=self.request.get('content')
        news=''
        content2=''
        if content:
#            news=skinSubOne(content)
            news,content2=skinSubOne(content)
#            news,content2=skinSubTwo(content)
        self.response.out.write(template.render('templates/detailSkin1.html', {'content':content,'content2':content2,'news':news}))

class deleteContents(webapp.RequestHandler):
    def get(self):
        db.delete(Contents.all().fetch(300))



