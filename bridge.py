import os
if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "quizBowl.settings")

from BridgePython import Bridge
from engine.signals import *
import threading
import time

class Scheduler(object):
    events = []
    t = None
    again = True

    def clear(self):
        events = []
    def addEvent(self, delay, func, args):
        self.events.append( (delay, func, args) )
    def run(self):
        self.again = True
        self.t = threading.Timer(0, self.helper)
        self.t.start()

    def helper(self):
        while self.again == True and len(self.events) > 0:
            head = self.events[0]
            del self.events[0]
            head[1](*head[2])

            time.sleep(head[0])

    def pause(self):
        self.t.cancel()
        self.again = False

s = Scheduler()

class Match(object):
    questionText = []
    pos = 0
    controller = None
    players = []
    goNext = True

    def addPlayer(self, player):
        self.players.append(player)

    def startMatch(self, controller, callback=None):
        if callback != None:
            callback.notify("Started!")

        self.controller = controller
        self.controller.startQuestion()


    def startQuestion(self, words, callback=None):
        goNext = False
        print "start question"
        self.questionText = words
        self.pos = 0

        for player in self.players:
            player.onStartQuestion()

        s.clear()

        for i in xrange(len(self.questionText)):
            s.addEvent(0.5, self.read, (callback,))
        s.run()

    def buzz(self, callback=None):
        s.pause()

        if callback != None:
            callback.onBuzz()

        for player in self.players:
            player.onBuzz()

    def correct(self, isCorrect):
        if isCorrect:
            goNext = True
            self.controller.startQuestion()
        else:
            s.run()

    def answer(self, answerText, callback=None):
        self.controller.onAnswer(None, self.pos, answerText)
        self.controller.isCorrect()

        if callback != None:
            callback.onAnswer("", answerText)

        for player in self.players:
            player.onAnswer("", answerText)

    def read(self, callback=None):
        for player in self.players:
            player.onNewWord(self.questionText[self.pos]);

        self.pos += 1

bridge = Bridge(api_key="60707403e0bf87e4")
bridge.publish_service("match_22", Match())
bridge.connect()
