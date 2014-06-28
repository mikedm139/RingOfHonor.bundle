####################################################################################################
VIDEO_PREFIX = "/video/ringofhonor"

NAME = "Ring of Honor"

ART = 'art-default.jpg'
ICON = 'icon-default.png'

####################################################################################################


#import re
#import ast
import urllib
from datetime import datetime
import time
import re

# This function is initially called by the PMS framework to initialize the plugin. This includes
# setting up the Plugin static instance along with the displayed artwork.

def Start():
	# Clear any previous cookies
	HTTP.ClearCookies()
	
	# Set header for any requests
	HTTP.Headers['Referrer'] = 'https://www.rohwrestling.com/user?destination=node'

	# Initialize the plugin
	Plugin.AddPrefixHandler(VIDEO_PREFIX, MainMenu, NAME, ICON, ART)
	Plugin.AddViewGroup("List", viewMode = "List", mediaType = "items")

	# Setup the artwork associated with the plugin
	MediaContainer.art = R(ART)
	MediaContainer.title1 = NAME
	MediaContainer.viewGroup = "List"
	DirectoryItem.thumb = R(ICON)
	
#def ValidatePrefs() :
#	RC = ROHSiteLogin()
#	if RC :
#		return MessageContainer("Success", "Login successful")
#	else:
#		return MessageContainer("Error", "Unable to log in. Please check username and password")

# This main function will setup the displayed items.
def MainMenu():
	dir = MediaContainer(viewMode="List")
	
	# TV Episodes menu
	dir.Append(Function(DirectoryItem(TVMenu, 'TV Episodes')))
	
	# Videos menu
	dir.Append(Function(DirectoryItem(GalleryMenu, 'Video Galleries')))
	
	# Youtube menu
	dir.Append(Function(DirectoryItem(YoutubeMenu, 'ROH on Youtube', thumb=R('icon-youtube.png'))))
	
	# Preferences
	dir.Append(PrefsItem('Preferences', thumb=R('icon-prefs.png')))

	return dir
	
# This menu displays the most recent ROH TV episode.
# Future versions that support ringside accounts will also be able to show past episodes.
def TVMenu(sender):
	#Log.Info(Prefs["username"])
	#Log.Info(Prefs["password"])
	#Log.Info(Prefs["quality"])
	
	dir = MediaContainer(viewMode="List")
	
	RC = ROHSiteLogin()
	
	summary = "Current and Previous TV shows are available to Ringside Members on the Monday after it airs on TV.\n\nCurrent TV Show will be available to GA Members every Thursday after it airs on TV."
	#try:
	page = HTML.ElementFromURL('https://www.rohwrestling.com/tv/watch-now')
	dir.Append(ParseVideoPage(page, isTV=True, title = page.xpath('//div["views-field-title"]//span["field-content"]//h2')[0].text, summary=summary))
	#except:
	#	return MessageContainer("Error", "Unable to find video. Make sure username and password are correct.")

	return dir
	
# This menu displays video galleries from the ROH site
def GalleryMenu(sender):
	
	dir = MediaContainer(viewMode="List")
	
	gallery = []
	i = 0
	
	# Get first page of gallery data
	gallery.append(JSON.ObjectFromURL('https://www.rohwrestling.com/views/ajax?js=1&page=0&view_name=video_gallery&view_display_id=page_1&view_path=media%2Fvideos&view_base_path=media%2Fvideos&view_dom_id=1&pager_element=0&view_args='))
	
	# The gallery AJAX API seems to return the first page of data (page 0) any time the page number is invalid.
	# So, to determine if we've reached the end of the data, we compare the page we just received to the first page.
	while (i == 0) or (gallery[i] != gallery[0]) :
	
		# Translate JSON element into HTML for further parsing
		gallerypage = HTML.ElementFromString(gallery[i]["display"])
		#Log.Info (HTML.StringFromElement(gallerypage))
		
		# Find each gallery as we go through HTML objects
		items = gallerypage.xpath('//ul[@class="views-fluid-grid-list"]//li')
		for item in items:
			# Get data for each video gallery
			url = "http://www.rohwrestling.com" + item.xpath('.//div[@class="views-field-phpcode"]//a')[0].get('href')
			image = item.xpath('.//div[@class="views-field-phpcode"]//img')[0].get('src')
			title = item.xpath('.//div[@class="views-field-title"]//a')[0].text
			
			# Get higher-res image
			image = image.replace("rotor_carousel_thumbnail", "news_featured_photo")
			
			# Add directory item for each gallery
			dir.Append(Function(DirectoryItem(VideoMenu, title, summary="", thumb=image), url=url))			
			
		# Get the next page and take it from the top
		i = i + 1
		gallery.append(JSON.ObjectFromURL('https://www.rohwrestling.com/views/ajax?js=1&page=' + str(i) + '&view_name=video_gallery&view_display_id=page_1&view_path=media%2Fvideos&view_base_path=media%2Fvideos&view_dom_id=1&pager_element=0&view_args='))
	
	return dir

def VideoMenu(sender, url):
	dir = MediaContainer(viewMode="List")
	
	# Get video gallery page
	page = HTML.ElementFromURL(url)
	
	# Scrape for individual video elements
	items = page.xpath('//div[@id="content-area"]//ul[@class="views-fluid-grid-list"]//li')
	for item in items :
		#Log.Info(HTML.StringFromElement(item))
		#vidurl = 'http://www.rohwrestling.com' + item.xpath('.//div[@class="views-field-field-video-cover-image-ref-nid"]//a[@class="vidpullajax"]')[0].get('href')
		#vidjson = JSON.ObjectFromURL(vidurl)
		#vidhtml = HTML.ElementFromString(vidjson["video"])
		vidurl = 'http://www.rohwrestling.com' + item.xpath('.//div[@class="views-field-title"]//a')[0].get('href')
		vidhtml = HTML.ElementFromURL(vidurl)
		title=item.xpath('.//div[@class="views-field-title"]//a')[0].text
		
		#Log.Info(HTML.StringFromElement(vidhtml))
		dir.Append(ParseVideoPage(vidhtml, isTV=False, title=title))
	
	return dir
	
# ROHSiteLogin():
# Logs in to ROH website
# Returns True if login successful, False if login unsuccessful	
def ROHSiteLogin():
	# Clear any previous cookies
	HTTP.ClearCookies()
	HTTP.Headers['Referrer'] = 'https://www.rohwrestling.com/user?destination=node'
	
	# Get login page
	loginpage = HTML.ElementFromURL('https://www.rohwrestling.com/user?destination=node')
	buildid = loginpage.xpath('//div[@id="content-area"]//input[@name="form_build_id"]')[0].get('value')
	#Log.Info(buildid)
	
	# Build dictionary object for login
	postdata = dict({'name': Prefs["username"], 'pass': Prefs["password"], 'form_build_id': buildid, 'form_id': 'user_login', 'op': 'Log in'})
	#Log.Info(postdata)
	
	# log in to site
	login = HTTP.Request('https://www.rohwrestling.com/user?destination=node', postdata)
	
	# Check for presence of error message, and return appropriate value
	return '<li class="message-item first">' not in login.content

# ParseVideoPage() :
# 	Takes an HTML Element and looks for video objects
#	Parameters:
#		page = HTML Element
#		isTV = True if TV page (and thus has high-quality variant), false otherwise.  Defaults to false.
#		summary = Summary to return with RTMPVideoItem.  Defaults to empty string
#	Returns RTMPVideoItem
def ParseVideoPage(page, isTV=False, title="", summary="", thumb=""):
	
	# Get page
	# page = HTML.ElementFromURL(url)
	# Log.Info(HTML.StringFromElement(page))
	
	# Get video title if no title given
	if title == "" :
		title = page.xpath('//div["views-field-title"]//span["field-content"]//h2')[0].text
	
	# Parse player parameters from javascript
	pagestr = HTML.StringFromElement(page) # convert to string
	
	#find appropriate JSON parameter block
	if Prefs["quality"] == "Low" or not isTV:
		start = pagestr.find('{"height":') 
	else :
		start = pagestr.find('showhifivdo')  #Find "showhifivdo" function
		start = pagestr.find('{ "height":', start)  #hifi video JSON has a space between bracket and height parameter
	end = pagestr.find('}',start)
	#paramstring = pagestr[start:end]
	#params = dict(ast.literal_eval(paramstring))
	params = JSON.ObjectFromString(pagestr[start:(end + 1)])
	
	# Pull arguments to build video object
	streamer = params['streamer']
	
	extstart = params['file'].find('.')
	if params['file'][extstart:len(params['file'])] == ".mp4" :
		file = "mp4:" + params['file'][0:extstart]
	else:
		file = params['file'][0:extstart]
		
	
	# If no thumbnail is given, scrape one
	if thumb == "" :
		thumb = "http://www.rohwrestling.com" + urllib.unquote_plus(params['image'])
		
	if thumb[0:3] == "http" :
		HTTP.PreCache(image)
	
	#Log.Info('streamer = ' + streamer)
	#Log.Info('file = ' + file)
	#Log.Info('image = ' + image)
	#Log.Info('title = ' + title)
	
	# Add video item to menu
	return RTMPVideoItem(url=streamer, clip=file, live=False, title=title, summary=summary, thumb=thumb)
	
#####################################################################################################
#
#  Below code from Youtube kickstarter
#
#####################################################################################################
####################################################################################################

FEED = 'http://gdata.youtube.com/feeds/api/users/ringofhonor/uploads?v=2'
YOUTUBE_VIDEO_PAGE = 'http://www.youtube.com/watch?v=%s'
YOUTUBE_VIDEO_FORMATS = ['Standard', 'Medium', 'High', '720p', '1080p']
YOUTUBE_FMT = [34, 18, 35, 22, 37]

####################################################################################################
	
def YoutubeMenu(sender):

    dir = MediaContainer(viewGroup="InfoList",title2=L('Episodes'), httpCookies=HTTP.GetCookiesForURL('http://www.youtube.com/'))
    dir = FeedMenu(feed = FEED)
    return dir

def FeedMenu(feed=''):
    dir = MediaContainer(viewGroup="InfoList",title2=L('Episodes'), httpCookies=HTTP.GetCookiesForURL('http://www.youtube.com/'))

    if '?' in feed:
	  feed = feed + '&alt=json'
    else:
	  feed = feed + '?alt=json'

    rawfeed = JSON.ObjectFromURL(feed, encoding='utf-8',cacheTime=CACHE_1HOUR)
    if rawfeed['feed'].has_key('entry'):
      for video in rawfeed['feed']['entry']:
        if video.has_key('yt$videoid'):
          video_id = video['yt$videoid']['$t']
        elif video['media$group'].has_key('media$player'):
          try:
            video_page = video['media$group']['media$player'][0]['url']
          except:
            video_page = video['media$group']['media$player']['url']
          video_id = re.search('v=([^&]+)', video_page).group(1)
        else:
          video_id = None      
        title = video['title']['$t']

        if (video_id != None) and not(video.has_key('app$control')):
	      try:
		    published = Datetime.ParseDate(video['published']['$t']).strftime('%a %b %d, %Y')
	      except: 
	  	    published = Datetime.ParseDate(video['updated']['$t']).strftime('%a %b %d, %Y')
	      if video.has_key('content') and video['content'].has_key('$t'):
		    summary = video['content']['$t']
	      else:
		    summary = video['media$group']['media$description']['$t']
	      duration = int(video['media$group']['yt$duration']['seconds']) * 1000
	      try:
		    rating = float(video['gd$rating']['average']) * 2
	      except:
		    rating = 0
	      thumb = video['media$group']['media$thumbnail'][0]['url']
	      dir.Append(Function(VideoItem(PlayVideo, title=title, subtitle=published, summary=summary, duration=duration, rating=rating, thumb=Function(Thumb, url=thumb)), video_id=video_id))
	
    if len(dir) == 0:
      return MessageContainer(L('Error'), L('This query did not return any result'))
    else:
      return dir

def Thumb(url):
  try:
    data = HTTP.Request(url, cacheTime=CACHE_1WEEK).content
    return DataObject(data, 'image/jpeg')
  except:
    return Redirect(R(ICON))
    
def PlayVideo(sender, video_id):
  yt_page = HTTP.Request(YOUTUBE_VIDEO_PAGE % (video_id), cacheTime=1).content
    
  fmt_url_map = re.findall('"url_encoded_fmt_stream_map".+?"([^"]+)', yt_page)[0]
  fmt_url_map = fmt_url_map.replace('\/', '/').split(',')

  fmts = []
  fmts_info = {}

  for f in fmt_url_map:
    map = {}
    params = f.split('\u0026')
    for p in params:
      (name, value) = p.split('=')
      map[name] = value
    quality = str(map['itag'])
    fmts_info[quality] = String.Unquote(map['url'])
    fmts.append(quality)

  index = YOUTUBE_VIDEO_FORMATS.index(Prefs['youtube_fmt'])
  if YOUTUBE_FMT[index] in fmts:
    fmt = YOUTUBE_FMT[index]
  else:
    for i in reversed( range(0, index+1) ):
      if str(YOUTUBE_FMT[i]) in fmts:
        fmt = YOUTUBE_FMT[i]
        break
      else:
        fmt = 5

  url = (fmts_info[str(fmt)]).decode('unicode_escape')
  Log("  VIDEO URL --> " + url)
  return Redirect(url)



