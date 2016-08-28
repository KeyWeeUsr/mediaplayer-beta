from kivy.utils import platform
from kivy.clock import Clock
from kivy.logger import Logger
from time import sleep
from default_providers import *
import traceback
if platform == 'android':
    from android_intents import android_fileExt_activity
    from android_native_player import Android_Native_Player

def printer(text):
    print str(text)

class Playlist(object):
    def __init__(self,*args,**kwargs):
        self.list = []
        self.current = 0
        self.length = 0

    def get_next(self):
        self.current +=1
        if self.length != 0:
            try:
                return self.current, self.list[self.current]
            except:
                self.current = 0
                return self.current, self.list[self.current]
        else:
            raise Exception('Playlist error','list is empty')

    def get_previous(self):
        self.current -= 1
        if self.length != 0:
            try:
                return self.current, self.list[self.current]
            except:
                self.current = self.length-1
                return self.current, self.list[self.current]
        else:
            raise Exception('Playlist error','list is empty')

    def get_current(self):
        name = self.list[self.current]['name']
        path = self.list[self.current]['path']
        return self.current, (name, path)

    def set_current(self,value):
        self.current = int(value)

    def add(self,name,path,**kwargs):
        appending = {'name': name, 'path': path}
        for key,value in kwargs.iteritems():
            self.appending['key'] = value
        self.list.append(appending)
        self.length += 1

    def reset(self):
        self.current = 0
        self.length = 0
        self.list = []


class Media_Player(object):
    class Dummy(object):
        class Sound(object):
            def __init__(self):
                self.sound, self.state = 'Dummy', 'Dummy'
            def seek(self): return 0
            def unload(self): pass
        def __init__(self):
            self.state = 'stop'
            self.length, self.source, name_name, self.sound = 0, False, False, self.Sound()
            self.paused = False
        def unload(self,*arg): return 'Dummy'
        def play(self,*arg): return 'Dummy'
        def stop(self,*arg): return 'Dummy'
        def get_pos(self,*arg): return 0
        def seek(self,*arg): return 'Dummy'

    def __init__(self):
        self.paused = False
        self.pauseSupported = False
        self.sound, self.state = False, 'stop'
        self.gui_update = None
        self.starting = False
        self.playlist = Playlist()
        self.mediaName = ''
        self.sound = self.Dummy()
        self.player = 'audio'
        self.stream = False
        self.modes = {'next_on_stop': True,
                      'on_video': [],
                      'on_start': [],
                      'on_next': [],
                      'on_previous': []}
        self.providers_active = {'video':'Kivy',
                                 'audio':'Kivy',
                                 'stream':'Kivy'}
        self.providers = {
            'video':[
                ['Kivy', start_video_kivy],
                ['External', start_video_external],
                ['No video', start_video_no_video]
            ],
            'audio':[
                ['Kivy', start_audio_kivy],
                ['External', start_audio_kivy]
            ],
            'stream-audio':[
                ['Kivy', start_stream_kivy],
            ],
            'stream-video':[
                ['Kivy', start_stream_kivy],
            ]
        }

    def set_video_provider(self,value): self.providers_active['video'] = value
    def set_audio_provider(self,value):
        self.providers_active['audio'] = value
    def set_stream_provider(self,value): self.providers_active['stream'] = value
    def set_gui_update_callback(self,callback): self.gui_update = callback
    def set_modes(self,dictio): self.modes.update(dictio)
    def add_provider(self,mType,provider): self.providers[mType].append(provider)

    def start(self,place,seek=0):
        try:
            self.trying_seek = False
            place = int(place)
            self.playlist.set_current(place)
            ID, (name, path) = self.playlist.get_current()
            self.starting = True
            self.state = 'stop'
            self.paused = False
            self.pauseSupported = False
            if self.stream:
                self.stream = False
                try:
                    self.streamTimer.stop_thread(reason='Start media')
                except: pass
                self.streamTimer = None
            stream = False
            try: self.stop()
            except Exception as e:
                pass
            self.player = 'none'

            if len(name) > 10:
                if name[:7] == 'http://' or  name[:8] == 'https://':
                    self.player = 'stream-audio'
            if self.player == 'none':
                for x in '.wav','.mp3','.ogg','.m4a':
                   if name[-4:] == x: self.player = 'audio'
                for x in '.mp4','.mkv':
                   if name[-4:] == x: self.player = 'video'

            found = False
            for provider,callback in self.providers[self.player]:
                if self.providers_active[self.player] == provider:
                    found = True
                    self.mediaName = callback(self,place)
                    if self.gui_update:
                        kwargs = {'name': name, 'path:': path}
                        self.gui_update(**kwargs)
                    for x in self.modes['on_start']:
                        x()
                    if self.player in ('video', 'video2'):
                        for x in self.modes['on_video']:
                            x(self.sound)
                    self.starting = False
                    if seek:
                        self.seek(seek)
                    return self.mediaName
            if not found:
                self.sound = self.Dummy()
                self.starting = False
                return False
        except Exception as e:
            print e

    def on_stop(self,*arg):
        if not self.starting:
            if self.paused == False:
                self.pauseSeek = 0
                if self.modes['next_on_stop']:
                    self.next()

    def play(self,*arg):
        try:
            if self.player == 'video':
                self.sound.state = 'play'
            else:
                self.sound.play()
            Clock.schedule_once(self.resume, 0.2)
            self.state = 'play'
        except: pass

    def next(self,*arg):
        ID,(name,path) = self.playlist.get_next()
        self.start(str(ID))
        for x in self.modes['on_next']:
            x()

    def previous(self,*arg):
        ID,(name,path) = self.playlist.get_previous()
        name = self.start(str(ID))
        for x in self.modes['on_previous']:
            x()

    def seek(self,value):
        if self.paused: self.pauseSeek = int(value)
        else:
            if self.stream and platform == 'linux':
                self.streamTimer.seek(int(value),self.get_mediaDur())
            elif self.player in ('audio', 'video2'):
                self.sound.seek(int(value))
            elif self.player == 'video':
                val = float(value)
                getDur = float(self.get_mediaDur())
                fn = val/getDur
                self.sound.seek(fn)

    def resume(self,*arg):
        self.paused = False
        if self.pauseSupported == False:
            try: self.sound.seek(self.pauseSeek)
            except: pass
        self.state = 'play'

    def stop(self,*arg):
        if self.player in ('audio', 'video2') and self.sound:
            self.sound.stop()
            self.sound.unload()
        elif self.player == 'video' and self.sound:
            self.sound.state = 'stop'
            self.sound.source = ''
        self.state = 'stop'

    def pause(self,*arg):
        self.paused = True
        self.pauseSeek = self.get_mediaPos()
        if self.player in ('audio', 'video2'):
            self.sound.stop()
        elif self.player == 'video':
            self.sound.state = 'pause'

    def get_mediaPos(self,*arg):
        pos = 0
        if self.stream: pos = self.streamTimer.get_pos()
        elif self.player in ('audio', 'video2'):
            pos = int(self.sound.get_pos())
        elif self.player == 'video':
            pos = int(self.sound.position)
        return pos
    def get_mediaDur(self,*arg):
        dur = 0
        if self.player in ('audio', 'video2'):
            dur = int(self.sound.length)
            return dur
        elif self.player == 'video':
            dur = int(self.sound.duration)
            return dur

    def return_pos(self):
        if self.sound != None and self.player != 'external':
            seconds = self.get_mediaPos()
            soundlen = self.get_mediaDur()
            m, s = divmod(seconds, 60)
            m2, s2 = divmod(int(soundlen), 60)
            s = str(m).zfill(2)+':'+str(s).zfill(2)+'/'+str(m2).zfill(2)+':'+str(s2).zfill(2)
            # print s, (seconds, soundlen)
            return s, (seconds, soundlen)
