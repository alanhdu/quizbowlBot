from __future__ import division

import re
import urllib
import xml.dom.minidom
import unicodedata
from nltk.tokenize import sent_tokenize, PunktWordTokenizer
from nltk.probability import *
from math import log
import functools
import collections

class Counter(dict):
    def __init__(self, iterator=None):
        if iterator != None:
            for obj in iterator:
                self[obj] += 1
    def __getitem__(self, key):
        if key in self:
            return self.get(key)
        else:
            self[key] = 0
            return self.get(key)
    def update(self, iterator):
        for obj in iterator:
            self[obj] += 1

def wordFilter(docCount, numDoc, worddist, context=None, tfidfLimit=0.3):
    for word in worddist.keys():
        if context:
            tfidf = log(numDoc / docCount[context + (word, )])
        else:
            tfidf = log(numDoc / docCount[word])
        tfidf *= worddist[word]

        if tfidf < tfidfLimit:
            worddist.pop(word)

_wordNormalize = re.compile(r"[^\w -]*")
def wordNormalize(word):
    return _wordNormalize.sub("", word).lower()

_word_tokenize = PunktWordTokenizer().tokenize
def wordParse(text):
    words = [wordNormalize(word) for word in _word_tokenize(text)]
    return [word for word in words if word]

def ngramFinder(text, n):
    ngrams = []
    sents = sent_tokenize(text)

    for sent in sents:
        words = wordParse(sent)

        ngrams += []
        for i in xrange(len(words) - (n - 1)):
            ngrams.append(tuple(words[i:i+n]))
    return ngrams


def stringDistance(a, b):
    a = " " + a
    b = " " + b
    distance = [ [0 for x in b] for y in a]

    for i in xrange(len(a)):
        distance[i][0] = i
    for j in xrange(len(b)):
        distance[0][j] = j

    for j in xrange(1, len(b)):
        for i in xrange(1, len(a)):
            if a[i] == b[j]:
                distance[i][j] = distance[i - 1][j - 1]
            else:
                distance[i][j] = min(distance[i - 1][j] + 1,
                                     distance[i][j - 1] + 1,
                                     distance[i - 1][j - 1] + 1)
    return distance[-1][-1]

if __name__ == "__main__":
    pass
