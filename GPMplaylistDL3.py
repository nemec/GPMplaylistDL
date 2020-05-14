#!/usr/bin/python3
# -*- coding: utf-8 -*- 
'''
This is a little script to download every song from every playlist
if your Google Play Music account. Songs are organized as follows:
    <playlist>/<artist>/<album>/<song>.mp3

I Highly recomend putting this file in your %USER%\Music folder
before running.

Please note that this will ONLY work if you have a subscription.

Requirements:
- gmusicapi
- requests

For further documentation on what I'm using here, check out:
http://unofficial-google-music-api.readthedocs.io/en/latest/reference/mobileclient.html
'''

from gmusicapi import Mobileclient
from gmusicapi.exceptions import CallFailure
import requests
import os, unicodedata
import sys
from pprint import pprint
import json
import re
from config import (
    GOOGLE_USERNAME, GOOGLE_PASSWORD,
    ROOT_MUSIC_DIRECTORY, DEVICE_MAC_ADDRESS,
    IGNORE_PLAYLISTS
)

# Account settings


# Output Settings
showSongs = True # set to true to show each song path before it's downloaded
quiet = False # set to true to completely silence

# Playlist settings
## Export as...
m3u = True
winamp = False

if ROOT_MUSIC_DIRECTORY == "" or ROOT_MUSIC_DIRECTORY is None:
    ROOT_MUSIC_DIRECTORY = os.path.realpath('.')


# Here thar be dragons

# Start with some declarations
def dlSong(id, name):
    try:
        url = mc.get_stream_url(id, device_id=device_id)
    except CallFailure as e:
        print(e)
        return
    r = requests.get(url, stream=True)
    with open(name, "wb") as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)

def dl_art(url, path):
    r = requests.get(url, stream=True)
    with open(path, "wb") as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)

def dl_metadata(metadata, path):
    with open(path, "w") as f:
        f.write(metadata)


def clean(s):
    # https://github.com/django/django/blob/master/django/utils/text.py#L221
    """
    Copyright (c) Django Software Foundation and individual contributors.
    All rights reserved.

    Redistribution and use in source and binary forms, with or without modification,
    are permitted provided that the following conditions are met:

        1. Redistributions of source code must retain the above copyright notice,
        this list of conditions and the following disclaimer.

        2. Redistributions in binary form must reproduce the above copyright
        notice, this list of conditions and the following disclaimer in the
        documentation and/or other materials provided with the distribution.

        3. Neither the name of Django nor the names of its contributors may be used
        to endorse or promote products derived from this software without
        specific prior written permission.

    THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
    ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
    WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
    DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
    ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
    (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
    LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
    ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
    (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
    SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
    """
    s = str(s).strip()
    s = re.sub(r'\s+', ' ', s)
    return re.sub(r"(?u)[^-\w.&, ']", "", s)
    if len(bytes(s.encode('utf-8'))) > 250:
        s = s.encode('utf-8')[:250].decode('utf-8', errors='ignore')
    return s

class Playlist(object):
    def __init__(self, name):
        name = clean(name)
        self.name = name
        self.path = name
        self.songs = []

    def __repr__(self):
        return "{}: {} songs".format(self.name, len(self.songs))

    def addSong(self, song):
        self.songs.append(song)

    def makeAlbumPath(self, song):
        path = song.path = os.path.join(ROOT_MUSIC_DIRECTORY, clean(song.artist), clean(song.album))
        if os.path.exists(song.path):
            return path
        try:
            os.makedirs(song.path)
        except:
            pass
        return path

    def makeArtistPath(self, song):
        path = os.path.join(ROOT_MUSIC_DIRECTORY, clean(song.artist))
        if os.path.exists(path):
            return path
        try:
            os.makedirs(path)
        except:
            pass
        return path

    def songPath(self, song):
        path = self.makeAlbumPath(song)
        return os.path.join(path, clean(song.title) + ".mp3")

    def metadataPath(self, song):
        path = self.makeAlbumPath(song)
        return os.path.join(path, clean(song.title) + ".json")

    def albumArtPath(self, song):
        path = self.makeAlbumPath(song)
        return os.path.join(path, "folder.jpg")

    def artistArtPath(self, song):
        path = self.makeArtistPath(song)
        return os.path.join(path, "folder.jpg")


class Song(object):
    def __init__(self, tid, title, number, artist, album, length, artist_art_url, album_art_url, metadata):
        self.tid = clean(tid)
        self.title = clean(title)
        self.number = number
        self.artist = clean(artist)
        self.album = clean(album)
        self.length = length
        self.artist_art_url = artist_art_url
        self.album_art_url = album_art_url
        self.metadata = metadata
    def __repr__(self):
        return "{} - {}".format(self.artist, self.title)

# Login
mc = Mobileclient()
mc.__init__(debug_logging=False, validate=True, verify_ssl=True)
if DEVICE_MAC_ADDRESS is not None:
    mc.login(GOOGLE_USERNAME, GOOGLE_PASSWORD, DEVICE_MAC_ADDRESS)
else: 
    mc.login(GOOGLE_USERNAME, GOOGLE_PASSWORD, mc.FROM_MAC_ADDRESS)


# Pick a device_id for downloading later
device_id = None
for device in mc.get_registered_devices():
    if device['type'] == 'ANDROID':
        device_id = device['id'][2:] #.encode('ascii','ignore')
        break
    elif device['type'] == 'IOS':
        device_id = device['id']
        break

if not device_id:
    print("No Android or iOS device linked to account!")
    exit()

mc = Mobileclient()
mc.login(GOOGLE_USERNAME, GOOGLE_PASSWORD, device_id)


# Grab all playlists, and sort them into a structure
mc.get_all_playlists()
playlists = mc.get_all_user_playlist_contents()
if not quiet:
    print(len(playlists), "playlist(s) found.")
master = []
for ply in playlists:
    name = ply['name']
    curPlaylist = Playlist(name)
    tracks = ply['tracks']
    for song in tracks:
        if song['source'] == u"2": # If song is not custom upload
            #pprint(song)
            tid = song['trackId']
            title = song['track']['title']
            number = song['track']['trackNumber']
            artist = song['track']['artist']
            album = song['track']['album']
            artist_art = song['track'].get('artistArtRef', [{}])[0].get('url')
            album_art = song['track'].get('albumArtRef', [{}])[0].get('url')
            length = int(song['track']['durationMillis']) / 1000
            metadata = json.dumps(song['track'], indent=2)
            newSong = Song(tid, title, number, artist, album, length, artist_art, album_art, metadata)
            curPlaylist.addSong(newSong)
    master.append(curPlaylist)


# thumbs up playlist
curPlaylist = Playlist('auto-playlist-thumbs-up')
songs = mc.get_all_songs()
thumbs_up_lib = [t for t in songs if t.get('rating') == '5']
track_cache = set()
if thumbs_up_lib:
    if not quiet:
        print("Downloading thumbs-up playlist data")
    for info in thumbs_up_lib:
        tid = info.get('storeId')
        if not tid or tid in track_cache:
            continue
        track_cache.add(tid)
        title = info['title']
        number = info['trackNumber']
        artist = info['artist']
        album = info['album']
        artist_art = song['track'].get('artistArtRef', [{}])[0].get('url')
        album_art = info.get('albumArtRef', [{}])[0].get('url')
        length = int(info['durationMillis']) / 1000
        metadata = json.dumps(info, indent=2)
        newSong = Song(tid, title, number, artist, album, length, artist_art, album_art, metadata)
        curPlaylist.addSong(newSong)
if os.path.isfile('getephemthumbsup.json'):
    if not quiet:
        print("Adding data from getephemthumbsup json file")
    artist_cache = {}
    # get response when desktop client posts to
    # https://play.google.com/music/services/getephemthumbsup
    with open('getephemthumbsup.json', 'r') as f:
        j = json.loads(f.read())
        track_ids = [x[0] for x in j[1][0]]
        for tid in track_ids:
            if tid in track_cache:
                continue
            track_cache.add(tid)

            info = mc.get_track_info(tid)
            title = info['title']
            number = info['trackNumber']
            artist = info['artist']
            album = info['album']
            album_art = info.get('albumArtRef', [{}])[0].get('url')
            length = int(info['durationMillis']) / 1000
            metadata = json.dumps(info, indent=2)

            artist_id = info['artistId'][0]
            if artist_id in artist_cache:
                a_info = artist_cache[artist_id]
            else:
                a_info = mc.get_artist_info(
                    artist_id, 
                    include_albums=False, 
                    max_top_tracks=0, 
                    max_rel_artist=0)
                artist_cache[artist_id] = a_info
            artist_art = a_info.get('artistArtRef')

            newSong = Song(tid, title, number, artist, album, length, artist_art, album_art, metadata)
            curPlaylist.addSong(newSong)
if curPlaylist.songs:
    master.append(curPlaylist)

print(master)

# Step through the playlists and download songs
for playlist in master:
    if playlist.name in IGNORE_PLAYLISTS:
       continue
    if not quiet:
        print("Grabbing", playlist)
    for song in playlist.songs:
        albumart_path = playlist.albumArtPath(song)
        #print(f"Album Art: {albumart_path}, {song.album_art_url}")
        if song.album_art_url and not os.path.isfile(albumart_path):
            dl_art(song.album_art_url, albumart_path)
            
        artistart_path = playlist.artistArtPath(song)
        #print(f"Artist Art: {artistart_path}, {song.artist_art_url}")
        if song.artist_art_url and not os.path.isfile(artistart_path):
            dl_art(song.artist_art_url, artistart_path)

        metadata_path = playlist.metadataPath(song)
        if not os.path.isfile(metadata_path):
            dl_metadata(song.metadata, metadata_path)
        
        path = playlist.songPath(song)
        if not os.path.isfile(path): # Skip existing songs
            if showSongs and not quiet:
                print("DL:", path)
            dlSong(song.tid, path)


# Deal with playlists
if m3u:
    for playlist in master:
        fname = playlist.name + ".m3u"
        with open(fname, "w+") as f:
            f.write("#EXTM3U\n")
            for song in playlist.songs:
                meta = "#EXTINF:{},{}".format(song.length, song)
                path = os.path.join(ROOT_MUSIC_DIRECTORY, playlist.songPath(song))
                f.write(meta + "\n")
                f.write(path + "\n")

if winamp:
    for playlist in master:
        fname = playlist.name + ".pls"
        with open(fname, "w+") as f:
            f.write("[playlist]")
            for i, song in enumerate(playlist.songs):
                path = os.path.join(ROOT_MUSIC_DIRECTORY, playlist.songPath(song))
                f.write("File{}={}\n".format(i, path))
                f.write("Title{}={}\n".format(i, song.title))
                f.write("Length{}={}\n".format(i, song.length))
            f.write("NumberOfEntries={}".format(len(playlist.songs)))
            f.write("Version=2")

