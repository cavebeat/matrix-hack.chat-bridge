#!/usr/bin/env python3
# encoding: utf-8

'''
@author: cave
https://github.com/cavebeat/matrix-hack.chat-bridge

License is from now on GPLv3 available at:  
https://github.com/cavebeat/matrix-hack.chat-bridge/blob/master/LICENSE
'''


'''
https://github.com/gkbrk/hackchat

Copyright (c) 2017 Gökberk Yaltirakli

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
'''

import json
import threading
import time
import websocket
import config

class HackChat:
    """A library to connect to https://hack.chat.

    <on_message> is <list> of callback functions to receive data from
    https://hack.chat. Add your callback functions to this attribute.
    e.g., on_message += [my_callback]
    The callback function should have 3 parameters, the first for the
    <HackChat> object, the second for the message someone sent and the
    third for the nickname of the sender of the message.
    """

    def __init__(self, nick, channel="programming", interval=1):
        """Connects to a channel on https://hack.chat.

        Keyword arguments:
        nick -- <str>; the nickname to use upon joining the channel
        channel -- <str>; the channel to connect to on https://hack.chat
        """
        self.nick = nick
        self.channel = channel
        self.online_users = []
        self.on_message = []
        self.on_join = []
        self.on_leave = []
        self.interval = interval
        self.ws = websocket.create_connection(config.hackchat_server)
        self._send_packet({"cmd": "join", "channel": channel, "nick": nick})
        threading.Thread(target = self._ping_thread).start()
        # added threading to the websocket listener too
        thread = threading.Thread(target=self.run, args=())
        thread.daemon = True                            # Daemonize thread
        thread.start()                                  # Start the execution


    def send_message(self, msg):
        """Sends a message on the channel."""
        self._send_packet({"cmd": "chat", "text": msg})

    def _send_packet(self, packet):
        """Sends <packet> (<dict>) to https://hack.chat."""
        encoded = json.dumps(packet)
        self.ws.send(encoded)

    def run(self):
#         """ Method that runs forever """
#         while True:
#             # Do something        
                    
        """Sends data to the callback functions."""
        while True:
            #print('Doing something imporant in the background')
            time.sleep(self.interval)
#            self.send_message("leetBot!")

            result = json.loads(self.ws.recv())
            if result["cmd"] == "chat" and not result["nick"] == self.nick:
                for handler in list(self.on_message):
                    handler(self, result["text"], result["nick"])
            elif result["cmd"] == "onlineAdd":
                self.online_users.append(result["nick"])
                for handler in list(self.on_join):
                    handler(self, result["nick"])
            elif result["cmd"] == "onlineRemove":
                self.online_users.remove(result["nick"])
                for handler in list(self.on_leave):
                    handler(self, result["nick"])
            elif result["cmd"] == "onlineSet":
                for nick in result["nicks"]:
                    self.online_users.append(nick)

    def _ping_thread(self):
        """Retains the websocket connection."""
        while self.ws.connected:
            self._send_packet({"cmd": "ping"})
            time.sleep(60)
