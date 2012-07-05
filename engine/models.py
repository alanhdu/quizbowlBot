from django.db import models
from django.contrib.auth.models import User

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

class UserProfile(models.Model):
    user = models.OneToOneField(User, related_name="profile")
    def get_absolute_url(self):
        return "/player/{0}".format(self.user.username)

class Question(models.Model):
    body = models.TextField()
    category = models.TextField()
    author = models.TextField()
    tournament = models.TextField()

class Answer(models.Model):
    user = models.ForeignKey(User, null=True)
    question = models.ForeignKey(Question, related_name="answers")
    body = models.TextField()
    isCorrect = models.BooleanField()
    numWords = models.IntegerField()

    def correct(self):
        self.body = self.body.strip()
        texts = [correctAnswer.body
                 for correctAnswer in self.question.correctAnswers.all()]

        distances =[stringDistance(body, self.body)
                    for body in texts]
        lengths = [len(body)
                   for body in texts]

        if min(distances) < min(3, min(lengths)):
            self.isCorrect = True
        else:
            self.isCorrect = False

        self.save()

class CorrectAnswer(models.Model):
    question = models.ForeignKey(Question, related_name="correctAnswers")
    body = models.TextField()
