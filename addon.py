# coding=utf-8
##########################################################################
#
#  Copyright 2014 Lee Smith
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
# 
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
# 
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##########################################################################

import os
import sys
import re
import urllib
from urlparse import urljoin, urlsplit, urlunsplit

import requests
from bs4 import BeautifulSoup
from xbmcswift2 import Plugin, xbmcgui
try:
    import xbmcvfs
except ImportError:
    from xbmcswift2 import xbmcvfs


BASE_URL = "http://windows.microsoft.com/en-GB/windows/wallpaper"

plugin = Plugin()

def get_soup(url):
    try:
        html = requests.get(url).text
    except:
        return None
    else:
        return BeautifulSoup(html, 'html.parser')

def quote_url_path(url):
    url_split = urlsplit(url)
    path = urllib.quote(url_split.path)
    return urlunsplit((url_split.scheme, url_split.netloc, path, None, None))

def get_categories():
    soup = get_soup(BASE_URL)
    if soup is None:
        return
        yield

    for category in soup('a', 'tabLink'):
        item = {'label': category.text,
                'path': plugin.url_for('select_item',
                                       category=category['data-baseid'])}
        yield item

def get_items(category):
    url = urljoin(BASE_URL, "?T1={}".format(category))
    soup = get_soup(url)
    if soup is None:
        return
        yield

    for image in soup('div', 'prodPane'):
        name = image.find('h2', 'headingBase').string
        label = name.encode('utf-8')
        href = quote_url_path(image.find('a', 'navigationLink')['href'])

        ext = os.path.splitext(href)[1]
        name_lower = re.sub('[,()]', '', name.lower())
        filename = u"{0}{1}".format('_'.join(name_lower.split()), ext).encode('utf-8')

        thumbnail = quote_url_path(image.find('img')['src'])

        download_action = "RunScript({0}, download, {1}, {2})".format(plugin.id,
                                                                      href,
                                                                      filename)
        item = {'label': name,
                'path': href,
                'is_playable': True,
                'thumbnail': thumbnail,
                'context_menu': [('Download', download_action)]}

        yield item


@plugin.route('/')
def index():
    return get_categories()

@plugin.route('/category/<category>')
def select_item(category):
    return plugin.finish(get_items(category), view_mode='thumbnail')


if __name__ == '__main__':
    if sys.argv[1] == 'download':
        import script
        script.DownloadImage(*sys.argv[2:])
    else:
        plugin.run()
