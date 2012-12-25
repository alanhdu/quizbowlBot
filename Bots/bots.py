from __future__ import division
from nltk.probability import *
from math import log, exp
import utility
import random
from collections import defaultdict
import pickle
import os

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
    def loadDocuments(self):
        for label in os.listdir("../wiki"):
            fin = open("../wiki/{0}".format(label))
            label = label.replace("_", " ")
            self.documents[label] = fin.read().strip().lower()
            fin.close()

def getBot():
    f = open("pickledBot.data")
    features = pickle.load(f)
    f.close()

    bot = NaiveBayesBot(None)
    bot.features = features

    return bot

def allQuestions(bot):
    fout = open('a.txt', "w")
    correct = utility.Counter()
    incorrect = utility.Counter()
    for key in bot.features:
        label = Label.objects.get(body=key)
        #label = Label.objects.get(body="Clarinet")
        for question in label.questions.all():
            bot.onStartQuestion()
            correctAnswer = label.body

            for i, word in enumerate(question.body.split()):
                answer = bot.onNewWord(word)
                if correctAnswer == answer:
                    correct[i] += 1
                elif answer is not None:
                    incorrect[i] += 1
                    if i > 100:
                        print label.body, question.id
                        break

    for i in xrange(max(max(correct), max(incorrect))):
        s = "{0}, {1}, {2}\n".format(i, correct[i], incorrect[i])
        fout.write(s)

    fout.close()
