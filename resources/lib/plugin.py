# -*- coding: utf-8 -*-

import routing

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin

import re
import time
import datetime
import json
from bs4 import BeautifulSoup
import requests

_addon = xbmcaddon.Addon()

plugin = routing.Plugin()

_baseurl = 'https://tv.idnes.cz/'
_videourl = 'https://servix.idnes.cz/media/video.aspx'

def get_page(url):
    r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.68 Safari/537.36'})
    return r.content

@plugin.route('/')
def root():
    listing = []
    list_item = xbmcgui.ListItem(_addon.getLocalizedString(30001))
    list_item.setArt({'icon': 'DefaultRecentlyAddedEpisodes.png'})
    listing.append((plugin.url_for(get_list,  show_url = _baseurl+'archiv'), list_item, True))
    
    list_item = xbmcgui.ListItem(_addon.getLocalizedString(30002))
    list_item.setArt({'icon': 'DefaultTVShows.png'})
    listing.append((plugin.url_for(list_shows), list_item, True))
    
    list_item = xbmcgui.ListItem(_addon.getLocalizedString(30004))
    list_item.setArt({'icon': 'DefaultTVShows.png'})
    listing.append((plugin.url_for(list_news), list_item, True))
    
    xbmcplugin.addDirectoryItems(plugin.handle, listing, len(listing))
    xbmcplugin.endOfDirectory(plugin.handle)
    
@plugin.route('/list_shows/')
def list_shows():
    xbmcplugin.setContent(plugin.handle, 'tvshows')
    soup = BeautifulSoup(get_page(_baseurl+'porady'), 'html.parser')
    porady = soup.find('div', {'class': 'entry-list'}).find_all('div', {'class': 'entry entry-square'})
    
    listing = []
    for porad in porady:
        name = porad.find('h3').get_text()
        url = porad.find('a', {'class': 'art-link'})['href']
        thumb = 'https:'+(re.search('url\(\'(.+)\'\)', porad.find('div', {'class': 'art-img'})['style'])).group(1)
        
        list_item = xbmcgui.ListItem(label=name)
        list_item.setInfo('video', {'mediatype': 'tvshow', 'title': name, 'plot': url})
        list_item.setArt({'icon': thumb})
        listing.append((plugin.url_for(get_list, show_url = url), list_item, True))
        
    xbmcplugin.addDirectoryItems(plugin.handle, listing, len(listing))
    xbmcplugin.endOfDirectory(plugin.handle)
    
@plugin.route('/list_news/')
def list_news():
    xbmcplugin.setContent(plugin.handle, 'tvshows')
    soup = BeautifulSoup(get_page(_baseurl), 'html.parser')
    porady = soup.find('menu', {'id': 'menu'}).find('ul').find_all('li')

    listing = []
    for porad in porady:
        name = porad.find('a').get_text()
        url = 'https:'+porad.find('a')['href']
        list_item = xbmcgui.ListItem(label=name)
        listing.append((plugin.url_for(get_list, show_url = url), list_item, True))
        
    xbmcplugin.addDirectoryItems(plugin.handle, listing, len(listing))
    xbmcplugin.endOfDirectory(plugin.handle)
    
@plugin.route('/get_list')
def get_list():
    xbmcplugin.setContent(plugin.handle, 'episodes')
    url = plugin.args['show_url'][0]
    soup = BeautifulSoup(get_page(url), 'html.parser') #+"/"+str(page)
    items = soup.find('div', {'class': 'entry-list'}).find_all('div', {'class': 'entry'})
    count = 0
    listing = []
    for item in items:
        title = item.find('h3').get_text()
        dur = item.find('span', {'class': 'length'}).get_text()
        if dur:
            l = dur.strip().split(':')
            duration = 0
            for pos, value in enumerate(l[::-1]):
                duration += int(value) * 60 ** pos

        video_id = item.find('a', {'class': 'art-link'})['data-id']
        date = datetime.datetime(*(time.strptime(item.find('span', {'class': 'time'})['datetime'], "%Y-%m-%dT%H:%M:%S")[:6])).strftime("%Y-%m-%d")
        thumb = 'https:'+(re.search('url\(\'(.+)\'\)', item.find('div', {'class': 'art-img'})['style'])).group(1)
            
        list_item = xbmcgui.ListItem(title)
        list_item.setInfo('video', {'mediatype': 'episode', 'title': title, 'duration': duration, 'premiered': date})
        list_item.setArt({'icon': thumb})
        list_item.setProperty('IsPlayable', 'true')
        listing.append((plugin.url_for(get_video, video_id), list_item, False))
        count += 1
    
    next_url = soup.find('a', {'class': 'btn btn-on'})['href']
    
    #fix pro Rozstrel
    if 'strana' in next_url:
        next_url = url+next_url
        
    if next_url:
        list_item = xbmcgui.ListItem(label=_addon.getLocalizedString(30003))
        list_item.setArt({'icon': 'DefaultFolder.png'})
        listing.append((plugin.url_for(get_list, show_url = next_url), list_item, True))
    
    xbmcplugin.addDirectoryItems(plugin.handle, listing, len(listing))
    xbmcplugin.endOfDirectory(plugin.handle)
  
@plugin.route('/get_video/<video_id>')
def get_video(video_id):  
    xml = BeautifulSoup(get_page(_videourl+"?idvideo="+video_id))
    server = 'https://'+xml.find("server").get_text()
    videofile = xml.find("linkvideo").find("file", {'quality': 'high'}).get_text()
    stream_url = server + "/" + videofile
       
    list_item = xbmcgui.ListItem(path=stream_url)
    xbmcplugin.setResolvedUrl(plugin.handle, True, list_item)

def run():
    plugin.run()
    