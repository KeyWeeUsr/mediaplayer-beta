from media_player import Media_Player
from media_player import Playlist
from kivy.clock import Clock
from time import sleep
import traceback

def dd(*arg,**kwarg):
    text = arg
    print text

class Playlist_Client(Playlist):
        def __init__(self,osc_sender):
            super(Playlist_Client, self).__init__()
            self.osc_sender = osc_sender
            self.mstring = 'audioCL:'

        def add(self,name,path):
            super(Playlist_Client, self).add(name,path)
            self.osc_sender(self.mstring+'addPlaylist:'+name+':'+path)

        def reset(self):
            super(Playlist_Client, self).reset()
            self.osc_sender(self.mstring+'resetPlaylist:')


class OSC_Media_Interface(object):
    def __init__(self,place,osc_sender):
        self.mstring = 'audioCL:'
        self.osc_sender = osc_sender
        self.pos = 0
        self.length = 0
        self.kwargs = {'on_stop': None}
        self.state = 'play'
        self.osc_sender(self.mstring+'Load:'+str(place))

    def play(self):
        self.osc_sender(self.mstring+'Play:')

    def pause(self):
        self.osc_sender(self.mstring+'Pause:')

    def stop(self):
        self.osc_sender(self.mstring+'Stop:')

    def unload(self):
        self.osc_sender(self.mstring+'Stop:')

    def seek(self,value):
        self.osc_sender(self.mstring+'Seek:'+str(value))

    def get_pos(self):
        return self.pos

    def length(self):
        return self.length

    def bind(self,**kwargs):
        self.kwargs.update()


class Media_Player_Client(Media_Player):
    def __init__(self):
        super(Media_Player_Client, self).__init__()
        self.osc_sender = None
        self.oscPlayer = False
        self.add_provider('audio',['Kivy-Server',start_audio_kivy_server])
        self.mstring = 'audioCL:'

    def set_osc_sender(self,value):
        self.osc_sender = value
        self.playlist = Playlist_Client(value)

    def osc_callback(self,message):
        try:
            msg = message.split(':')
            # dd(msg)
            # print '[OSC-RECV]', msg
            if self.oscPlayer:
                # print msg
                if msg[0] == 'return_pos' and not self.paused:
                    self.sound.pos = msg[2]
                    self.sound.length = msg[3]
                elif msg[0] == 'update_media':
                    ID, name, path = msg[1], msg[2], msg[3]
                    self.playlist.set_current(msg[1])
                    if self.gui_update:
                        kwargs = {'name': msg[2], 'path': msg[3]}
                        self.gui_update(**kwargs)
            if msg[0] == 'start_video':
                self.oscPlayer = False
                self.start(msg[1],seek=msg[4])
        except Exception as e:
            dd(e)

    def start(self,place,seek=0):
        try:
            seek = int(seek)
            self.oscPlayer = False
            name = super(Media_Player_Client, self).start(place)
            if self.oscPlayer == False and seek:
                Clock.schedule_once(lambda x: self.try_seeking(seek), 1)
            return name
        except Exception as e:
            dd(e)

    def try_seeking(self,value):
        if self.return_pos()[1][0] < int(value)-3:
            self.seek(value)
            Clock.schedule_once(lambda x: self.try_seeking(value), 1)

    def background_switch(self,*arg):
        try:
            if self.sound.state == 'play' and self.oscPlayer == False:
                ID, (name, path) =  self.playlist.get_current()
                seektime = self.return_pos()[1][0]
                string = self.mstring+'background_switch:'+'%s:%s:%s:%s' % (ID, name, path, seektime)
                self.osc_sender(string)
                self.stop()
        except Exception as e:
            dd(e)

    def pause(self):
        if self.oscPlayer:
            self.paused = True
            self.osc_sender(self.mstring+'Pause:')
        else:
            super(Media_Player_Client, self).pause()

def start_audio_kivy_server(self,place):
    ID, (name, path) = self.playlist.get_current()
    self.sound = OSC_Media_Interface(place,self.osc_sender)
    self.sound.play()
    self.oscPlayer = True
    self.sound.bind(on_stop= self.on_stop())
    return name
