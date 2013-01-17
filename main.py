#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import webapp2
from news.interface import saveRSS, listRSS, syncRSS, initRSS
from news.urlmanage import getRss, getContent, getNewsSubOne,default, addRSS, Look, getAnalysis, DetailLook, detailSkin1, deleteContents, getWebsiteRSS, downloadpic, showImg, showPiclist, RSSMsg
from news.weather import Weather, GuPiao


app = webapp2.WSGIApplication([
                                        ('/', default),

                                        ('/saveRSS', saveRSS),
                                        ('/rssList', listRSS),

                                        ('/RSS',getRss),
                                        ('/syncRSS',syncRSS),
                                        ('/initRSS',initRSS),
                                        ('/getWebsiteRSS',getWebsiteRSS),
                                        ('/rssMsg',RSSMsg),
                                        ('/Content/(\d{1,2})',getContent),
                                        ('/Skin1',getNewsSubOne),
                                        ('/addRSS',addRSS),
                                        ('/look',Look),
                                        ('/detailLook',DetailLook),
                                        ('/detailSkin1',detailSkin1),
                                        ('/analysis',getAnalysis),
                                        ('/delete',deleteContents),
                                        ('/img',showImg),
                                        ('/pic',showPiclist),
                                        ('/downloadimg',downloadpic),


                                        ('/weather',Weather),
                                        ('/gupiao',GuPiao),
#                                        ('/testurl',testurl),

                              ],
                                         debug=True)
def main():
    pass

#    util.run_wsgi_app(app)


if __name__ == '__main__':
    main()