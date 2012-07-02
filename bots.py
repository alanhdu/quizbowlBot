import os

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "quizBowl.settings")

#-------------------------------------------------------------------
from django.db import models
from engine.models import *
import random
# Create your models here.
class Bot():
    question = None

    def consider(self, text):
        pass
    def buzz(self, answer):
        print "Buzz! {0}".format(answer)

class RepeatBot(Bot):
    questionText = ""
    answer = None
    match = None

    def __init__(self, match):
        self.match = match

    def onStartQuestion(self):
        print "Starting question"
        self.questionText = "" 
        self.answer = None
    def onNewWord(self, word):
        self.questionText += " " + word
        print self.questionText

        if self.answer == None and Question.objects.filter(body__startswith=self.questionText).count() == 1:
            question = Question.objects.get(body__startswith=text)
            self.answer = random.choice(Answer.objects.filter(question=question))
        elif self.answer != None and len(self.questionText.split()) == self.answer.numWords:
            self.match.buzz()
            self.match.answer("", self.answer.body)

    def consider(self):
        if Question.objects.filter(body__startswith=self.questionText).count() == 1:
            question = Question.objects.get(body__startswith=text)
            self.answer = random.choice(Answer.objects.filter(question=question))

from BridgePython import Bridge
bridge = Bridge(api_key="60707403e0bf87e4")
match = bridge.get_service("match_22")
bot = RepeatBot(match)
match.addPlayer(bot)

bridge.connect()
