from __future__ import division
import os

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "quizBowl.settings")

#-------------------------------------------------------------------
from nltk.probability import *
from django.db import models
from engine.models import *

import unicodedata
from nltk.stem.porter import PorterStemmer
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
            self.posterior[label] = log(1 / len(self.features))
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

        temp = exp(self.posterior["Clarinet"])
        temp /= sum(exp(x) for x in self.posterior.itervalues())

        word = self.questionText.split()[-1]
        #print bestGuess, exp(self.posterior[bestGuess]), exp(self.posterior["Clarinet"]), self.features[bestGuess].prob(word), self.features["Clarinet"].prob(word)
        return bestGuess

    def onNewWord(self, word):
        # P(A|B) = P(B|A) * P(A) / P(B)
        # A is the label, B is the text given so far
        # Assuming every label is equally likely, on each word
        # you just need to update P(B|A) and P(B)
        # P(text and word) = P(text) * P(word)
        # P(B and word | A) = P(B|A) * P(word|A)

        word = re.sub(r"[^\w -]", "", word).lower()
        self.questionText += " " + word
        #print word,

        for label in self.posterior:
            self.posterior[label] += log(self.features[label].prob(word))
            self.posterior[label] += 10          #Prevents probalities from going to 0

        return self.consider()


    def train(self):
        # Maybe some stemming later?
        docCount = FreqDist()
        self.model = FreqDist()

        for text in self.documents.itervalues():
            words = reduce(list.__add__, 
                          (word_tokenize(re.sub(r"[^\w '-]", "", sent))
                          for sent in sent_tokenize(text)))
            docCount.update(set(words))
        print "Got doc count"

        for doc in self.documents:
            wordCount = FreqDist()
            for sent in sent_tokenize(self.documents[doc]):
                sent = re.sub(r"[^\w '-]", "", sent)
                wordCount.update(word_tokenize(sent)) 

            for word in wordCount:
                if docCount[word] / len(self.documents) > 0.5:
                    wordCount[word] = 0
                    wordCount.pop(word)
                else:
                    tfidf = log(len(self.documents) / docCount[word])
                    tfidf *= wordCount[word]
                    if tfidf < 3:
                        wordCount[word] = 0
                        wordCount.pop(word)

            self.model += wordCount
            self.features[doc] = wordCount

        for label in self.features:
            t = self.features[label]
            self.features[label] = WittenBellProbDist(t, self.model.B())
        print "Trained Wikipedia"

        for question in Question.objects.filter(id__lt=1000):
            for sent in sent_tokenize(question.body):
                sent = re.sub(r"[^\w '-]", "", sent).lower()
                self.model.update(word_tokenize(sent))
        print "Got Questions"

        self.model = WittenBellProbDist(self.model, self.model.B() + 1)
        print "Finised Model"

    def loadDocuments(self):
        for document in os.listdir("wiki"):
            fin = open("wiki/{0}".format(document))
            self.documents[document] = fin.read().lower().strip()
            fin.close()

    def downloadDocuments(self):
        for i, label in enumerate(Label.objects.all()):
            title = "_".join( (s[0].upper() + s[1:].lower()
                               for s in label.body.split()))
            title, text = self.getWikipedia(title)
            title = unicode(title.replace(" ", "_"), "utf-8")

            if len(text) > 0 and len(title) > 0:
                title = unicodedata.normalize("NFKD", title)
                title = title.encode('ascii', 'ignore')
                try:
                    fout = open("wiki/{0}".format(title), "w")
                except UnicodeEncodeError:
                    title = title.encode("utf-8")
                    fout = open("wiki/{0}".format(title), "w")
                fout.write(text.lower())
                fout.close()

                label.body = title
                label.save()

            if i > 120:
                break

    def getWikipedia(self, title):
        try:
            title = title.decode('utf-8')
        except UnicodeEncodeError:
            title = title.encode('utf-8')
            title = title.decode('utf-8')
        url = u"http://en.wikipedia.org/w/index.php?action=raw&title={0}".format(title)

        title = title.encode('utf-8')
        if os.path.exists("wiki/{0}".format(title)):
            return ("", "")

        if title.startswith("List_of_"):
            return ("", "")


        text = urllib.urlopen(url.encode("utf-8")).read()

        if len(text) == 0:
            title = title.decode('utf-8')
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

        if "#REDIRECT" in text.upper():
            newTitle = text.split("]]")[0]
            newTitle = " ".join(newTitle.split()[1:]).translate(None, "[]")

            return self.getWikipedia(newTitle)

        else:
            l = ["{{disambig", "surname", "hndis", "geodis"]
            for search in l:
                if search in text:
                    return (title, "")

        text = re.sub(r"==( )?[Ss]ee [Aa]lso( )?==(.|\n)*$", "", text)
        text = re.sub(r"==( )?[Nn]otes( )?==(.|\n)*$", "", text)
        text = re.sub(r"==( )?[Ee]xternal [Ll]inks( )?==(.|\n)*$", "", text)
        text = re.sub(r"==( )?[Rr]eferences( )?==(.|\n)*$", "", text)
        text = re.sub(r"==.*==", "", text)

        text = re.sub(r"<!(.|\n)*?>", "", text) 
        text = re.sub(r"<.*?/>", "", text)
        text = re.sub(r"<.*?>(.|\n)*?</.*?>", "", text)

        text = re.sub(r"\[\[:Image.*?]]", "", text)
        text = re.sub(r"\[\[Image.*]]", "", text)

        text = re.sub(r"\[\[File.*]]", "", text)
        text = re.sub(r"\[\[File(.|\n)*?]]", "", text)

        text = re.sub(r"{{.*?}}", "", text)
        text = re.sub(r"{\|(.|\n)*?}", "", text)

        text = re.sub(r"\[\[[^\]]*?\|", "", text)
        text = re.sub(r"(\n)+", "\n", text)

        text = text.replace("&nbsp;", " ")
        text = text.translate(None, "'[]")

        return (title, text.strip())


def getBot():
    bot = TrainedBot(None)
    bot.loadDocuments()
    bot.train()
    return bot

if __name__ == "__main__":
    bot = TrainedBot(None)
    #bot.downloadDocuments()
    bot.loadDocuments()
    bot.train()


    fout = open('a.txt', "w")
    for key in bot.features:
        ls = Label.objects.filter(body=key)
        #print key
        label = ls[0]
        if len(ls) > 1:
            qids = []
            for l in ls[1:]:
                qids += [q.id for q in l.questions.all()]
            for l in ls[1:]:
                l.delete()

            for qid in qids:
                label.questions.add(Question.objects.get(id=qid))

        #label = Label.objects.get(body="Clarinet")
        print >>fout, label.body
        for question in label.questions.all():
            print >>fout, "Question:", len(question.body.split())
            bot.onStartQuestion()

            prevTime = -2

            for i, word in enumerate(question.body.split()):
                answer = bot.onNewWord(word)

                if answer == label.body:
                    #if i > prevTime + 1:
                    #    print >>fout
                    prevTime = i
                    print >>fout, i,

            print >>fout 
        print >>fout

    fout.close()

    """
    l = Label.objects.get(body__startswith=u"Piet\xe0_")
    q = l.questions.get()

    bot.onStartQuestion()
    for word in q.body.split():
        bot.onNewWord(word)
    """
