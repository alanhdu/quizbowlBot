from BridgePython import Bridge
import Queue
import threading
import time

class Scheduler(object):
    events = Queue.Queue()
    t = None
    again = True

    def clear(self):
        while not self.events.empty():
            self.events.get()
    def addEvent(self, delay, func, args):
        self.events.put( (delay, func, args) )
    def run(self):
        self.again = True

        self.t = threading.Timer(0, self.helper)
        self.t.start()

    def helper(self):
        if self.again and not self.events.empty():
            head = self.events.get()
            head[1](*head[2])

            self.t = threading.Timer(head[0], self.helper)
            self.t.start()

    def pause(self):
        self.t.cancel()
        self.again = False

s = Scheduler()

class Match(object):
    questionText = []
    pos = 0
    controller = None
    players = []
    isAsking = False

    def addPlayer(self, player):
        self.players.append(player)
        print "Added player"

    def connect(self, controller, callback=None):
        self.controller = controller
    def startMatch(self):
        self.controller.startQuestion() 
        # gets a random question and calls self.startQuestion() with it

    def startQuestion(self, words, callback=None):
        if self.isAsking == False:
            self.isAsking = True
            self.questionText = words
            self.pos = 0

            for player in self.players:
                player.onStartQuestion()

            s.clear()

            for i in xrange(len(self.questionText)):
                s.addEvent(0.5, self.read, (callback,))
            s.run()

    def buzz(self, callback=None):
        s.pause()

        if callback != None:
            callback.onBuzz("")

        for player in self.players:
            player.onBuzz("")

    def correct(self, isCorrect):
        if isCorrect:
            self.isAsking = False
            self.controller.startQuestion()
        else:
            s.run()

    def answer(self, answerText, callback=None):
        self.controller.onAnswer(None, self.pos, answerText) # enters answer into django database
        self.controller.isCorrect() # calls self.correct()

        if callback != None:
            callback.onAnswer("", answerText)

        for player in self.players:
            player.onAnswer("", answerText)

    def read(self, callback=None):
        print self.questionText[self.pos]
        for player in self.players:
            player.onNewWord(self.questionText[self.pos]);
        self.pos += 1

bridge = Bridge(api_key="60707403e0bf87e4")
bridge.publish_service("match_22", Match())
bridge.connect()
