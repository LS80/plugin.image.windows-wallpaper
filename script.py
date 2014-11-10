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
import urllib

import requests
from xbmcswift2 import Plugin
import xbmcgui, xbmcvfs

plugin = Plugin()


class DownloadError(Exception):
    pass


class DownloadProgress(object):

    BLOCK_SIZE = 16384

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
            try:
                data = self._remote.read(self.BLOCK_SIZE)
            except Exception as e:
                raise DownloadError(str(e))
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
                response = requests.get(url, stream=True, timeout=5)
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


if __name__ == '__main__':
    if len(sys.argv) == 1:
        xbmc.executebuiltin("RunAddon(plugin.image.windows-wallpaper)")
    elif sys.argv[1] == 'download':
        DownloadImage(*sys.argv[2:])
