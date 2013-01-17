#coding=utf-8
#author:u'王健'
#Date: 12-7-10
#Time: 下午9:17
__author__ = u'王健'



from google.appengine.ext import db

__author__ = 'Administrator'
class RSS(db.Model):
    code=db.StringProperty(indexed=False)
    rssUrl=db.StringProperty()
    groupname=db.StringProperty(indexed=False)
    type=db.StringProperty(default='1')
    head=db.StringProperty(indexed=False,default='0')
    tag=db.StringProperty(indexed=False)
    issync=db.BooleanProperty(default=False)
    isfilterImg=db.BooleanProperty(default=False)
    updateTime=db.DateTimeProperty(auto_now=True)
    numCon=db.IntegerProperty(default=0,indexed=False)
class Setting(db.Model):
    webSite=db.StringProperty()
    imSite=db.StringProperty()

#rss新闻json
class ContentsObj(db.Model):
    rss=db.ReferenceProperty(RSS)
    contentdata=db.TextProperty(default='[]')

class Contents(db.Model):
    title=db.StringProperty(indexed=False)
    link=db.LinkProperty(indexed=False)
    desc=db.StringProperty(indexed=False)
    content=db.TextProperty()
    realContent=db.TextProperty()
    updateTime=db.DateTimeProperty(auto_now=True)
#    hasRealContent=db.BooleanProperty(default=False)
    rss=db.ReferenceProperty(RSS)
#    hasContent=db.BooleanProperty(default=False)
#    hasDown=db.BooleanProperty(default=False)
#    hasDelete=db.BooleanProperty(default=False)
    status=db.StringProperty()# 1: title 和 link 赋值 2：content 下载 3：content 过滤得到 realcontent 4：同步content

#    realContentResult=db.IntegerProperty()
#    realContentBz=db.StringProperty(multiline=True,indexed=False)
#    next=db.LinkProperty()
#    hasFather=db.BooleanProperty(default=False)

class Picture(db.Model):
    content=db.ReferenceProperty(Contents)
    src=db.StringProperty()
    df=db.BlobProperty()
    isDown=db.BooleanProperty(default=False)
    datetime=db.DateTimeProperty(auto_now_add=True)