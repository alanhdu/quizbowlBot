from __future__ import division

import re
import urllib
import xml.dom.minidom
import unicodedata
from nltk.tokenize import sent_tokenize, PunktWordTokenizer
from nltk.probability import *
from math import log
from engine.models import *
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

class WordDist(dict):
    freq = None
    _n = None
    _b = None
    bins = None
    def __init__(self, collection=None, bins = None):
        self.freq = collections.defaultdict(int)
        if collection is not None:
            for i in collection:
                self[i] += 1
            self._n = len(collection)
        else:
            self._n = 0

        self._b = len(self.freq)
        self.bins = bins
    def update(self, collection):
        for i in collection:
            self[i] += 1
        self._n += len(collection)
        self._b = len(self.freq)
    def pop(self, item):
        self._n -= self[item]
        del self[item]
    def prob(self, token):
        if token in self:
            return self[token] / (self._n + self._b)
        else:
            return self._b / ((self.bins - self._b) * (self._n + self._b))
    def __getitem__(self, token):
        return self.freq[token]

class NGramModel():
    model = None 
    n = 0

    def __init__(self, n, text, docCount, numDoc):
        self.n = n
        self.model = []

        unigrams = WordDist(wordParse(text))
        wordFilter(docCount[1], numDoc, unigrams)

        for i in xrange(n, 1, -1):
            ngrams = ngramFinder(text, i)
            cwd = collections.defaultdict(functools.partial(WordDist, None, len(docCount[i])))

            for ngram in ngrams:
                rare = docCount[i][ngram] / numDoc < 0.8 / 4**(i-1)
                important = any(word in unigrams for word in ngram)
                if rare and important:
                    context = tuple(ngram[:-1])
                    token = ngram[-1]
                    cwd[context][token] += 1

            for context in cwd.keys():
                wordFilter(docCount[n], numDoc, cwd[context], context)

            self.model.append(cwd)

        cwd = collections.defaultdict(functools.partial(WordDist, None, len(docCount[1])))
        cwd[()] = unigrams
        self.model.append(cwd)

    def prob(self, word, context):
        prob = None
        for model in self.model[::-1]:
            if prob is None:
                prob = 0.5 * model[context].prob(word)
            else:
                prob = 0.5 * prob + model[context].prob(word)
        return prob

    def addBackoff(self, freq, bins):
        condFreq = collections.defaultdict(functools.partial(WordDist, None, bins))
        condFreq[()] = freq
        self.model.append(condFreq)

    def __repr__(self):
        return "<NGramModel with %d-grams>" % (self.n)

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
