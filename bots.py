from __future__ import division
import os

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "quizBowl.settings")

#-------------------------------------------------------------------
from nltk.probability import *
from django.db import models
from engine.models import *

from nltk.tokenize import word_tokenize, sent_tokenize
import os
import urllib
import re
from collections import defaultdict, Counter
from math import log, exp
import xml.dom.minidom
import StringIO
import random

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
    model = {}

    def onStartQuestion(self):
        for label in self.features:
            self.posterior[label] = 0
        self.questionText = ""

    def consider(self, word):
        maxGain = 0
        bestGuess = None

        for label in posterior:
            temp = 10 * exp(posterior[label]) - 5 * (1 - exp(posterior[label]))
            if temp > maxGain:
                bestGuess = label
                maxGain = temp

        if maxGain > 0:
            print bestGuess

    def onNewWord(self, word):
        # P(A|B) = P(B|A) * P(A) / P(B)
        # A is the label, B is the text given so far
        # Assuming every label is equally likely, on each word
        # you just need to update P(B|A) and P(B)
        # P(B and word) = P(B) * P(word)
        # P(B and word | A) = P(B|A) * P(word|A)

        for label in self.posterior:
            self.posterior[label] += log(self.features[label].prob(word))
            self.posterior[label] -= log(self.model.prob(word, []))

        self.consider()

    def train(self):
        docCount = FreqDist()
        for text in self.documents.itervalues():
            docCount.update(reduce(set.union,
                            (set(word_tokenize(re.sub(r"[^\w -]", "", sent)))
                             for sent in sent_tokenize(text))))

        print "Got doc count"


        for doc in self.documents:
            wordCount = FreqDist()
            for sent in sent_tokenize(self.documents[doc]):
                sent = re.sub(r"[^\w -]", "", sent)
                wordCount.update(word_tokenize(sent))

            for word in wordCount:
                tfidf = log(len(self.documents) / docCount[word])
                tfidf *= wordCount[word]
                if tfidf < 3:
                    del wordCount[word]

            self.features[doc] = SimpleGoodTuringProbDist(wordCount)
            print self.features[doc]
    def constructModel(self):
        counter = FreqDist()
        for question in Question.objects.filter(id__lt=1000):
            for sent in sent_tokenize(question.body):
                sent = re.sub(r"[^\w -]", "", sent).lower()
                counter.update(word_tokenize(sent))

        self.model = SimpleGoodTuringProbDist(counter)

    def loadDocuments(self):
        for document in os.listdir("wiki"):
            fin = open("wiki/{0}".format(document))
            self.documents[document] = fin.read().lower().strip()
            fin.close()

    def downloadDocuments(self):
        for i, label in enumerate(Label.objects.all()):
            title = "_".join( (s[0].upper() + s[1:].lower()
                               for s in label.body.split()))

            if os.path.exists("wiki/{0}".format(title)):
                continue

            title, text = self.getWikipedia(title)
            title.replace(" ", "_")

            if len(text) > 0:
                try:
                    fout = open("wiki/{0}".format(title), "w")
                except UnicodeEncodeError:
                    title = title.encode("utf-8")
                    fout = open("wiki/{0}".format(title), "w")
                fout.write(text.lower())
                fout.close()

            if i > 100:
                break

    def getWikipedia(self, title):
        url = u""
        try:
            url = u"http://en.wikipedia.org/w/index.php?action=raw&title={0}".format(title)
        except UnicodeDecodeError:
            title = title.decode('utf-8')
            url = u"http://en.wikipedia.org/w/index.php?action=raw&title={0}".format(title)

        text = urllib.urlopen(url.encode("utf-8")).read()

        if len(text) == 0:
            url = u"http://en.wikipedia.org/w/api.php?action=opensearch&search={0}".format(title)
            text = urllib.urlopen(url.encode("utf-8")).read()

            try:
                text = text.replace(r'\"', "''")
                newTitle = text.split(",[")[-1].split('"')[1]
                newTitle = eval('u"{0}"'.format(newTitle))
                newTitle = newTitle.strip('[]"').replace("\\", "")
                newTitle = newTitle.replace(" ", "_")
                newTitle = newTitle.replace("''", '"')

                return self.getWikipedia(newTitle)
            except IndexError:
                try:
                    url = u"http://en.wikipedia.org/w/api.php?action=query&list=search&srprop=timestamp&format=xml&srsearch={0}".format(title)
                    text = urllib.urlopen(url.encode("utf-8")).read()
                    doc = xml.dom.minidom.parse(StringIO.StringIO(text))

                    nodes = doc.getElementsByTagName("search")[0].childNodes
                    newTitle = nodes[0].getAttribute("title")

                    return self.getWikipedia(newTitle)
                except IndexError:
                    print title
                    return (title, "")

        if "#REDIRECT" in text:
            newTitle = text.split("]]")[0]
            newTitle = " ".join(newTitle.split()[1:]).translate(None, "[]")

            return self.getWikipedia(newTitle)

        elif "{{disambig" in text or "{{surname" in text:
            return (title, "")

        text = re.sub(r"==( )?See also( )?==(.|\n)*$", "", text)
        text = re.sub(r"==( )?Notes( )?==(.|\n)*$", "", text)
        text = re.sub(r"==( )?External Links( )?==(.|\n)*$", "", text)
        text = re.sub(r"==( )?References( )?==(.|\n)*$", "", text)
        text = re.sub(r"==.*==", "", text)

        text = re.sub(r"<!(.|\n)*?>", "", text) 
        text = re.sub(r"<.*?/>", "", text)
        text = re.sub(r"<.*?>(.|\n)*?</.*?>", "", text)

        text = re.sub(r"\[\[:Image.*?]]", "", text)
        text = re.sub(r"\[\[Image.*]]", "", text)

        text = re.sub(r"\[\[File.*]]", "", text)
        text = re.sub(r"\[\[File(.|\n)*?]]", "", text)

        text = re.sub(r"{{.*?}}", "", text)
        text = re.sub(r"{{(.|\n)*?}}", "", text)

        text = re.sub(r"\[\[[^\]]*?\|", "", text)

        text = text.replace("&nbsp;", " ")
        text = text.translate(None, "'[]")

        return (title, text.strip())

    def consider(self):
        newWord = self.questionText.split(" ")[-1]

        # Needs some form of smoothing
        for label in posterior:
            if newWord in self.features[label][newWord]:
                posterior[label] += self.features[label][newWord]



if __name__ == "__main__":
    bot = TrainedBot(None)
    bot.downloadDocuments()
    bot.constructModel()
    bot.loadDocuments()
    print "Loaded documents"
    bot.train()
    bot.onStartQuestion()
    bot.onNewWord("A")
    #print bot.getWikipedia("James_Sidney_Ensor")

"""
from BridgePython import Bridge
bridge = Bridge(api_key="60707403e0bf87e4")
match = bridge.get_service("match_22")
bot = RepeatBot(match)
match.addPlayer(bot)

bridge.connect()
"""
