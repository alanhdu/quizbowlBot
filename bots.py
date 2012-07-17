import os

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "quizBowl.settings")

#-------------------------------------------------------------------
from django.db import models
from engine.models import *
import random
# Create your models here.
class Bot():
    questionText = "" 
    match = None
    users = {}

    def __init__(self, match):
        self.match = match
    def onChat(self, user, message):
        pass
    def onSystemBroadcast(self, message):
        pass
    def onJoin(self, user):
        self.users[user] = None
    def onLeave(self, user):
        del self.users[user]
    def onStartQuestion(self):
        self.questionText = "" 
    def onBuzz(self, user):
        pass
    def onNewWord(self, word):
        self.questionText += word + " "
        self.consider()
    def consider(self):
        pass
    def onUpdateScore(self, scores):
        pass
    def onAnswer(self, user, answer):
        pass
    def onQuestionTimeout(self):
        pass
    def onFinish(self):
        pass
    def onSit(self, user, team):
        pass
    def onCompleteQuestion(self, question):
        pass

class RepeatBot(Bot):
    answer = None

    def onStartQuestion(self):
        self.questionText = "" 
        self.answer = None
    def consider(self):
        q = Question.objects.filter(body__contains=self.questionText)
        if self.answer == None and q.count() == 1:
            question = q.all()[0]
            answers = Answer.objects.filter(question=question)
            if (answers.count() > 0):
                self.answer = random.choice(answers)
                print "Got answer!", self.answer.body, self.answer.numWords
        elif self.answer != None:
            if len(self.questionText.split()) == self.answer.numWords:
                print "Buzzing"
                self.match.buzz()
                self.match.answer(self.answer.body)

from BridgePython import Bridge
bridge = Bridge(api_key="60707403e0bf87e4")
match = bridge.get_service("match_22")
bot = RepeatBot(match)
match.addPlayer(bot)

bridge.connect()
