from __future__ import division
from bots import Bot
from math import log, exp, sqrt
from collections import defaultdict
import utility
import Queue

def getBot():
    bot = DecisionTreeBot(None)
    bot.loadDocuments()
    bot.train()

class DecisionTreeBot(Bot):
    tree = None
    documents = {}
    def train(self):
        trainingData, allFeatures, docCount = [], set(), utility.Counter()
        paragraphCounter = 0

        for label, text in self.documents.items():
            for paragraph in text.split("\n"):
                d = defaultdict(bool)
                words = set(utility.wordParse(paragraph))
                docCount.update(words)
                paragraphCounter += 1
                for word in words:
                    d[word] = True
                    allFeatures.add(word)
                trainingData.append((label, d))
        print len(allFeatures)
        self.tree = BoolDecisionTree(trainingData, allFeatures)

class Node():
    feature, true, false, plurality = None, None, None, None
    def __init__(self, feature=None, plurality=None, true=None, false=None,):
        self.feature = feature
        self.true = true
        self.false = false
        self.plurality = plurality
    def __repr__(self):
        s = ""
        if self.true is not None:
            s += "\n".join("\t" + x for x in repr(self.true).split("\n"))
        if self.feature is not None:
            s += "\n" + str(self.feature) + "\n"
        else:
            s += str(self.plurality)
        if self.false is not None:
            s += "\n".join("\t" + x for x in repr(self.false).split("\n"))
        return s

class BoolDecisionTree():
    root = None
    def __init__(self, trainingData, allFeatures):
        """trainingData -- [(label,features), ...]
           features should be a dict with keys of the feature and values of a bool
 
           allFeatures -- list of features
        """
        self.root = Node()
        q = Queue.Queue()
        q.put( (trainingData, allFeatures, self.root) )
        while not q.empty():
            trainingData, allFeatures, node = q.get()

            labelCounter = utility.Counter()
            truthCounter = defaultdict(utility.Counter)
            falseCounter = defaultdict(utility.Counter)
            for label, features in trainingData:
                for feature, value in features.iteritems():
                    if value:
                        truthCounter[feature][label] += 1
                labelCounter[label] += 1

            for feature in truthCounter:
                for label in labelCounter:
                    falseCounter[feature][label] = labelCounter[label] - truthCounter[feature][label]

            node.plurality = len(labelCounter) > 0 and \
                             max(labelCounter, key=labelCounter.get) or None

            if len(labelCounter) > 1:
                bestFeature = (None, float("inf")) #feature, entropy, trueBranch, falseBranch
                for feature in allFeatures:
                    gini = goodness(truthCounter[feature], falseCounter[feature])

                    if gini < bestFeature[1]:
                        bestFeature = (feature, gini)
   
                remaining = [feature for feature in allFeatures
                              if feature != bestFeature[0]]
                trueBranch, falseBranch = [], []
                for label, features in trainingData:
                    if features[bestFeature[0]]:
                        trueBranch.append((label, features))
                    else:
                        falseBranch.append((label, features))
   
                node.feature, node.true, node.false = bestFeature[0], Node(), Node()
                q.put( (trueBranch, [t for t in remaining], node.true) )
                q.put( (falseBranch, remaining, node.false) )

    def classify(self, features):
        node = self.root
        while (node.feature != None):
            if features[node.feature]:
                node = node.true
            else:
                node = node.false
        return node.plurality
    def __repr__(self):
        return repr(self.root)

def calcEntropy(iterator):
    c = utility.Counter(iterator)
    entropy = 0
    try:
        length = len(iterator)
    except TypeError:
        length = c.total()
    for count in c.values():
        prob = count / length
        entropy -= prob * log(prob, 2)

    return entropy

def goodness(counter1, counter2):
    s1, s2, s3, s4 = 0, 0, 0, 0
    size1, size2 = 0, 0
    for k in counter1.values():
        size1 += 1
        s1 += k
        s2 += k**2
    if s1 == 0:
        return float('inf')
    for k in counter2.values():
        size2 += 1
        s3 += k
        s4 += k**2
    if s2 == 0:
        return float('inf')
    return size1 * (1 - s2 / (s1*s1)) + size2 * (1 - s4 / (s3*s3))

def calcGini(iterator):
    c = utility.Counter(iterator)
    try:
        length = len(iterator)
    except TypeError:
        length = c.total()
    gini = 1 - sum((count/length) ** 2 for count in c.itervalues())
    return gini

if __name__ == "__main__":
    getBot()
