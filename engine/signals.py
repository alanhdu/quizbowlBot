from django.core.signals import request_started
from django.dispatch import receiver, Signal
from django.shortcuts import redirect
from BridgePython import Bridge
from engine.models import *
import engine.views
import random
import threading

matchStarted = Signal(providing_args = [])

class Thread(threading.Thread):
    def __init__(self, func):
        threading.Thread.__init__(self)
        self.func = func
    def run(self):
        self.func()

def getBridge():
    return Bridge(api_key = "60707403e0bf87e4")

def bridgeConnect(bridge):
    t = Thread(bridge.connect)
    t.start()
    t.join(0.25)

class Controller(object):
    question = None
    answer = None
    
    def startQuestion(self):
        bridge = getBridge()
        match = bridge.get_service("match_22")
        self.question = random.choice(Question.objects.all())
        q = self.question.body.split()
        print q
        match.startQuestion(q)

        bridgeConnect(bridge)
        questionStarted.send(sender=self)

    def onAnswer(self, user, pos, answerText):
        self.answer = Answer.objects.create(body=answerText, user=None, numWords=pos, question=self.question)
        self.answer.correct()


    def isCorrect(self):
        print self.answer.isCorrect, self.answer.body
        return self.answer.isCorrect


class CallBack(object):
    def notify(self, message):
        print message

@receiver(matchStarted)
def startMatch(sender, **kwargs):
    bridge = getBridge()
    c = Controller()
    match = bridge.get_service("match_22")

    match.startMatch(c, CallBack())
    bridgeConnect(bridge)
