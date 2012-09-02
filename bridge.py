import os
if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "quizBowl.settings")

from BridgePython import Bridge
import utility
import bots

bridge = Bridge(api_key="c44bcbad333664b9")

class Handler():
    bots = {}
    def createBot(self, roomName, team):
        print roomName, team
        self.bots[roomName] = bots.TrainedBot(None)

        def getMatch(match):
            self.bots[roomName].match = match

        multi = bridge.get_service("quizbowl-multiplayer")
        multi.joinRoom(roomName, self.bots[roomName], getMatch)

if __name__ == "__main__":
    bridge.publish_service("quizbowl-bot", Handler())
    bridge.connect()
