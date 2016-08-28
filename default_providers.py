from kivy.core.audio import SoundLoader
from kivy.uix.videoplayer import VideoPlayer
from threading import Thread
from time import sleep
from kivy.utils import platform
import traceback

class VideoPlayer_modified(VideoPlayer):
    def __init__(self, **kwargs):
        super(VideoPlayer_modified, self).__init__(**kwargs)
        self.modified_stop_callback = None

    def on_state(self, instance, value):
        super(VideoPlayer_modified, self).on_state(instance, value)
        if value == 'stop' and self.modified_stop_callback:
            self.modified_stop_callback()

    def bind(self, **kwargs):
        super(VideoPlayer_modified, self).bind(**kwargs)
        if 'on_stop' in kwargs:
            self.modified_stop_callback = kwargs['on_stop']

def start_audio_kivy(self,place):
    ID, (name, path) = self.playlist.get_current()
    self.sound = SoundLoader.load(path)
    if self.sound:
        self.sound.play()
        self.sound.bind(on_stop= self.on_stop)
        return name

def start_audio_external(self,place):
    ID, (name, path) = self.playlist.get_current()
    self.player = 'external'
    android_fileExt_activity("audio/*",path+name)
    return 'External player'

def start_video_kivy(self,place):
    ID, (name, path) = self.playlist.get_current()
    self.pauseSupported = True
    self.sound = VideoPlayer_modified(source=path, state='play', options={'allow_stretch': True})
    self.sound.bind(on_stop= self.on_stop)
    return name

def start_video_external(self,place):
    ID, (name, path) = self.playlist.get_current()
    self.player = 'external'
    android_fileExt_activity("video/*",path)
    return 'External player'

def start_video_no_video(self,place):
    ID, (name, path) = self.playlist.get_current()
    self.sound = VideoPlayer(source=path, state='play', options={'allow_stretch': True})
    return name

def start_android_audio(self,place):
    ID, (name, path) = self.playlist.get_current()
    self.player = 'audio'
    self.sound = Android_Native_Player()
    self.sound.load(path)
    self.sound.play()
    self.sound.bind(on_stop= self.on_stop)
    self.stream = False
    self.pauseSupported = True
    return name

def start_android_video(self,place):
    ID, (name, path) = self.playlist.get_current()
    self.player = 'video2'
    self.sound = Android_Native_Player()
    self.sound.load(path)
    self.sound.play()
    self.sound.bind(on_stop= self.on_stop)
    self.stream = False
    self.pauseSupported = True
    return name

def start_stream_kivy(self,place):
    ID, (name, path) = self.playlist.get_current()
    if platform == 'linux':
        import testplayer
        class Gst_Stream_Timer:
            def __init__(self,parent,player):
                self.parent,self.player,self.looping = parent,player,True
                Thread(target=self.start_thread).start()
                # Window.bind(on_close=self.stop_thread)

            def get_pos(self):
                return self.pos

            def stop_thread(self,*arg,**kwarg):
                kwarg.setdefault('reason','n/a')
                self.looping = False
                if kwarg['reason'] == 'error': Logger.info('GstStreamTimer: Player crashed.')
                else: Logger.info('GstStreamTimer: Thread was stopped.')
                self.stream = False

            def seek(self,pos,length):
                self.player.seek(int(pos))
                self.startTime = self.curTime - pos

            def start_thread(self):
                self.startTime,self.pos  = time(),0
                while self.looping:
                    if self.player == self.parent.sound and self.player.length != -1:
                        self.curTime = time()
                        self.pos = int(self.curTime - self.startTime)
                        sleep(1)
                    else:
                        if self.player.length == -1: self.stop_thread(reason='error')
                        else: self.stop_thread()

        self.sound = testplayer.SoundGstplayer()
        self.player = 'audio'
        self.sound.source = path
        self.sound.load()
        self.sound.play()
        self.streamTimer = Gst_Stream_Timer(self,self.sound)
        self.sound.bind(on_stop= self.on_stop())
        self.stream = stream
        return name
    elif platform == 'android':
        if self.providers['stream'] == 'Kivy':
            start_android_audio(self,path,'',stream=True)
            return name
        else:
            self.player = 'external'
            android_fileExt_activity("video/*",path)
            return 'External player'
