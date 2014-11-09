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
import urllib2
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


class DownloadError(Exception):
    pass


class DownloadProgress(object):

    BLOCK_SIZE = 131072

    def __init__(self, heading, remote, outpath, size):
        self._heading = heading
        self._remote = remote
        self._outpath = outpath
        self._outfile = os.path.basename(outpath)
        self._out = None
        
        self._size = size
        self._progress = xbmcgui.DialogProgressBG()  
        self._done = 0
 
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._remote.close()
        if self._out is not None:
            self._out.close()

        self._progress.close()

        if exc_type is not None:
            xbmcvfs.delete(self._outpath)

    def start(self):
        self._progress.create(self._heading, self._outfile)
        self._out = xbmcvfs.File(self._outpath, 'w')

        while self._done < self._size:
            data = self._remote.read(self.BLOCK_SIZE)
            self._done += len(data)
            result = self._out.write(data)
            if not result:
                raise DownloadError(plugin.get_string(30024))
            percent = int(self._done * 100 / self._size)
            self._progress.update(percent)


class DownloadImage(object):
    def __init__(self, url, filename):
        directory = plugin.get_setting('directory')
        if not directory:
            plugin.open_settings()
        directory = plugin.get_setting('directory')

        if directory:
            path = os.path.join(directory, filename)
            url = urllib.unquote(url)
            try:
                response = requests.get(url, stream=True)
                size = int(response.headers["content-length"])
            except Exception as e:
                xbmcgui.Dialog().ok(plugin.get_string(30022), str(e), url)
            else:
                try:
                    with DownloadProgress(plugin.get_string(30020),
                                          response.raw, path, size) as downloader:
                        downloader.start()
                except DownloadError as e:
                    xbmcgui.Dialog().ok(plugin.get_string(30022), str(e), path,
                                        plugin.get_string(30023))
                    plugin.open_settings()


@plugin.route('/')
def index():
    return get_categories()

@plugin.route('/category/<category>')
def select_item(category):
    return get_items(category)


if __name__ == '__main__':
    print sys.argv
    if sys.argv[1] == 'download':
        DownloadImage(*sys.argv[2:])
    else:
        plugin.run()
