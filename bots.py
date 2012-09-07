from __future__ import division
import os

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "quizBowl.settings")

#-------------------------------------------------------------------
from nltk.probability import *
from django.db import models
from engine.models import *
from nltk.util import ingrams

from nltk.tokenize import word_tokenize, sent_tokenize
from utility import NGramModel
from math import log, exp
import os
import utility
import random
import collections
import pickle

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
        if self.answer != None:
            if len(self.questionText.split()) == self.answer.numWords:
                print "Buzzing"
                self.match.buzz()
                self.match.answer(self.answer.body)
        else:
            q = Question.objects.filter(body__contains=self.questionText)

            if self.answer == None and q.count() == 1:
                answers = Answer.objects.filter(question=q[0])
                if (answers.count() > 0):
                    self.answer = random.choice(answers)
                    print "Got answer!", self.answer.body, self.answer.numWords

class TrainedBot(Bot):
    features = {} 
    documents = {}
    posterior = {}

    def onStartQuestion(self):
        for label in self.features:
            self.posterior[label] = 0
        self.questionText = ""

    def consider(self):
        bestGuess = None 

        for label in self.posterior:
            if bestGuess == None:
                bestGuess = label
            elif self.posterior[label] > self.posterior[bestGuess]:
                bestGuess = label

        normProb = exp(self.posterior[bestGuess])
        normProb /= sum(exp(x) for x in self.posterior.itervalues())

        context = self.questionText.split()[:-1]
        word = self.questionText.split()[-1]

        #correct = Question.objects.get(id=279).label.body
        #print word, bestGuess, normProb, self.features[bestGuess].prob(word, context),
        #print self.features[correct].prob(word, context), exp(self.posterior[bestGuess]), exp(self.posterior[correct])

        #if normProb * len(words) / 100 > 0.5:
        return bestGuess
        #else:
        #    return None

    def onNewWord(self, word):
        # P(A|B) = P(B|A) * P(A) / P(B)
        # A is the label, B is the text given so far
        # Assuming every label is equally likely, on each word
        # you just need to update P(B|A) and P(B)
        # P(text and word) = P(text) * P(word)
        # P(B and word | A) = P(B|A) * P(word|A)

        word = utility.wordNormalize(word)
        self.questionText += " " + word
        context = self.questionText.split()[:-1]

        for label in self.posterior:
            self.posterior[label] += log(self.features[label].prob(word, context))
            self.posterior[label] += 7          #Prevents probalities from going to 0

        return self.consider()

    def train(self):
        # Maybe some stemming later?
        docCount = {1:collections.Counter(), 2:collections.Counter()}

        for text in self.documents.itervalues():
            docCount[1].update(set(utility.wordParse(text)))
            docCount[2].update(set(utility.ngramFinder(text, 2)))
        print "Got doc count"

        categoryCount = collections.Counter()
        categoryWords = collections.defaultdict(list)
        for q in Question.objects.filter(id__lt=1000).iterator():
            words = utility.wordParse(q.body)

            categoryWords[q.category] += words
            categoryWords[""] += words

        categoryBins = len(set(categoryWords[""]))
        del categoryWords[""]

        for category in categoryWords:
            categoryCount.update(set(categoryWords[category]))

        for category, words in categoryWords.items():
            categoryWords[category] = collections.Counter(words)
            utility.wordFilter(categoryCount, len(categoryWords), 
                               categoryWords[category])
        print "Trained Category"

        for label in self.documents:
            self.features[label] = NGramModel(2, self.documents[label],
                                              docCount, len(self.documents))
            l = Label.objects.get(body=label)
            #self.features[label].addBackoff(categoryWords[l.category],
            #                                categoryBins)
        print "Trained Wikipedia"

    def loadDocuments(self):
        for document in os.listdir("wiki"):
            fin = open("wiki/{0}".format(document))
            self.documents[document] = fin.read().strip().lower()
            fin.close()

    def downloadDocuments(self):
        for i, label in enumerate(Label.objects.all()):
            title, text, status = utility.getWikipedia(label.body)
            title = utility.unicodeNormalize(title).replace(" ", "_")

            if status == 0:
                fout = open("wiki/{0}".format(title), "w")
                fout.write(text.lower())
                fout.close()

                label.body = title
                label.save()
            elif status == 1:
                label.body = title
                label.save()

                utility.combine(Label.objects.filter(body=title))
            else:
                print label.body

            if i > 110:
                break

def getBot():
    f = open("pickledBot.data")
    features = pickle.load(f)
    f.close()

    bot = TrainedBot(None)
    bot.features = features

    return bot

def allQuestions(bot):
    fout = open('a.txt', "w")
    correct = collections.Counter()
    incorrect = collections.Counter()
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


if __name__ == "__main__":
    #bot = getBot()
    
    bot = TrainedBot(None)  # 3.8 million
    bot.loadDocuments()
    bot.train()
    """

    f = open("pickledBot.data", "w")
    pickle.dump(bot.features, f)
    f.close()
    """

    #allQuestions(bot)

    """
    q = Question.objects.get(id=279)
    l = q.label

    print q.body, l.body

    bot.onStartQuestion()
    for word in q.body.split():
        bot.onNewWord(word)
    """
