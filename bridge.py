from BridgePython import Bridge
import utilities
from bots import *

bridge = Bridge(api_key="c44bcbad333664b9")

class Handler():
    self.bots
    def createBot(self, roomName, team):
        self.bots[roomName] = bots.getBot()

        def getMatch(match):
            self.bots[roomName].match = match

        multi = bridge.get_service("quizbowl-multiplayer")
        multi.joinRoom(roomName, self.bots[roomName], getMatch)

bridge.publish_service("quizbowl-bot", Handler())
bridge.connect()
