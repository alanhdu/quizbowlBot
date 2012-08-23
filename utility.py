from __future__ import division

import os
import re
import urllib
import xml.dom.minidom
import unicodedata
import collections
import StringIO
import itertools
from collections import defaultdict
from nltk.tokenize import word_tokenize, sent_tokenize, PunktWordTokenizer
from nltk.probability import *
from nltk.util import ingrams
import nltk.model
from math import log, exp
from engine.models import *

class CondProbDist(ConditionalProbDistI):
    def __init__(self, cfdist, probdistFactory, *args, **kwargs):
        l = lambda: probdistFactory(FreqDist(), *args, **kwargs)
        collections.defaultdict.__init__(self, l) 
        for condition in cfdist:
            self[condition] = probdistFactory(cfdist[condition], *args, **kwargs)
        

class NGramModel(nltk.model.NgramModel):
    def __init__(self, n):
        self._n = n
        self._lpad = ()
        self._rpad = ()
        self._ngrams = set()
        self._backoff = None

    @classmethod
    def fromWords(cls, n, trainingText, estimator, docCount, numDoc):
        model = cls(n)

        if n > 1:
            model._backoff = NGramModel.fromWords(n-1, trainingText, estimator,
                                                  docCount, numDoc)
        else:
            model._backoff = None

        cfd = ConditionalFreqDist()
        ngrams = ngramFinder(trainingText, n)

        unigrams = [a for a, in model.getUnigram()._ngrams]
        for ngram in ngrams:
            include = docCount[n][ngram] / numDoc < 0.8 / 4**(n-1)
            if n > 1:
                include = include and any(word in unigrams for word in ngram)
            if include:
                context = tuple(ngram[:-1])
                token = ngram[-1]
                cfd[context].inc(token)

        for context in cfd.conditions():
            wordFilter(docCount[n], numDoc, cfd[context], context)

        for ngram in set(ngrams):
            context = tuple(ngram[:-1])
            token = ngram[-1]
            if token in cfd[context]:
                model._ngrams.add(ngram)

        model._model = CondProbDist(cfd, estimator, docCount[n].B())

        return model

    @classmethod
    def fromCondFreq(cls, n, condFreq, estimator, bins):
        model = cls(n)
        model._model = CondProbDist(condFreq, estimator, bins)
        model._backoff = None
        model._ngrams = set(model._model[()].freqdist().samples())

        return model
    
    def getUnigram(self):
        t = self
        while t._n > 1:
            t = t._backoff
        return t
    
    def prob(self, word, context):
        if self._n > 1:
            context = tuple(context[1-self._n:])
        else:
            context = ()

        if self._backoff is None:
            return 0.5 * self[context].prob(word)
        else:
            prob = self[context].prob(word) + self._backoff.prob(word, context)
            return prob * 0.5

    def addBackoff(self, freq, estimator, bins):
        t = self

        while t._backoff != None:
            t = t._backoff

        condFreq = ConditionalFreqDist()
        condFreq[()] = freq

        t._backoff = NGramModel.fromCondFreq(1, condFreq, estimator, bins)

    def __repr__(self):
        return "<NGramModel with %d %d-grams>" % (len(self._ngrams), self._n)

def wordFilter(docCount, numDoc, freqdist, context=None, tfidfLimit=0.3):
    for word in freqdist.samples():
        if context:
            tfidf = log(numDoc / docCount[context + (word, )])
        else:
            tfidf = log(numDoc / docCount[word])
        tfidf *= freqdist[word]

        if tfidf < tfidfLimit:
            freqdist[word] = 1
            freqdist.pop(word)

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

def unicodeNormalize(text):
    text = unicode(str(text), "utf-8")
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore")

    return text

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

def getWikipedia(title):
    try:
        title = title.decode('utf-8')
    except UnicodeEncodeError:
        title = title.encode('utf-8')
        title = title.decode('utf-8')
    url = u"http://en.wikipedia.org/w/index.php?action=raw&title={0}".format(title)

    title = title.encode('utf-8')
    if os.path.exists("wiki/{0}".format(title)):
        return (title, "", 1)

    text = urllib.urlopen(url.encode("utf-8")).read()

    if len(text) == 0:
        title = title.decode('utf-8')
        url = u"http://en.wikipedia.org/w/api.php?action=opensearch&search={0}".format(title)
        text = urllib.urlopen(url.encode("utf-8")).read()

        text = text.replace(r'\"', "''")
        l = re.findall(r'".*?"', text)
        if len(l) > 1:
            newTitle = l[1].replace('"', "")
            newTitle = eval('u"""{0}"""'.format(newTitle))
            newTitle = newTitle.replace(" ", "_")
            newTitle = newTitle.replace("''", '"')

            return getWikipedia(newTitle)
        else:
            url = u"http://en.wikipedia.org/w/api.php?action=query&list=search&srprop=timestamp&format=xml&srsearch={0}".format(title)

            text = urllib.urlopen(url.encode("utf-8")).read()

            doc = xml.dom.minidom.parseString(text)

            suggestion = doc.getElementsByTagName("searchinfo")[0]
            if suggestion.hasAttribute("suggestion"):
                newTitle = suggestion.getAttribute("suggestion")

            else:
                nodes = doc.getElementsByTagName("search")[0].childNodes
                if len(nodes) > 0:
                    newTitle = nodes[0].getAttribute("title")
                else:
                    return (title, "", -1)

            return getWikipedia(newTitle)

    if "#REDIRECT" in text.upper():
        newTitle = re.findall("\[\[.*]]", text)[0]
        newTitle = newTitle.replace("[", "").replace("]", "")

        return getWikipedia(newTitle)

    else:
        l = ["{{disambig", "{{surname", "{{hndis", "{{geodis"]
        for search in l:
            if search in text:
                return (title, "", -1)

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
    text = text.translate(None, "[]")

    text = unicodeNormalize(text)

    return (title, text.strip(), 0)

def combine(ls):
    if len(ls) > 0:
        qids = []

        for l in ls:
            qids += [q.id for q in l.questions.all()]

        for qid in qids:
            ls[0].questions.add(Question.objects.get(id=qid))

        for l in ls[1:]:
            l.delete()
        return ls[0]
    else:
        return ()


if __name__ == "__main__":
    (title, text) = getWikipedia("admiral carpet")
    print unicodeNormalize(title)
