from bots import Bot
import utility

class DecisionTreeBot(Bot):
    tree = None
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
        allFeatures = [feature for feature in allFeatures
                       if docCount[feature] / paragraphCounter < 0.4
                       and docCount[feature] > 2]
        print len(allFeatures)
        self.tree = BoolDecisionTree(trainingData, allFeatures)

class BoolDecisionTree():
   feature, left, right, plurality = None, None, None, None
   def __init__(self, trainingData, allFeatures):
       """trainingData -- [(label,features), ...]
          features should be a dict with keys of the feature and values of a bool

          allFeatures -- list of features
       """
       c = Counter(x[0] for x in trainingData)
       self.plurality = len(c) > 0 and max(c, key=c.get) or None
       if len(allFeatures) != 0 and calcEntropy(c) > 0:
           bestFeature = [None, float("inf"), [], []]
           for feature in allFeatures:
               trueBranch, falseBranch = [], []
               for label, features in trainingData:
                   if features[feature]:
                       trueBranch.append((label, features))
                   else:
                       falseBranch.append((label, features))
   
               newEntropy = len(trueBranch) * calcEntropy(x[0] for x in trueBranch)
               newEntropy += len(falseBranch) * calcEntropy(x[0] for x in falseBranch)

               if newEntropy < bestFeature[1]:
                   bestFeature = [feature, newEntropy, trueBranch, falseBranch]
   
           temp = [feature for feature in allFeatures
                   if feature != bestFeature[0]]
   
           self.feature = bestFeature[0]
           self.true = BoolDecisionTree(bestFeature[2], [t for t in temp])
           self.false = BoolDecisionTree(bestFeature[3], temp)
       else:
           self.feature, self.true, self.false = None, None, None
   def classify(self, features):
       if self.feature == None:
           return self.plurality
       else:
           if features[self.feature]:
               return self.true.classify(features)
           else:
               return self.false.classify(features)

   def __repr__(self):
       s = ""
       if self.true != None:
           s += "\n".join("\t" + x for x in repr(self.true).split("\n")) + "\n"
       s += str(self.feature) + ", " + str(self.plurality)
       if self.false != None:
           s += "\n" + "\n".join("\t" + x for x in repr(self.false).split("\n"))
       return s

def calcEntropy(iterator):
    c = Counter(iterator)
    entropy = 0
    length = c.total()
    for obj in c:
        prob = c[obj] / length
        entropy -= prob * log(prob, 2)

    return entropy
