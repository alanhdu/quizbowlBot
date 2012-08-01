import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "quizBowl.settings")

import re
import sqlite3

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

def loadQuestions(fout, c):
    l = []
    for row in c.execute("select question_id, body, category, author, tournament from questions"):
        try:
            l.append( "|".join((str(x).strip() for x in row)))
        except UnicodeEncodeError:
            print "Problem w/", row[0]
    fout.write("\n".join(l))

def loadLabels(fout1, fout2, c):
    l1 = []
    l2 = []
    i = 0
    j = 0

    mapping = {}

    for (aid, text) in c.execute("select answer_id, answer_text from cannonical_answer"):
        try:
            l1.append("|".join([str(aid), str(text)]))
        except UnicodeEncodeErrgeor:
            pass

        if aid > i:
            i = aid
            print i

    for (text, qid) in c.execute("select answer_text, question_id from answers where is_reference=1"):
        i += 1
        try:
            l1.append("|".join([str(i), str(text)]))
        except UnicodeEncodeError:
            pass

        if qid in mapping:
            mapping[qid].append(i)
        else:
            mapping[qid] = [i]


    for (qid, aid) in c.execute("select question_id, answer_id from question_mapping"):
        if qid in mapping:
            mapping[qid].append(aid)
        else:
            mapping[qid] = [aid]

    for qid in mapping:
        for aid in mapping[qid]:
            j += 1
            l2.append("|".join([str(j), str(aid), str(qid)]))

    fout1.write("\n".join(l1))
    fout2.write("\n".join(l2))

from engine.models import *
def cleanupLabels():
    i = 0
    labels = Label.objects.all().order_by("body")

    while i != labels.count():
        label = labels[i]
        
        if any(word[0].lower() == word[0] and (len(word) >= 3 or len(word) == 1)
                and word != "the"
                and word[0] not in "0123456789\""
               for word in label.body.split()):
            newBody = ""
            words = label.body.split()

            for (j, word) in enumerate(words):
                if j == 0:
                    newBody += word[0].upper() + word[1:] + " "
                else:
                    if "." in word or (len(word) < 3 and len(word) > 1) or word == "the":
                        newBody += word + " "
                    else:
                        newBody += word[0].upper() + word[1:] + " "

            newBody = newBody.strip()
            
            print "Capitalize", label.body, newBody
            label.body = newBody
            label.save()
        if "<" in label.body:
            label.body = re.sub("<.*>", "", label.body)
            label.save()
            print "Remove < >"
        if "{" in label.body:
            label.body = re.sub("{.*}", "", label.body)
            label.save()
            print "Remove { }"
        if label.body.strip() != label.body:
            print "strip", label.body,
            label.body = label.body.strip()
            label.save()
            print label.body

        temps = [Label.objects.filter(body=l.body)
                 for l in labels
                 if l.body.lower()[:5] == label.body.lower()[:5]
                 and stringDistance(l.body.lower(), label.body.lower()) < len(l.body) / 10 + 1
                 and "I" not in l.body
                 ]
        ls = []
        for temp in temps:
            for l in temp:
                ls.append(l)
        if len(ls) > 1:
            for l in ls:
                if "-" in l.body:
                    label = l
                if "'" in l.body:
                    label = l
                if "." in l.body:
                    label = l

            qids = []
            for l in ls:
                for q in label.questions.all():
                    qids.append(q.id)

            qids = list(set(qids))
            print label.body, qids, [l.body for l in ls], len(ls) - 1

            for l in ls:
                if l.id != label.id:
                    l.delete()

            for qid in qids:
                label.questions.add(Question.objects.get(id=qid))

            label.body = label.body.strip()
            label.save()

            labels = Label.objects.all()
        if len(label.questions.all()) == 0:
            print "No answer", label.body
            label.delete()
            labels = Label.objects.all()

        i += 1
        if i % 100 == 0:
            print i

if __name__ == "__main__":
    cleanupLabels()
