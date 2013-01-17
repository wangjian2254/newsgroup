#coding=utf-8
from google.appengine.api import memcache
from google.appengine.ext import db
import re



__author__ = 'WangJian'
from models import Picture, Contents

def skinSubOne(html=''):
    news=''
#    html, number = re.subn('<!--.*?-->','', html)#字符串替换
    html, number = re.subn('(?i)<style.*?</style>|<script.*?</script>|<!--[^<>]*<.*?-->|<div[^\u4e00-\u9fa5]*?</div>|<[/]{0,1}b>|<[/]{0,1}strong>|<[/]{0,1}h\d>|<[/]{0,1}iframe[^>].*>|<a[^>]*>[^<]*</a>|<input[^>]*>[^<]*</input>|<input[^>]*[/]{0,1}>|<head>.*?</head>','', html)#字符串替换

    newsContentList=re.findall('(?i)<p[^>]*>(.*?)</p>',html)
    newsContentList+=re.findall('(?i)>(.*?)<br>',html)
    newslist=[]
    for n in newsContentList:
         if n.find('opyright')==-1 and n.find(u'联系我们')==-1:
#             n,num=re.subn('<.*?>','',n)
             if len(n)>20:
                newslist.append('<p>'+n+'</p>')
         else:
             break
    news=''.join(newslist)
    return news
#    return news,html
def skinSubTwo(oldHtmlList,newsHtmlList):
    news=''
#    html, number = re.subn('(?i)<head>.*?</head>','', html)#字符串替换
#    html, number = re.subn('(?i)<style.*?</style>|<script.*?</script>|<!--[^<>]*<.*?-->|<div[^\u4e00-\u9fa5]</div>|<[/]{0,1}b|<[/]{0,1}strong>|<[/]{0,1}h\d>|<[/]{0,1}iframe[^>].*>>>','', html.replace('\n','').replace('\r',''))#字符串替换
#    newsContentList=re.findall('(?i)<p>(.*?)</p>',html)
#    newsContentList+=re.findall('(?i)>(.*?)<br',html)
#    newsContentList=re.findall('<div.*?</div>',html)
    
    newslist=set()
    imglist=set()
    imgsrclist=[]
    for content in oldHtmlList:
        html=content.content
        for n in html.split('\n'):
             if n.find('<meta')!=-1:
                 continue
             if n.find('opyright')==-1 and n.find(u'联系我们')==-1 :
                 if n.find('<p>')!=-1 or n.find('<P>')!=-1 or n.find('<p ')!=-1 or n.find('<P ')!=-1 or n.find('</p>')!=-1 or n.find('</P>')!=-1 or n.find('<br><br>')!=-1 or n.find('<BR><BR>')!=-1:
    #                 if len(n.split('a'))
                     n=n.strip()
                     if n not in newslist:
                        newslist.add(n)
        for img in re.findall('(?i)src=[\'\"]{0,1}([^>\s\?&]*\.jpg)',html.replace('\n','').replace('\r','')):
            imglist.add(img)
            memcache.set('img'+str(img),img,360000)
        
    for content in newsHtmlList:
        html=content.content
        realContent=[]
        realimg=[]
        picList=[]
#        nextnews=[]
#        hasContent=False
        for n in html.split('\n'):
             if n.find('<meta')!=-1:
                 continue
             if n.find('opyright')==-1 and n.find(u'联系我们')==-1 and n.find(u'版权所有')==-1:
                 if n.find('<p>')!=-1 or n.find('<P>')!=-1 or n.find('<p ')!=-1 or n.find('<P ')!=-1 or n.find('</p>')!=-1 or n.find('</P>')!=-1 or n.find('<br><br>')!=-1 or n.find('<BR><BR>')!=-1:
    #                 if len(n.split('a'))
                     n=n.strip()
                     if n not in newslist:
                        newslist.add(n)
#                        hasContent=True
                        realContent.append(n+'[()]')
#             if hasContent and '下一页' in n:
#                 for link,next in re.findall('(?i)<a\s+[^>]*href\s*=[\'\" ]*([^\s\"\']*)[\'\" ]*[^>]*>([^<]{3,6})</a>',html):
#                     if '下一页' in next:
#                         nextnews.append(link)
        news=''.join(realContent)
        #news=news.replace('<img ','[img ')
        news, number = re.subn('(?i)<style.*?</style>|<script.*?</script>','', news)#字符串替换
        news, number = re.subn('(?i)</p>|<p[^>]*>|<br><br>','[()]', news)#字符串替换
        news, number = re.subn('<[^>]*>','', news)#字符串替换
#        news=content.title+'[()]'+news
        news=news.replace('[()][()]','[()]')
        news=news.replace('[()][()]','[()]')
        #news=news.replace('[img ','<img ')
        if len(realContent)>0:
            start=html.find(content.title)
            if start<0:
                start=0
            end=html.find(realContent[len(realContent)-len(realContent)/4-1])
            html=html[start:end]
        for img in re.findall('(?i)src=[\'\"]{0,1}([^>\s\?&]*\.jpg)',html.replace('\n','').replace('\r','')):
            hasimg=memcache.get('img'+str(img))
            if  hasimg:
                continue
            memcache.set('img'+str(img),img,360000)
            if img not in imglist:
                imglist.add(img)
                if img.find('http')==-1:
                    if img[0]=='/':
                        root=re.findall('(?i)(http://[^/]*).*',content.link)
                        imgsrc=root[0]+img
                        img='<img src="%s%s" />'%(root[0],img)
                    else:
                        root=re.findall('(?i)(http://.*/)[^/]+',content.link)
                        imgsrc=root[0]+img
                        img='<img src="%s%s" />'%(root[0],img)
                else:
                    imgsrc=img
                    img='<img src="%s" />'%img
                realimg.append(img)
                pic=Picture()
                pic.content=content
                pic.src=imgsrc
                picList.append(pic)
        memcache.set('piclist'+str(content.key().id()),{'list':picList},3600*24)

        if len(realimg)>6:
            imgstr=''
        else:
            imgstr=''.join(realimg)
            imgsrclist+=picList
        content.realContent=news
        content.status='3'
#        content.realContentResult=0
#        if nextnews and len(nextnews)==1:
#            img=nextnews[0]
#            if img.find('http')==-1:
#                if img[0]=='/':
#                    root=re.findall('(?i)(http://[^/]*).*',content.link)
#                    imgsrc=root[0]+img
#                    #img='<img src="%s%s" />'%(root[0],img)
#                else:
#                    root=re.findall('(?i)(http://.*/)[^/]+',content.link)
#                    imgsrc=root[0]+img
#                    #img='<img src="%s%s" />'%(root[0],img)
#            else:
#                imgsrc=img
#                #img='<img src="%s" />'%img
#            content.next=imgsrc
#            nextContent=Contents()
#            nextContent.link=imgsrc
#            nextContent.hasFather=True
        
    db.put(newsHtmlList)
    db.put(imgsrclist)
#    news=''.join(newslist)
#    return news
def skinSubThree(oldHtmlList,html,title,link):
    news=''
    #    html, number = re.subn('(?i)<head>.*?</head>','', html)#字符串替换
    #    html, number = re.subn('(?i)<style.*?</style>|<script.*?</script>|<!--[^<>]*<.*?-->|<div[^\u4e00-\u9fa5]</div>|<[/]{0,1}b|<[/]{0,1}strong>|<[/]{0,1}h\d>|<[/]{0,1}iframe[^>].*>>>','', html.replace('\n','').replace('\r',''))#字符串替换
    #    newsContentList=re.findall('(?i)<p>(.*?)</p>',html)
    #    newsContentList+=re.findall('(?i)>(.*?)<br',html)
    #    newsContentList=re.findall('<div.*?</div>',html)

    newslist=set()
    imglist=set()
#    imgsrclist=[]
    for content in oldHtmlList:
#        html=content
        for nn in content.split('\n'):
            try:
                n=nn.decode('utf-8').strip()
            except :
                try:
                    n=nn.decode('gbk').strip()
                except :
                    try:
                        n=nn.decode('gb18030').strip()
                    except:
                        n=nn
            if n.find('<meta')!=-1:
                continue
            if n.find('opyright')==-1 and n.find(u'联系我们')==-1 :
                if n.find('<p>')!=-1 or n.find('<P>')!=-1 or n.find('<p ')!=-1 or n.find('<P ')!=-1 or n.find('</p>')!=-1 or n.find('</P>')!=-1 or n.find('<br><br>')!=-1 or n.find('<BR><BR>')!=-1:
                #                 if len(n.split('a'))
                    n=n.strip()
                    if n not in newslist:
                        newslist.add(n)
        for img in re.findall('(?i)src=[\'\"]{0,1}([^>\s\?&]*\.jpg)',content.replace('\n','').replace('\r','')):
            imglist.add(img)
            memcache.set('img'+str(img),img,360000)

#    html=content.content
    realContent=[]
    realimg=[]
    picList=[]
    realhtml=[]
    for nn in html.split('\n'):
        try:
            n=nn.decode('utf-8').strip()
        except :
            try:
                n=nn.decode('gbk').strip()
            except :
                try:
                    n=nn.decode('gb18030').strip()
                except:
                    continue
        try:
            realhtml.append(n)
            if n.find('<meta')!=-1:
                continue
            if n.find('opyright')==-1 and n.find(u'联系我们')==-1 and n.find(u'版权所有')==-1:
                if n.find('<p>')!=-1 or n.find('<P>')!=-1 or n.find('<p ')!=-1 or n.find('<P ')!=-1 or n.find('</p>')!=-1 or n.find('</P>')!=-1 or n.find('<br><br>')!=-1 or n.find('<BR><BR>')!=-1:
                    n=n.strip()
                    if n not in newslist:
                        newslist.add(n)
                        realContent.append(n+'[()]')
        except :
            pass
    html='\n'.join(realhtml)
    memcache.set(link,html,360000)
    news=''.join(realContent)
    news, number = re.subn('(?i)<style.*?</style>|<script.*?</script>','', news)#字符串替换
    news, number = re.subn('(?i)</p>|<p[^>]*>|<br><br>','[()]', news)#字符串替换
    news, number = re.subn('<[^>]*>','', news)#字符串替换
    news=news.replace('[()][()]','[()]')
    news=news.replace('[()][()]','[()]')

    if len(realContent)>0:
        start=html.find(title)
        if start<0:
            start=0
        end=html.find(realContent[len(realContent)-len(realContent)/4-1])
        html=html[start:end]
    for img in re.findall('(?i)src=[\'\"]{0,1}([^>\s\?&]*\.jpg)',html.replace('\n','').replace('\r','')):
        hasimg=memcache.get('img'+str(img))
        if  hasimg:
            continue
        memcache.set('img'+str(img),img,360000)
        if img not in imglist:
            imglist.add(img)
            if img.find('http')==-1:
                if img[0]=='/':
                    root=re.findall('(?i)(http://[^/]*).*',link)
                    imgsrc=root[0]+img
                    img='<img src="%s%s" />'%(root[0],img)
                else:
                    root=re.findall('(?i)(http://.*/)[^/]+',link)
                    imgsrc=root[0]+img
                    img='<img src="%s%s" />'%(root[0],img)
            else:
                imgsrc=img
                img='<img src="%s" />'%img
            realimg.append(img)
#            pic=Picture()
#            pic.content=content
#            pic.src=imgsrc
            picList.append(imgsrc)
#    memcache.set('piclist'+str(content.key().id()),{'list':picList},3600*24)

#    if len(realimg)>6:
#        imgstr=''
#    else:
#        imgstr=''.join(realimg)
#        imgsrclist+=picList
#    content.realContent=news
#    content.status='3'

#    db.put(newsHtmlList)
#    db.put(imgsrclist)
    return news,picList

def skinSubFour(oldHtmlList,html,title,link):
    '''
     第四版 新闻过滤。新的原理:
     1.正文都是相对集中的。正文的图片也是在正文结束前显示的。。
     2.没有超链接的图片一定是新闻图片
     3.新闻图片的alt、title 一定是相对稀少的

     优化方案：
     1.根据<p> <br>标签 相对集中的 行数 .保留下真正的新闻（所有集中的标签部分都认为是新闻）。 (不可行，有些新闻在正文之前或之后，使用了很多p标签，而且内容都是广告)
     2.将有可能是新闻的内容，坐html标签过滤。 字数多的一部分为新闻。字数少的为无用信息（因为上一条不可行，这一条也不可行了）
     3.将确认为是新闻的部分。找出最后一行的行号。新闻图片必然在这一行之前。 （因为上一条不可行，这一条也不可行了）
     4.新闻title 所在行 必然有 <h> 标签，新闻图片必然在新闻标题之下。（h标签，被多次使用，也不可行）
     5.新闻结束前的图片，没有超链接的必然是新闻图片。 （可行。现在只在p标签之间的内容中查询图片，p标签之间的行号不能大于20，大于20的不算正文内容）
     6.图片alt 、title 和新闻标题一样的必然是新闻图片 (难度太大，暂不考虑)
     7.图片alt、title 相对不重复的也有很大可能是新闻图片。(难度太大，暂不考虑)

    '''
    news=''
    #    html, number = re.subn('(?i)<head>.*?</head>','', html)#字符串替换
    #    html, number = re.subn('(?i)<style.*?</style>|<script.*?</script>|<!--[^<>]*<.*?-->|<div[^\u4e00-\u9fa5]</div>|<[/]{0,1}b|<[/]{0,1}strong>|<[/]{0,1}h\d>|<[/]{0,1}iframe[^>].*>>>','', html.replace('\n','').replace('\r',''))#字符串替换
    #    newsContentList=re.findall('(?i)<p>(.*?)</p>',html)
    #    newsContentList+=re.findall('(?i)>(.*?)<br',html)
    #    newsContentList=re.findall('<div.*?</div>',html)

    newslist=set()
    imglist=set()
#    imgsrclist=[]
    for content in oldHtmlList:
#        html=content
        for n in content.split('\n'):
            if n.find('<meta')!=-1:
                continue
            if n.find('opyright')==-1 and n.find(u'联系我们')==-1 :
                if n.find('<p>')!=-1 or n.find('<P>')!=-1 or n.find('<p ')!=-1 or n.find('<P ')!=-1 or n.find('</p>')!=-1 or n.find('</P>')!=-1 or n.find('<br><br>')!=-1 or n.find('<BR><BR>')!=-1:
                #                 if len(n.split('a'))
                    n=n.strip()
                    if n not in newslist:
                        newslist.add(n)
        for img in re.findall('(?i)src=[\'\"]{0,1}([^>\s\?&]*\.jpg)',content.replace('\n','').replace('\r','')):
            imglist.add(img)
            memcache.set('img'+str(img),img,360000)

#    html=content.content
    realContent=[]
    realContenttupl=[]
    realimg=[]
    picList=[]
    htmllist=html.split('\n')
    htmlimglist=[]
    initrow=0
    bodysite=0
    for i,n in enumerate(htmllist):
        if n.find('<meta')!=-1:
            continue
        if bodysite==0:
            if n.lower().find('<body>')>0:
                bodysite=i
            if n.lower().find('<body ')>0:
                bodysite=i
        else:
            if initrow==0 and title in n:
                initrow=i
        if n.find('opyright')==-1 and n.find(u'联系我们')==-1 and n.find(u'版权所有')==-1:
            if n.find('<p>')!=-1 or n.find('<P>')!=-1 or n.find('<p ')!=-1 or n.find('<P ')!=-1 or n.find('</p>')!=-1 or n.find('</P>')!=-1 or n.find('<br><br>')!=-1 or n.find('<BR><BR>')!=-1:
                n=n.strip()
                if n not in newslist:
                    newslist.add(n)
                    realContenttupl.append((i,'  '+n+'[()]'))
#    if len(realContenttupl)>0:
#        initrow=realContenttupl[0][0]
#    else:
#        initrow=0
    for row,text in realContenttupl:
        if (row-initrow)<20:
            htmlimglist.extend(html[initrow:row])
        initrow=row
        realContent.append(text)

    news=''.join(realContent)
    news, number = re.subn('(?i)<style.*?</style>|<script.*?</script>','', news)#字符串替换
    news, number = re.subn('(?i)</p>|<p[^>]*>|<br><br>','[()]', news)#字符串替换
    news, number = re.subn('<[^>]*>','', news)#字符串替换
    news=news.replace('[()][()]','[()]')
    news=news.replace('[()][()]','[()]')
#    if len(realContent)>0:
#        start=html.find(title)
#        if start<0:
#            start=0
#        end=html.find(realContent[len(realContent)-len(realContent)/4-1])
#        html=html[start:end]
    htmlimgtext=''.join(htmlimglist)
    for img in re.findall('(?i)src=[\'\"]{0,1}([^>\s\?&]*\.jpg)',htmlimgtext.replace('\r','')):
        hasimg=memcache.get('img'+str(img))
        if  hasimg:
            continue
        memcache.set('img'+str(img),img,360000)
        if img not in imglist:
            imglist.add(img)
            if img.find('http')==-1:
                if img[0]=='/':
                    root=re.findall('(?i)(http://[^/]*).*',link)
                    imgsrc=root[0]+img
                    img='<img src="%s%s" />'%(root[0],img)
                else:
                    root=re.findall('(?i)(http://.*/)[^/]+',link)
                    imgsrc=root[0]+img
                    img='<img src="%s%s" />'%(root[0],img)
            else:
                imgsrc=img
                img='<img src="%s" />'%img
            realimg.append(img)
#            pic=Picture()
#            pic.content=content
#            pic.src=imgsrc
            picList.append(imgsrc)
#    memcache.set('piclist'+str(content.key().id()),{'list':picList},3600*24)

#    if len(realimg)>6:
#        imgstr=''
#    else:
#        imgstr=''.join(realimg)
#        imgsrclist+=picList
#    content.realContent=news
#    content.status='3'

#    db.put(newsHtmlList)
#    db.put(imgsrclist)
    return news,picList