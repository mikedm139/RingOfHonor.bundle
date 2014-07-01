####################################################################################################
PREFIX = "/video/ringofhonor"

NAME = L("Title")
ART = 'art-default.jpg'
ICON = 'icon-default.png'

CURRENT_URL = "http://www.rohwrestling.com/tv/current"

RE_OOYALA_PLAYER = Regex('var videoPlayer = OO\.Player\.create\((.+)\)')

PLAYER_URL = 'http://player.ooyala.com/player.js?embedCode=%s'
MOBILE_PLAYER_URL = 'http://player.ooyala.com/mobile_player.js?%s'

RE_EMBED_CODE = Regex('embedCode=([^&]+)')
RE_PLAYER_ARGS = Regex('var mobile_player_url="http://player.ooyala.com/mobile_player.js\?([^"]+)"')
RE_STREAM = Regex('var streams=window.oo_testEnv\?\[\]:eval\("\((?P<json>.+?)\)"\);', Regex.DOTALL)

RE_THUMB_URL = Regex('img class="oo_promoImageEndScreen" src="(http://.+?)"')

YT_FEED = 'http://gdata.youtube.com/feeds/api/users/ringofhonor/uploads?v=2&alt=json'
YT_VIDEO_URL = 'http://www.youtube.com/watch?v=%s'
YT_THUMB_URL = 'http://i1.ytimg.com/vi/%s/hqdefault.jpg'

####################################################################################################

# This function is initially called by the PMS framework to initialize the plugin. This includes
# setting up the Plugin static instance along with the displayed artwork.

def Start():
	# Setup the artwork associated with the plugin
	ObjectContainer.art = R(ART)
	ObjectContainer.title1 = NAME
	DirectoryObject.thumb = R(ICON)
	
# This main function will setup the displayed items.
@handler(PREFIX, NAME, ICON, ART, allow_sync=True)
def MainMenu():
	oc = ObjectContainer()
	
	# TV Episodes menu
	#oc.add(DirectoryObject(key=Callback(TVMenu), title=L('TV Episodes')))
	oc.add(CurrentEpisode(title=L("Latest Episode"), summary=L("Watch the latest episode of ROH"), thumb=R(ICON)))
	
	# Videos menu
	#oc.add(DirectoryObject(key=Callback(GalleryMenu), title= L("Video Galleries")))
	
	# Youtube menu
	oc.add(DirectoryObject(key=Callback(YoutubeMenu), title="ROH on YouTube", thumb=R('icon-youtube.png')))
	
	# Preferences
	#oc.add(PrefsObject)
	
	return oc

####################################################################################################


@route(PREFIX+'/current')
def CurrentEpisode(title, summary, thumb, include_container=False):
	data = HTTP.Request(CURRENT_URL, cacheTime=CACHE_1DAY).content
	player = RE_OOYALA_PLAYER.search(data)
	if player == None:
		raise Ex.MediaNotAvailable
	
	player_data = player.group(1).split(',')
	embed_code = player_data[1].strip('"')
	
	# Once we've got this, we can then request the main JS page to do with the actual player. Since it
	# only actually contains JS source, we simply obtain the content.
	player_page = HTTP.Request(PLAYER_URL % embed_code, cacheTime=0).content

	# The player page will contain a reference to the mobile JS page (including all required parameters).
	# We therefore search for the known url.
	mobile_player_page_args = RE_PLAYER_ARGS.search(player_page).group(1) + 'ipad'
	mobile_player_page = HTTP.Request(MOBILE_PLAYER_URL % mobile_player_page_args, cacheTime=0).content

	# We now have the mobile JS player page.
	try:
		stream_json = RE_STREAM.search(mobile_player_page).group('json')
		stream_json = stream_json.decode('unicode_escape')[1:-1]
		stream_details = JSON.ObjectFromString(stream_json)
	except:
		raise Ex.MediaNotAvailable
	
	title = stream_details['title']
	duration = int(stream_details['duration'])
	thumb = RE_THUMB_URL.search(mobile_player_page).group(1)
	
	episode = VideoClipObject(
		key = Callback(CurrentEpisode, title=title, summary=summary, thumb=thumb, include_container=True),
		rating_key = CURRENT_URL + '/' + str(Datetime.Now().date()),
		title = title,
		summary = summary,
		duration=duration,
		thumb = thumb,
		items = [
			MediaObject(
				parts = [PartObject(key=HTTPLiveStreamURL(stream_details['ipad_url']))]
				)
			]
		)

	if include_container:
		return ObjectContainer(objects=[episode])
	else:
		return episode
	
####################################################################################################
@route(PREFIX + '/yt')
def YoutubeMenu():
	oc = ObjectContainer(title2=L("ROH on YouTube"))
	
	rawfeed = JSON.ObjectFromURL(YT_FEED, encoding='utf-8',cacheTime=CACHE_1HOUR)
	if rawfeed['feed'].has_key('entry'):
		for video in rawfeed['feed']['entry']:
			title = video['title']['$t']
			video_id = video['media$group']['yt$videoid']['$t']
			url = YT_VIDEO_URL % video_id
			published = Datetime.ParseDate(video['published']['$t']).date()
			duration = int(video['media$group']['yt$duration']['seconds']) * 1000
			thumb = YT_THUMB_URL % video_id
			oc.add(VideoClipObject(url=url, title=title, originally_available_at=published, duration=duration, thumb=thumb))
	
	if len(oc) == 0:
		return ObjectContainer(header=L('Error'), message=L('This query did not return any result'))
	else:
		return oc

