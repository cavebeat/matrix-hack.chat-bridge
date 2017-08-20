#!/usr/bin/env python3
# encoding: utf-8

'''
Created on 19 Aug 2017
@author: cave
https://github.com/cavebeat/matrix-hack.chat-bridge

License GPLv3
https://www.gnu.org/licenses/gpl-3.0.html
'''

import hackchat
import requests
import json
import config
import time


def send_matrix(message, sender):
    '''
    Post Message from hack.chat to matrix room
    https://matrix.org/docs/spec/client_server/r0.2.0.html#m-room-message
    m.room.message
    '''
    api_location = "/send/m.room.message"
    api_endpoint = "/_matrix/client/r0/rooms/"
    
    #Combine Hack.Chat user + Hack.Chat Message into payload
    user_message = sender + ":" + message
    payload = {"msgtype":"m.text", "body": user_message}
    url = config.api_matrix_server + api_endpoint + config.matrix_room_id_esc + api_location + '?access_token=' + config.api_token 
    u = requests.post(url, data=json.dumps(payload))    
    print u
    
def message_got(chat, message, sender):
    '''
    CallBack Function which gets triggered in the hackchat websocket listener thread 
    '''
    print message.lower()
    send_matrix(message.lower().encode('ascii','ignore'), sender)
    if "hello" in message.lower():
        chat.send_message("Hello there {}!".format(sender))

def get_matrix_message(prev_batch):
    '''
    receive single message since the prev_batch state in the timeline.
    https://matrix.org/docs/spec/client_server/r0.2.0.html#get-matrix-client-r0-rooms-roomid-messages
    GET /_matrix/client/r0/rooms/{roomId}/messages
    returns:
    message = ['chunk'][0]['content']['body'] => payload to forward to hack.chat server
    message type = ['chunk'][0]['content']['msgtype'] => forward only text 
    sender = ['chunk'][0]['sender'] => used to prevent echo
    end_batch = ['end'] => used to find out the end of the timeline
    '''
    api_location = "/_matrix/client/r0/rooms/"
    
    url = config.api_matrix_server + api_location + config.matrix_room_id + '/messages' + '?from=' + prev_batch + '&dir=f' + '&limit=1' + '&access_token=' + config.api_token  
    headers = {"Content-Type": "application/json"}
    u = requests.get(url, headers=headers)
    j = json.loads(u._content)    

    if not j['chunk']:
        #check if the last message is received
        return "", "", "", j['end'].encode('ascii','ignore')
    else:
        #return message, messagetype, sender and next_batch    
        return j['chunk'][0]['content']['body'], j['chunk'][0]['content']['msgtype'], j['chunk'][0]['sender'].encode('ascii','ignore'), j['end'].encode('ascii','ignore')    
    

def initial_sync():
    '''
    used to find a recent prev_batch
    https://matrix.org/docs/spec/client_server/r0.2.0.html#get-matrix-client-r0-sync
    GET /_matrix/client/r0/sync
    returns: 
    prev_batch     string     A token that can be supplied to to the from parameter of the rooms/{roomId}/messages endpoint
    '''
    api_location = "/_matrix/client/r0/sync"
    
    url = config.api_matrix_server + api_location + "?full_state=false" + "&set_presence=offline" + "&timeout=30000" + '&access_token=' + config.api_token  
    headers = {"Content-Type": "application/json"}
    u = requests.get(url, headers=headers)
    j = json.loads(u._content)
    return j['rooms']['join'][config.matrix_room_id]['timeline']['prev_batch'].encode('ascii','ignore')
    

if __name__ == '__main__':
    '''
    start the hack.chat websocket client into thread
    '''
    chat = hackchat.HackChat(config.hackchat_botname, config.hackchat_room, 1)
    chat.on_message += [message_got]    
    
    #find previous sync event from 
    prev_batch = initial_sync()
    
    run = 1
    #iterate all messages which have been posted since the sync event. 
    while run == 1:
        msg, type, user, next_batch = get_matrix_message(prev_batch)
        if type == 'm.text':
            print msg
        if prev_batch == next_batch:
            run = 0
        prev_batch = next_batch 

    run = 1
    
    #check every 1 sleep for a matrix message 
    while run == 1:
        msg, type, user, next_batch = get_matrix_message(prev_batch)
        if type == 'm.text':
            print msg
            #surpress echo if sender is receiver
            if user != config.matrix_user:
                chat.send_message(msg)
        prev_batch = next_batch 
        time.sleep(1) 

