from __future__ import division
from bots import Bot
import utility
from collections import defaultdict, Counter
import functools
from math import log, exp

import os
import sys
_p, _name = os.path.split(sys.path[0])
sys.path.insert(0, _p)

# Allow Django imports
if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Database.quizBowl.importSettings")
from Database.engine.models import *

def getBot():
    bot = NaiveBayesBot(None)
    bot.loadDocuments()
    bot.train()
    bot.onStartQuestion()
    return bot

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

        bestGuess = self.posterior.keys()[0]
        for label in self.posterior:
            self.posterior[label] += log(self.features[label].prob(word, context))
            self.posterior[label] += 7          #Prevents probalities from going to 0

            if self.posterior[label] > self.posterior[bestGuess]:
                bestGuess = label

        normProb = exp(self.posterior[bestGuess])
        normProb /= sum(exp(x) for x in self.posterior.itervalues())

        print bestGuess, normProb

        if normProb * len(self.questionText) / 100 > 0.5:
            match.buzz(bestGuess)
            return bestGuess
        else:
            return None

    def train(self):
        # Maybe some stemming later?
        docCount = {1:utility.Counter(), 2:utility.Counter()}

        for text in self.documents.itervalues():
            docCount[1].update(set(utility.ngramFinder(text, 1)))
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
            categoryCount.update((word,) for word in set(categoryWords[category]))

        for category, words in categoryWords.items():
            categoryWords[category] = WordDist(words, categoryBins)
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

        return categoryCount

class WordDist():
    freq = None
    _n = None
    _b = None
    def __init__(self, collection=None, bins=None):
        self.freq = utility.Counter(collection)
        self._n = (collection is not None) and len(collection) or 0
        self._b = max(bins, len(self.freq))
    def update(self, collection):
        self.freq.update(collection)
        self._n += len(collection)
        self._b = max(len(self.freq), self._b)
    def add(self, token):
        self.freq[token] += 1
        self._n += 1
        self._b = max(len(self.freq), self._b)
    def pop(self, item):
        self._n -= self[item]
        del self.freq[item]
    def prob(self, token):
        return (1 + self.freq[token]) / (self._n + self._b)
    def __getitem__(self, token):
        return self.freq[token]
    def __str__(self):
        return "WordDist w/ n={0}, b={1}".format(self._n, self._b)
    def __repr__(self):
        return str(self)

class NGramModel():
    model = None 
    n = 0

    def __init__(self, n, text, docCount, numDoc):
        self.n = n
        self.model = []

        for i in xrange(1, n + 1):
            ngrams = utility.ngramFinder(text, i)
            cwd = defaultdict(functools.partial(WordDist, None, len(docCount[i])))

            for ngram in ngrams:
                context = tuple(ngram[:-1])
                token = ngram[-1]
                cwd[context].add(token)

            for context in cwd.keys():
                utility.wordFilter(docCount[i], numDoc, cwd[context], context)

            self.model.append(cwd)

    def prob(self, word, context):
        prob = 0
        for (n, model) in enumerate(self.model):
            c = tuple(context[-n-1:-1])
            prob = 0.5 * prob + model[c].prob(word)
        return prob

    def addBackoff(self, freq, bins):
        condFreq = defaultdict(functools.partial(WordDist, None, bins))
        condFreq[()] = freq
        self.model.insert(0, condFreq)

    def __repr__(self):
        return "<NGramModel with %d-grams>" % (self.n)


if __name__ == "__main__":
    bot = NaiveBayesBot(None)
    bot.loadDocuments()
    bot.train()
    pass
