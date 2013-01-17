#coding=utf-8
from datetime import datetime, timedelta
import logging
import re
import traceback
import urllib
from google.appengine.api.images import Image
from google.appengine.ext import db
from google.appengine.api import urlfetch
from google.appengine.api import memcache
from google.appengine.api import images
from models import Setting, RSS ,Contents,Picture
from news.models import ContentsObj
from news.skin import skinSubThree, skinSubFour
import setting
from skin import skinSubOne, skinSubTwo
from tools.page import Page
import json

import feedparser

__author__ = 'Administrator'



class default(Page):
    def get(self):
        self.render('templates/index.html', {'RSSs':RSS.all()})
class getWebsiteRSS(Page):
    def get(self):
        website=Setting().all().fetch(1)
        if 0 == len(website):
            w=Setting()
            w.webSite='http://im.zxxsbook.com'
            w.put()
            website.append(w)
        web=website[0]
        self.searchRSS(web.webSite+'/RssSource')
    def searchRSS(self,url):
        rpcs=[]
        rpc=urlfetch.create_rpc(deadline=50)
        rpc.callback=self.rpc_callback(rpc,url)
        urlfetch.make_fetch_call(rpc, url,  headers={'User-Agent':'Mozilla/5.0'},follow_redirects=True)
        rpcs.append(rpc)
        for rpc in rpcs:
            rpc.wait()

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
                                logging.error(rss.code+'||'+rss.rssUrl)
                                r=RSS().all().filter('code =',rss.code).fetch(1)
                                if r:
                                    logging.error(rss.code+'||'+rss.rssUrl)
                                    clist=Contents().all().filter('rss =',r[0])
                                    for c in clist:
                                        c.status='1'
                                        c.put()
                                    db.delete(r)
                                rsslist.append(rss)
                db.put(rsslist)
                deleteRss=[]
                for dbrss in RSS().all():
                    if dbrss.code not in realrss:
                        deleteRss.append(dbrss)
                db.delete(deleteRss)
        except Exception,e:
            logging.error('0000'+str(e)+url)
class RSSMsg(Page):
    def get(self):
        web=None
        syncerrornote=memcache.get('syncerrnote')
        if syncerrornote:
            try:
                website=Setting().all().fetch(1)
                if len(website)==0:
                    web=Setting()
                    web.webSite='http://im.zxxsbook.com'
                    web.put()
                else:
                    web=website[0]
                    web.put()
            except :
                return
        content=Contents().all().filter('status =','3').order('updateTime').fetch(3)
        if not web:
            website=Setting().all().fetch(1)
            if len(website)==0:
                web=Setting()
                web.webSite='http://im.zxxsbook.com'
                web.put()
            else:
                web=website[0]
        for c in content:
            piclist=memcache.get('piclist'+str(c.key().id()))
            if not piclist:
                piclist=Picture().all().filter('content =',c).fetch(20)
            else:
                piclist=piclist['list']
            pam={}
            for i in range(len(piclist)):
                img=piclist[i]
#                n=img.src.split('/')
#                pam['imgName'+str(i)]=n[-1]
                pam['img'+str(i)]=img.src
            pam['code']=c.rss.code
            pam['title']=c.title.encode('utf-8')
            pam['content']=c.realContent.encode('utf-8')
            pam['username']=setting.adminname
#            if c.rcode:
#                pam['rcode']=c.rcode.encode('utf-8')
            login_url = web.webSite+'/RssMsg'
            login_data = urllib.urlencode(pam)
            result = urlfetch.fetch(
            url = login_url,
            payload = login_data,
            method = urlfetch.POST,
            headers = {'Content-Type':'application/x-www-form-urlencoded',
                       'User-Agent':'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.2) Gecko/20100115 Firefox/3.6'},
            follow_redirects = False,deadline=50)
            if result.status_code == 200:
                c.code=result.content
                c.status='4'
                try:
                    c.put()
                    memcache.set('syncerrnote',False,3600)
                except :
                    memcache.set('syncerrnote',True,3600)
            else:
                logging.error('send news failure !'+c.link)
            logging.info('syncurl:'+login_url)
#        if True:
#            delcontent=Contents().all().filter('status =','1').filter('hasDelete =',False).fetch(10)
#            if not delcontent:
#                return
#            db.delete(delcontent)
#            pam={}
#            i=0
#            deleteC=[]
#            for d in delcontent:
#                if d.code:
#                    pam['deletecode'+str(i)]=d.code.encode('utf-8')
#                    i+=1
#                    deleteC.append(d)
#            if not pam:
#                return
#            login_url = web.webSite+'/RssMsg'
#            login_data = urllib.urlencode(pam)
#            result = urlfetch.fetch(
#            url = login_url,
#            payload = login_data,
#            method = urlfetch.POST,
#            headers = {'Content-Type':'application/x-www-form-urlencoded',
#                           'User-Agent':'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.2) Gecko/20100115 Firefox/3.6'},
#            follow_redirects = False,deadline=10)
#            if result.status_code == 200:
#                db.delete(deleteC)
#                logging.info('delete news success !')
#            else:
#                logging.info('delete news failure !')

class addRSS(Page):
    def post(self):
        rssUrl=self.request.get('rssUrl').strip()
        if RSS.all().filter('rssUrl =',rssUrl).count()==0 and rssUrl:
            rss=RSS()
            rss.rssUrl=rssUrl
            rss.put()
        self.render('templates/index.html', {'RSSs':RSS.all()})

class Look(Page):
    def get(self):
        cid=self.request.get('content')
        if cid:
            content=Contents.get_by_id(int(cid))
            self.render('templates/look.html', {'content':content,'view':True})
            return
        rssid=self.request.get('rss')
        if rssid:
            c=Contents.all().filter('realContentResult =',0).filter('rss =',RSS.get_by_id(int(rssid))).fetch(1)
        if not rssid or not c:
            c=Contents.all().filter('realContentResult =',0).fetch(1)
        if c:
            content=c[0]
            self.render('templates/look.html', {'content':content})
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
class DetailLook(Page):
    def get(self):
        rssid=self.request.get('rss')
        c=Contents.all().filter('rss =',RSS.get_by_id(int(rssid))).filter('realContentResult >',0).filter('realContentResult !=',None)
        self.render('templates/detailLook.html', {'content':c})

class getAnalysis(Page):
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
        self.render('templates/analysis.html', {'RSSs':rsslist})

class getRss(Page):
        
    def get(self):
        self.saveRssList=[]
        self.saveRssMap={}
        self.urls=[]
        rsslist=memcache.get('rsslist')
        if not rsslist:
            rsslist=[]
            for r in RSS.all().order('updateTime'):
                rsslist.append(r)
            memcache.set('rsslist',rsslist,36000)
#        import random
#        s=random.randint(0,len(rsslist)-1)
#        if  s%2==1:
#            rsslist.reverse()
#        s=random.randint(0,len(rsslist)-1)
        ls=rsslist[:50]
        rsslist=rsslist[50:]+ls
        memcache.set('rsslist',rsslist,36000)
        for rss in ls:
            if rss.code:
                self.urls.append((rss,rss.rssUrl))

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
            rpc=urlfetch.create_rpc(deadline=60)
            rpc.callback=self.rpc_callback(rpc,rss,url)
            urlfetch.make_fetch_call(rpc, url,  headers={'User-Agent':'Mozilla/5.0'},follow_redirects=True)
            rpcs.append(rpc)
        for rpc in rpcs:
            try:
                rpc.wait()
            except Exception,e:
                logging.error('rpc:'+str(e))
#        if self.saveRssList:
#            db.put(self.saveRssList)
#        Search.saveBook(self.bookMaps)
    def rpc_callback(self,rpc,rss,url):
        return lambda:self.handle_result(rpc,rss,url)

    def rpc2_callback(self,rpc,rss,linklist,oldlist,pam):
        return lambda:self.handle2_result(rpc,rss,linklist,oldlist,pam)
    def handle_result(self,rpc,rssSources,url):
        try:
            result=rpc.get_result()
            if result.status_code ==200:
                html=result.content
                rsslist=feedparser.parse(html)
                alist=[]
                for rss in rsslist.entries:
                    try:
                        alist.append((rss.title,rss.link,rss.description))
                    except Exception,e:
                        logging.error('rss jiexi'+str(e))
                newContent=[]
                contentobj=memcache.get(rssSources.rssUrl)
                if not contentobj:
                    contentobj=ContentsObj.all().filter('rss =',rssSources).fetch(1)
                    if not contentobj:
                        contentobj=ContentsObj()
                        contentobj.rss=rssSources
                    else:
                        contentobj=contentobj[0]
                nowNewsList=json.loads(contentobj.contentdata)
                for title,link,desc in alist:
                    link=link.strip()
                    if link not in nowNewsList:
                        newContent.append((link,title,desc,[]))
                rpcs=[]
                notediclist=[]
                for linkyuanzu in newContent:
                    pam={}
                    rpc=urlfetch.create_rpc(deadline=50)
                    rpc.callback=self.rpc2_callback(rpc,rssSources,linkyuanzu,nowNewsList[-10:],pam)
                    urlfetch.make_fetch_call(rpc, linkyuanzu[0],  headers={'User-Agent':'Mozilla/5.0'},follow_redirects=True)
                    rpcs.append(rpc)
                    notediclist.append(pam)
                for rpc in rpcs:
                    try:
                        rpc.wait()
                    except :
                        pass
                website=Setting().all().fetch(1)
                if len(website)==0:
                   web=Setting()
                   web.webSite='http://im.zxxsbook.com'
                   web.put()
                else:
                   web=website[0]
                allpam={}
                tempNewList=[]
                allpam['notenum']=str(len(notediclist))
                for i,pam in  enumerate(notediclist):
                    tempNewList.append(newContent[i][0])
                    if pam:

                        if not rssSources.isfilterImg:
                            for num in range(pam['imgnum']):
                                allpam[str(i)+'img'+str(num)]=pam['img'+str(num)]
                        allpam[str(i)+'code']=pam['code']
                        allpam[str(i)+'title']=pam['title']
                        allpam[str(i)+'content']=pam['content']
                        allpam[str(i)+'username']=pam['username']
                if not notediclist:
                    return
                login_url = web.webSite+'/RssMsg'
                login_data = urllib.urlencode(allpam)
#                logging.info('pam:'+str(allpam))
                result = urlfetch.fetch(
                    url = login_url,
                    payload = login_data,
                    method = urlfetch.POST,
                    headers = {'Content-Type':'application/x-www-form-urlencoded',
                               'User-Agent':'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.2) Gecko/20100115 Firefox/3.6'},
                    follow_redirects = False,deadline=50)
                if result.status_code == 200:
                    nowNewsList.extend(tempNewList)
                    contentobj.contentdata=json.dumps(nowNewsList[-60:])
                    contentobj.put()
                    memcache.set(rssSources.rssUrl,contentobj,3600)
                else:
    #                    linkyuanzu[3].append(False)
                    logging.error('send news failure !'+linkyuanzu[0])
#                for linkyuanzu in newContent:
#                    if linkyuanzu[3]:
#                        nowNewsList.append(linkyuanzu[0])

        except Exception,e:
            logging.error('0000'+str(e)+url)
#            logging.error(traceback.print_exc())

    def handle2_result(self,rpc,rss,linkyuanzu,oldlist,pam):
        try:
            result=rpc.get_result()
            if result.status_code ==200:

                html=result.content

                if html:
                    oldHtmlList=[]
                    for k in oldlist:
                        t=memcache.get(k)
                        if t:
                            oldHtmlList.append(t)
#                    logging.info('html:'+html)
                    news,piclist=skinSubThree(oldHtmlList,html,linkyuanzu[1],linkyuanzu[0])
#                    news,piclist=skinSubFour(oldHtmlList,html,linkyuanzu[1],linkyuanzu[0])
#                    logging.info('news:'+news)

                    imgmap={}
                    for url in piclist:
                        imgmap[url]=False
                    self.searchPic(imgmap,piclist)
                    imglist=[]
                    for url in piclist:
                        if imgmap[url]:
                            imglist.append(url)

#                    pam={}
#                    piclist=piclist[0:2]
                    pam['imgnum']=len(imglist)
                    for i in range(len(imglist)):
                        img=imglist[i]
                        pam['img'+str(i)]=img
                    pam['code']=rss.code
                    pam['title']=linkyuanzu[1].encode('utf-8')
                    pam['content']=news.encode('utf-8')
                    pam['username']=setting.adminname
                    #            if c.rcode:
                    #                pam['rcode']=c.rcode.encode('utf-8')

        #                    logging.info('syncurl:'+login_url)
            else:
                logging.error('500'+linkyuanzu[0]+'rss:'+str(rss.rssUrl))
        except Exception,e:
            logging.error('get html error '+linkyuanzu[0]+'---'+str(e))

    def searchPic(self,imgmap,imglist):
        rpcs=[]
        for url in imglist:
            try:
                rpc=urlfetch.create_rpc(deadline=20)
                rpc.callback=self.rpc_callbackImg(rpc,imgmap,url)
                urlfetch.make_fetch_call(rpc, url,  headers={'User-Agent':'Mozilla/5.0'},follow_redirects=True)
                rpcs.append(rpc)
            except :
                pass
        for rpc in rpcs:
            try:
                rpc.wait()
            except :
                pass
#        Search.saveBook(self.bookMaps)
    def rpc_callbackImg(self,rpc,imgmap,url):
        return lambda:self.handle_resultImg(rpc,imgmap,url)
    def handle_resultImg(self,rpc,imgmap,url):
        try:
            result=rpc.get_result()
            if result.status_code ==200:
                i=Image(result.content)
                if i.width>300 :
                    imgmap[url]=True
        except Exception,e:
            logging.error('img-'+str(e)+url)
#    def handle_result(self,rpc,rssSources,url):
#        try:
#            result=rpc.get_result()
#            if result.status_code ==200:
#                html=result.content
#
##                html=result.content.replace('\r\n','').replace('\n','')
##                try:
##                    html=html.decode('utf-8')
##                except :
##                    logging.error('gbk failure')
##                    html=html.decode('gbk')
##                    logging.error('gbk success')
#                rsslist=feedparser.parse(html)
#
#                alist=[]
#                for rss in rsslist.entries:
#                    alist.append((rss.title,rss.link,rss.description))
##                rssSaveList=[]
##                nowContent={}
##                nowContentLink=[]
##                saveContent=[]
#                newContent=[]
#                contentobj=ContentsObj().all().filter('rss =',rssSources).fetch(1)
#                if not contentobj:
#                    contentobj=ContentsObj()
#                    contentobj.rss=rssSources
#                else:
#                    contentobj=contentobj[0]
#                nowNewsList=json.loads(contentobj.contentdata)
##                if not nowNewsList:
##                    nowNewsList=[]
##                    for c in ContentsObj().all().filter('rss =',rssSources):
##                        nowNewsList=json.dumps(c.contentdata)
##                    memcache.set('RSSLink'+str(rssSources.key().id()),nowNewsList,36000)
##                for id,link in nowNewsList:
##                    nowContent[link]=id
##                    nowContentLink.append(link)
##                rss=memcache.get('getrss'+str(rssSources.key().id()))
##                if not rss:
##                    rss=RSS.get_by_id(rssSources.key().id())
##                    memcache.set('getrss'+str(rssSources.key().id()),rss,360000)
#                for title,link,desc in alist:
#                    link=link.strip()
#                    if link not in nowNewsList:
#                        newContent.append((link,title,desc,[]))
#                rpcs=[]
#                for linkyuanzu in newContent:
#                    rpc=urlfetch.create_rpc(deadline=30)
#                    rpc.callback=self.rpc2_callback(rpc,rssSources,linkyuanzu,nowNewsList[-10:])
#                    urlfetch.make_fetch_call(rpc, linkyuanzu[0],  headers={'User-Agent':'Mozilla/5.0'},follow_redirects=True)
#                    rpcs.append(rpc)
#                for rpc in rpcs:
#                    rpc.wait()
#                for linkyuanzu in newContent:
#                    if linkyuanzu[3]:
#                        nowNewsList.append(linkyuanzu[0])
#                contentobj.contentdata=json.dumps(nowNewsList[-60:])
#                contentobj.put()
#
#
##                self.saveRssList.append(rssSources) #每次都全部同步
#        except Exception,e:
#            logging.error('0000'+str(e)+url)
##            logging.error(traceback.print_exc())
#
#    def handle2_result(self,rpc,rss,linkyuanzu,oldlist):
#        try:
#            result=rpc.get_result()
#            if result.status_code ==200:
#                try:
#                    html=result.content.decode('utf-8').strip()
#                except :
#                    try:
#                        html=result.content.decode('gbk').strip()
#                    except :
#                        try:
#                            html=result.content.decode('gb18030').strip()
#                        except:
#                            html=None
#
#                if html:
#                    oldHtmlList=[]
#                    for k in oldlist:
#                        t=memcache.get(k)
#                        if t:
#                            oldHtmlList.append(t)
##                    logging.info('html:'+html)
#                    news,piclist=skinSubThree(oldHtmlList,html,linkyuanzu[1],linkyuanzu[0])
##                    logging.info('news:'+news)
#                    memcache.set(linkyuanzu[0],html,360000)
#
#                    website=Setting().all().fetch(1)
#                    if len(website)==0:
#                        web=Setting()
#                        web.webSite='http://im.zxxsbook.com'
#                        web.put()
#                    else:
#                        web=website[0]
#                    pam={}
#                    for i in range(len(piclist)):
#                        img=piclist[i]
#                        pam['img'+str(i)]=img
#                    pam['code']=rss.code
#                    pam['title']=linkyuanzu[1].encode('utf-8')
#                    pam['content']=news.encode('utf-8')
#                    pam['username']=setting.adminname
#                    #            if c.rcode:
#                    #                pam['rcode']=c.rcode.encode('utf-8')
#                    login_url = web.webSite+'/RssMsg'
#                    login_data = urllib.urlencode(pam)
#                    result = urlfetch.fetch(
#                        url = login_url,
#                        payload = login_data,
#                        method = urlfetch.POST,
#                        headers = {'Content-Type':'application/x-www-form-urlencoded',
#                                   'User-Agent':'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.2) Gecko/20100115 Firefox/3.6'},
#                        follow_redirects = False,deadline=20)
#                    if result.status_code == 200:
#                        linkyuanzu[3].append(True)
#                    else:
#        #                    linkyuanzu[3].append(False)
#                        logging.error('send news failure !'+linkyuanzu[0])
#        #                    logging.info('syncurl:'+login_url)
#            else:
#                logging.error('500'+linkyuanzu[0])
#        except :
#            logging.error('get html error '+linkyuanzu[0])


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
class getContent(Page):
    def get(self,limit):
        self.urls=[]
        for content in Contents.all().filter('status =','1').fetch(int(limit)):
            self.urls.append((content,content.link))
        self.searchRSS()
    def searchRSS(self):
        rpcs=[]
        for content,url in self.urls:
            rpc=urlfetch.create_rpc(deadline=50)
            rpc.callback=self.rpc_callback(rpc,content,url)
            urlfetch.make_fetch_call(rpc, url,  headers={'User-Agent':'Mozilla/5.0'},follow_redirects=True)
            rpcs.append(rpc)
        for rpc in rpcs:
            rpc.wait()
#        Search.saveBook(self.bookMaps)
    def rpc_callback(self,rpc,content,url):
        return lambda:self.handle_result(rpc,content,url)
    def handle_result(self,rpc,content,url):
        try:
            result=rpc.get_result()
            if result.status_code ==200:
                html=result.content
                try:
                    content.content=result.content.decode('utf-8').strip()
                except :
                    try:
                        content.content=result.content.decode('gbk').strip()
                    except :
                        try:
                            content.content=result.content.decode('gb18030').strip()
                        except:
                            content.content='<p>新闻获取出错!</p>'.decode('utf-8')
                
                content.status='2'
                content.put()
        except Exception,e:
            logging.error('1111'+str(e)+url)

class getNewsSubOne(Page):
    def get(self):
        newsHtmlList=Contents.all().filter('status =','2').fetch(1)
        if newsHtmlList:
            try:
                r=newsHtmlList[0].rss
            except :
                newsHtmlList[0].status='1'
                #db.delete(newsHtmlList)
                logging.error('delete one news ,has no rss')
                return
#            '''
#            接下来就是要处理原始材料了。这是第一个版本的剥皮程序。
#            1.找寻所有的<p></p> 之间的内容。
#                （根据我的观察，能发布新闻RSS的网站都是大型网站，有优化html代码的习惯。使得新闻html很简化。因此我觉得这个方法有一定的可行性。）
#          '''
            newsHtmlList=Contents.all().filter('rss =',newsHtmlList[0].rss).filter('status =','2').fetch(20)
            oldHtmlList=memcache.get('oldhtmllist'+str(newsHtmlList[0].rss.key().id()))
            if not oldHtmlList:
                oldHtmlList=Contents.all().filter('rss =',newsHtmlList[0].rss).filter('status >','2').fetch(10)
                try:
                    memcache.set('oldhtmllist'+str(newsHtmlList[0].rss.key().id()),oldHtmlList,3600*24*3)
                except Exception,e:
                    pass
#            content=newsHtmlList[0]
#            news=skinSubOne(content.content)
            skinSubTwo(oldHtmlList,newsHtmlList)
            
#            content.realContent=news
#            content.realContentResult=0
#            content.put()
class detailSkin1(Page):
    def get(self):
        self.render('templates/detailSkin1.html', {})
    def post(self):
        content=self.request.get('content')
        news=''
        content2=''
        if content:
#            news=skinSubOne(content)
            news,content2=skinSubOne(content)
#            news,content2=skinSubTwo(content)
        self.render('templates/detailSkin1.html', {'content':content,'content2':content2,'news':news})

class deleteContents(Page):
    def get(self):
#        nocode=Contents.all().filter('status =','1').filter('code =',None).fetch(10)
#        db.delete(nocode)
        nocontent=Contents.all().filter('status =','1').filter('hasContent =',False).fetch(10)
        db.delete(nocontent)
        deletecontent=Contents.all().filter('status =','1').filter('hasDelete =',True).fetch(10,30)
        db.delete(deletecontent)
#        oldpic=Picture.all().filter('datetime <',datetime.now()+timedelta(hours=-72)).fetch(300)
#        db.delete(oldpic)
#        norss=Contents().all().filter('status =','2').fetch(100)
        rss=0
#        for c in norss:
#            try:
#                r=c.rss.code
#            except :
#                logging.info('delete 1')
#                c.status='1'
#                c.put()
#                rss+=1
        logging.info('nocontent:'+str(len(nocontent))+'-'+'deletecontent:'+str(len(deletecontent)))

class showPiclist(Page):
    def get(self):
        self.render('templates/picture.html', {'piclist':Picture.all()})

class showImg(Page):
    def get(self):
        imgid=self.request.get("img_id")
        if imgid:
            imgid=int(imgid)
        else:
            self.error(500)
            return
        greeting = Picture.get_by_id(imgid)
        if not greeting:
            self.error(404)
        elif greeting.df:
            self.response.headers['Content-Type'] = "application/x-www-form-urlencoded"
            self.response.out.write(greeting.df)
        else:
            self.error(505)

class downloadpic(Page):
        
    def get(self):
        self.urls=[]
        imglist=Picture().all().filter('isDown =',False).fetch(10)
        for img in imglist:
            self.urls.append((img,img.src))
        self.searchPic()

    def searchPic(self):
        rpcs=[]
        for img,url in self.urls:
            try:
                rpc=urlfetch.create_rpc(deadline=10)
                rpc.callback=self.rpc_callback(rpc,img,url)
                urlfetch.make_fetch_call(rpc, url,  headers={'User-Agent':'Mozilla/5.0'},follow_redirects=True)
                rpcs.append(rpc)
            except :
                img.delete()
        for rpc in rpcs:
            rpc.wait()
#        Search.saveBook(self.bookMaps)
    def rpc_callback(self,rpc,img,url):
        return lambda:self.handle_result(rpc,img,url)
    def handle_result(self,rpc,img,url):
        try:
            result=rpc.get_result()
            if result.status_code ==200:
                i=Image(result.content)
                if i.width<300 :
                    db.delete(img)
                else:
                    img.df=db.Blob(images.resize(result.content,200,200))
                    img.isDown=True
                    img.put()
            elif result.status_code ==404:
                db.delete(img)
        except Exception,e:
            logging.error('img-'+str(e)+url)


class getTestRss(Page):

    def get(self):
        self.saveRssList=[]
        self.saveRssMap={}
        self.urls=[]
        rsslist=memcache.get('rsslist')
        if not rsslist:
            rsslist=[]
            for r in RSS.all().order('updateTime'):
                rsslist.append(r)
            memcache.set('rsslist',rsslist,36000)
        for rss in rsslist:
            if not rss.code:
                self.urls.append((rss,rss.rssUrl))

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
            rpc=urlfetch.create_rpc(deadline=50)
            rpc.callback=self.rpc_callback(rpc,rss,url)
            urlfetch.make_fetch_call(rpc, url,  headers={'User-Agent':'Mozilla/5.0'},follow_redirects=True)
            rpcs.append(rpc)
        for rpc in rpcs:
            try:
                rpc.wait()
            except Exception,e:
                logging.error('rpc:'+str(e))
#        if self.saveRssList:
#            db.put(self.saveRssList)
#        Search.saveBook(self.bookMaps)
    def rpc_callback(self,rpc,rss,url):
        return lambda:self.handle_result(rpc,rss,url)

    def rpc2_callback(self,rpc,rss,linklist,oldlist,pam):
        return lambda:self.handle2_result(rpc,rss,linklist,oldlist,pam)
    def handle_result(self,rpc,rssSources,url):
        try:
            result=rpc.get_result()
            if result.status_code ==200:
                html=result.content
                rsslist=feedparser.parse(html)
                alist=[]
                for rss in rsslist.entries:
                    try:
                        alist.append((rss.title,rss.link,rss.description))
                    except Exception,e:
                        logging.error('rss jiexi'+str(e))
                newContent=[]
                contentobj=ContentsObj().all().filter('rss =',rssSources).fetch(1)
                if not contentobj:
                    contentobj=ContentsObj()
                    contentobj.rss=rssSources
                else:
                    contentobj=contentobj[0]
                nowNewsList=json.loads(contentobj.contentdata)
                for title,link,desc in alist:
                    link=link.strip()
                    if link not in nowNewsList:
                        newContent.append((link,title,desc,[]))
                rpcs=[]
                notediclist=[]
                for linkyuanzu in newContent:
                    pam={}
                    rpc=urlfetch.create_rpc(deadline=50)
                    rpc.callback=self.rpc2_callback(rpc,rssSources,linkyuanzu,nowNewsList[-10:],pam)
                    urlfetch.make_fetch_call(rpc, linkyuanzu[0],  headers={'User-Agent':'Mozilla/5.0'},follow_redirects=True)
                    rpcs.append(rpc)
                    notediclist.append(pam)
                for rpc in rpcs:
                    rpc.wait()
                website=Setting().all().fetch(1)
                if len(website)==0:
                   web=Setting()
                   web.webSite='http://localhoat:8888'
                   web.put()
                else:
                   web=website[0]
                allpam={}
                tempNewList=[]
                allpam['notenum']=str(len(notediclist))
                for i,pam in  enumerate(notediclist):
                    if pam:
                        tempNewList.append(newContent[i][0])
                        if not rssSources.isfilterImg:
                            for num in range(pam['imgnum']):
                                allpam[str(i)+'img'+str(num)]=pam['img'+str(num)]
                        allpam[str(i)+'code']=pam['code']
                        allpam[str(i)+'title']=pam['title']
                        allpam[str(i)+'content']=pam['content']
                        allpam[str(i)+'username']=pam['username']
                if not notediclist:
                    return
                login_url = web.webSite+'/RssMsg'
                login_data = urllib.urlencode(allpam)
#                logging.info('pam:'+str(allpam))
                result = urlfetch.fetch(
                    url = login_url,
                    payload = login_data,
                    method = urlfetch.POST,
                    headers = {'Content-Type':'application/x-www-form-urlencoded',
                               'User-Agent':'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.2) Gecko/20100115 Firefox/3.6'},
                    follow_redirects = False,deadline=50)
                if result.status_code == 200:
                    nowNewsList.extend(tempNewList)
                    contentobj.contentdata=json.dumps(nowNewsList[-60:])
                    contentobj.put()
                else:
    #                    linkyuanzu[3].append(False)
                    logging.error('send news failure !'+linkyuanzu[0])
#                for linkyuanzu in newContent:
#                    if linkyuanzu[3]:
#                        nowNewsList.append(linkyuanzu[0])

        except Exception,e:
            logging.error('0000'+str(e)+url)
#            logging.error(traceback.print_exc())

    def handle2_result(self,rpc,rss,linkyuanzu,oldlist,pam):
        try:
            result=rpc.get_result()
            if result.status_code ==200:
                try:
                    html=result.content.decode('utf-8').strip()
                except :
                    try:
                        html=result.content.decode('gbk').strip()
                    except :
                        try:
                            html=result.content.decode('gb18030').strip()
                        except:
                            html=None

                if html:
                    oldHtmlList=[]
                    for k in oldlist:
                        t=memcache.get(k)
                        if t:
                            oldHtmlList.append(t)
#                    logging.info('html:'+html)
                    news,piclist=skinSubThree(oldHtmlList,html,linkyuanzu[1],linkyuanzu[0])
#                    logging.info('news:'+news)
                    memcache.set(linkyuanzu[0],html,360000)


#                    pam={}
                    pam['imgnum']=len(piclist)
                    for i in range(len(piclist)):
                        img=piclist[i]
                        pam['img'+str(i)]=img
                    pam['code']=rss.code
                    pam['title']=linkyuanzu[1].encode('utf-8')
                    pam['content']=news.encode('utf-8')
                    pam['username']=setting.adminname
                    #            if c.rcode:
                    #                pam['rcode']=c.rcode.encode('utf-8')

        #                    logging.info('syncurl:'+login_url)
            else:
                logging.error('500'+linkyuanzu[0]+'rss:'+str(rss.rssUrl))
        except Exception,e:
            logging.error('get html error '+linkyuanzu[0]+'---'+str(e))