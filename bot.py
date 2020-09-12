#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import msnp
import time
import signal
import sys
import time
import ConfigParser


class MsnChatListener(msnp.ChatCallbacks):
    def friend_joined(self, passport_id, display_name):
        print '*** %s has joined a chat!' % passport_id
        spam[passport_id] = 1

    def friend_left(self, passport_id):
        print '*** %s has left the chat!' % passport_id
        del spam[passport_id]

    def message_received(self, passport_id, display_name, text, charset):
        print '*** We have a message (charset = %s) from %s: %s' % (
            charset, passport_id, text)
        if text.lower().startswith(".echo"):
            command = text.split(' ')
            if len(command) > 1:
                del command[0]
                self.chat.send_message(
                    "We have received your command on %s. It was '%s'" %
                    (ReturnLocalTime(), ' '.join(command)), charset)
            else:
                self.chat.send_message(
                    "We have received your command on %s but it was empty." %
                    (ReturnLocalTime()), charset)
        if passport_id in bot_admins:
            if text.lower().startswith(".die"):
                StopBot("Kill command from %s" % display_name)


class MSNPCallbackIM(msnp.SessionCallbacks):
    def state_changed(self, state):
        #print 'New state:', state
        if state == msnp.States.ONLINE:
            print "*** Connected ! Changing Display Name"
            im.change_display_name(display_name)

    def display_name_changed(self, display_name):
        print "** Our new display name is: %s" % display_name

    def ping(self):
        print "*** Received a ping from server."

    def chat_started(self, chat):
        callbacks = MsnChatListener()
        chat.callbacks = callbacks
        callbacks.chat = chat

    def friend_online(self, state, passport_id, display_name):
        print "*** Friend %s (%s) is ONLINE (%s)" % (display_name, passport_id,
                                                     state)
        friends_connected[passport_id] = passport_id

    def friend_offline(self, passport_id):
        print "*** Friend %s is OFFLINE" % passport_id
        del (friends_connected[passport_id])

    def logged_out(self):
        print "*** Logged out from server."


def ReturnLocalTime():
    return str(time.ctime(time.time()))


def OpenActiveChats():
    for this_chat in im.active_chats:
        if this_chat not in chats_session:
            chats_session[this_chat] = 0

        if chats_session[this_chat] < 1:
            print "*** Chat ID %s is active" % (this_chat)
            im.active_chats[this_chat].send_message(
                "Opening chat session ID %s" % this_chat, "utf-8")

        #if chats_session[this_chat] == 2:
        #    print "*** Chat ID %s is associated with %s "  % (this_chat,im.active_chats[this_chat].passport_id)

        chats_session[this_chat] += 1


def RunBot():
    im.dispatch_server = ('m1.escargot.log1p.xyz', 1863)
    im.login(login, password)

    cycle_count = 0
    session_to_close = list()

    while True:
        im.process(chats=True)

        if len(friends_connected) > 0:
            for victim in friends_connected:
                if victim not in spam:
                    im.start_chat(victim)
                    im.process()
                    #spam[victim] = 1

            if len(im.active_chats) > 0 and cycle_count > 10:
                OpenActiveChats()

        if len(session_to_close) > 0:
            for chatid in session_to_close:
                print '** Closing Chat ID %s' % chatid
                im.active_chats[chatid].leave()

        cycle_count += 1
        time.sleep(1)


def StopBot(shutdown_reason):
    print "!!! Exit requested (%s), disconnecting ..." % shutdown_reason
    im.change_display_name(display_name + " (AFK)")
    [
        chat_.send_message("Bot shutdown requested (%s)" % shutdown_reason,
                           "utf-8") for chat_ in im.active_chats.values()
    ]
    im.logout()
    sys.exit(0)


if __name__ == "__main__":
    im = msnp.Session(MSNPCallbackIM())

    spam = dict()
    friends_connected = dict()
    chats_session = dict()
    bot_admins = []

    config = ConfigParser.ConfigParser()
    try:
        config.readfp(open('bot.config'))
    except IOError:
        print "Please create a bot.config"
        sys.exit(1)

    login = config.get('account', 'login')
    password = config.get('account', 'pass')
    display_name = config.get('account', 'display_name')

    if len(config.items("admins")) > 0:
        for userid in config.items("admins"):
            bot_admins.append(userid[1])

    try:
        RunBot()
    except KeyboardInterrupt:
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        StopBot("KeyboardInterrupt")
