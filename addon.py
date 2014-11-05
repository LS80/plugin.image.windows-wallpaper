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
from __future__ import division

import os
import sys
import re
import urllib
from urlparse import urljoin, urlsplit, urlunsplit

import requests
from bs4 import BeautifulSoup
from xbmcswift2 import Plugin, xbmcgui


BASE_URL = "http://windows.microsoft.com/en-GB/windows/wallpaper"

plugin = Plugin()

def get_soup(url):
    html = requests.get(url).text
    return BeautifulSoup(html, 'html.parser')

def quote_url_path(url):
    url_split = urlsplit(url)
    path = urllib.quote(url_split.path)
    return urlunsplit((url_split.scheme, url_split.netloc, path, None, None))

def get_categories():
    for category in get_soup(BASE_URL)('a', 'tabLink'):
        item = {'label': category.text,
                'path': plugin.url_for('select_item',
                                       category_id=category['data-baseid'])}
        yield item

def get_items(category_id):
    url = urljoin(BASE_URL, "?T1={}".format(category_id))
    soup = get_soup(url)

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

class DownloadImage(object):
    def __init__(self, url, filename):
        directory = plugin.get_setting('directory')
        if not directory:
            plugin.open_settings()
        directory = plugin.get_setting('directory')

        if directory:
            path = os.path.join(directory, filename)
            url = urllib.unquote(url)
            self.progress = xbmcgui.DialogProgressBG()
            self.progress.create(plugin.get_string(30020), filename)
            urllib.urlretrieve(url, path, self.update)
        else:
            xbmcgui.Dialog().ok(plugin.get_string(30000), plugin.get_string(30021))

    def update(self, nblocks, block_size, file_size):
        percent = int(nblocks * block_size * 100 / file_size)
        self.progress.update(percent)


@plugin.route('/')
def index():
    return get_categories()

@plugin.route('/category_id/<category_id>')
def select_item(category_id):
    return get_items(category_id)


if __name__ == '__main__':
    print sys.argv
    if sys.argv[1] == 'download':
        DownloadImage(*sys.argv[2:])
    else:
        plugin.run()
