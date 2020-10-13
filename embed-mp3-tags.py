#!/usr/bin/python3
# -*- coding: utf-8 -*- 

'''
Copyright (C) 2020 Dan Nemec

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
'''

# https://id3.org/id3v2.4.0-frames
# https://www.programcreek.com/python/example/73822/mutagen.id3.APIC
# https://mutagen.readthedocs.io/en/latest/api/id3_frames.html


import pathlib
import json

from mutagen.mp3 import MP3
from mutagen.id3 import ID3,TRCK,TIT2,TALB,TPE1,TPE2,APIC,TDRC,COMM,TPOS,USLT,TLEN,TCON,TCOM

from config import ROOT_MUSIC_DIRECTORY

def write_metadata(song_f: pathlib.Path):
    metadata_f = song_f.with_suffix('.json')

    if not metadata_f.exists():
        print(f"No metadata for file '{song_f}'. Skipping.")
        return

    with open(metadata_f, 'r') as f:
        metadata = json.load(f)

    mp3 = MP3(str(song_f))
    if mp3.tags is None:
        mp3.add_tags()
    tags = mp3.tags

    title = metadata.get('title')
    if title:
        tags.add(TIT2(encoding=3, text=title))
    artist = metadata.get('artist')
    if artist:
        tags.add(TPE1(encoding=3, text=artist))
    composer = metadata.get('composer')
    if composer:
        tags.add(TCOM(encoding=3, text=composer))
    album = metadata.get('album')
    if artist:
        tags.add(TALB(encoding=3, text=album))
    albumArtist = metadata.get('albumArtist')
    if albumArtist:
        tags.add(TPE2(encoding=3, text=albumArtist))
    genre = metadata.get('genre')
    if genre:
        tags.add(TCON(encoding=3, text=genre))
    tracknum = metadata.get('trackNumber')
    if tracknum:
        tags.add(TRCK(encoding=3, text=str(tracknum)))
    year = metadata.get('year')
    if year:
        tags.add(TDRC(encoding=3, text=str(year)))
    duration = metadata.get('durationMillis')
    if duration:
        tags.add(TLEN(encoding=3, text=str(duration)))

    
    albumart_f = song_f.with_name('folder.jpg')
    if albumart_f.is_file():
        with open(albumart_f, 'rb') as f:
            tags.add(APIC(encoding=3, mime='image/jpeg', type=3,
                        desc='Front Cover', data=f.read()))
    
    mp3.save()

def main():
    root = pathlib.Path(ROOT_MUSIC_DIRECTORY)

    if not root.is_dir():
        print(f"Root folder '{ROOT_MUSIC_DIRECTORY} is not a directory.")
        return

    for song_f in root.glob('**/*.mp3'):
        try:
            #print(song_f)
            write_metadata(song_f)
        except Exception as e:
            print(f"Error found writing song '{song_f}':")
            print(e)


        


if __name__ == '__main__':
    main()
