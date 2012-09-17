from __future__ import division
import os

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "quizBowl.settings")

#-------------------------------------------------------------------
from nltk.probability import *
from engine.models import *
from utility import NGramModel
from math import log, exp
import utility
import random
from collections import defaultdict
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
        for document in os.listdir("wiki"):
            fin = open("wiki/{0}".format(document))
            self.documents[document] = fin.read().strip().lower()
            fin.close()
    def downloadDocuments(self):
        labels = sorted(Label.objects.all(), lambda x: x.questions.count())
        for i, label in enumerate(labels):
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

            if i > 100:
                break

class NaiveBayesBot(Bot):
    features = {} 
    documents = {}
    posterior = {}

    def onStartQuestion(self):
        for label in self.features:
            self.posterior[label] = 0
        self.questionText = []

    def onNewWord(self, word):
        word = utility.wordNormalize(word)
        self.questionText.append(word)
        context = self.questionText[:-1]

        bestGuess = None 
        for label in self.posterior:
            self.posterior[label] += log(self.features[label].prob(word, context))
            self.posterior[label] += 7          #Prevents probalities from going to 0

            if bestGuess == None:
                bestGuess = label
            elif self.posterior[label] > self.posterior[bestGuess]:
                bestGuess = label

        normProb = exp(self.posterior[bestGuess])
        normProb /= sum(exp(x) for x in self.posterior.itervalues())

        if normProb * len(self.questionText) / 100 > 0.5:
            match.buzz(bestGuess)
            return bestGuess
        else:
            return None

    def train(self):
        # Maybe some stemming later?
        docCount = {1:utility.Counter(), 2:utility.Counter()}

        for text in self.documents.itervalues():
            docCount[1].update(set(utility.wordParse(text)))
            docCount[2].update(set(utility.ngramFinder(text, 2)))
        print "Got doc count"

        categoryCount = utility.Counter()
        categoryWords = defaultdict(list)
        for q in Question.objects.all()[::100]:
            words = utility.wordParse(q.body)

            categoryWords[q.category] += words
            categoryWords[""] += words

        categoryBins = len(set(categoryWords[""]))
        del categoryWords[""]

        for category in categoryWords:
            categoryCount.update(set(categoryWords[category]))

        for category, words in categoryWords.items():
            categoryWords[category] = utility.Counter(words)
            utility.wordFilter(categoryCount, len(categoryWords), 
                               categoryWords[category])
        print "Trained Category"

        for label in self.documents:
            self.features[label] = NGramModel(2, self.documents[label],
                                              docCount, len(self.documents))
            category = Label.objects.get(body=label).questions.all()[0].category
            self.features[label].addBackoff(categoryWords[category],
                                            categoryBins)
        print "Trained Wikipedia"

class DecisionTreeBot(Bot):
    pass

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


if __name__ == "__main__":
    #bot = getBot()
    
    bot = NaiveBayesBot(None)
    bot.loadDocuments()
    bot.train()

    f = open("pickledBot.data", "w")
    pickle.dump(bot.features, f)
    f.close()

    #allQuestions(bot)
