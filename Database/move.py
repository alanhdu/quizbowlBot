import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "quizBowl.settings")

from engine.models import *
import string
import re
import sqlite3
import utility

def loadQuestions(fout, c):
    l = []
    mapping = {}
    for qid, aid in c.execute("select question_id, answer_id from question_mapping"):
        mapping[qid] = aid

    for row in c.execute("select question_id, body, category from questions"):
        try:
            r = list(row)
            r.append(mapping[row[0]])

            l.append( "|".join(utility.unicodeNormalize(str(x).strip()) for x in r))
        except KeyError:
            pass

    fout.write("\n".join(l))

def loadLabels(fout, c):
    l1 = []
    for (aid, text) in c.execute("select answer_id, answer_text from cannonical_answer"):
        try:
            l1.append("|".join([str(aid), str(text)]))
        except UnicodeEncodeError:
            l1.append("|".join([str(aid).encode('utf-8'),
                                str(text).encode('utf-8')]))
    fout.write("\n".join(l1))

def cleanupLabels():
    i = 0
    labels = Label.objects.order_by("body")

    for label in labels:
        if any(word[0] in string.ascii_lowercase 
                and (len(word) >= 3 or len(word) == 1) and word != "the"
               for word in label.body.split()):
            newBody = ""
            words = label.body.split()

            for (j, word) in enumerate(words):
                if j == 0:
                    newBody += word[0].upper() + word[1:] + " "
                else:
                    if (len(word) < 3 and len(word) > 1) or word == "the":
                        newBody += word + " "
                    else:
                        newBody += word[0].upper() + word[1:] + " "

            newBody = newBody.strip()
            
            print "Capitalize", label.body, newBody
            label.body = newBody
            label.save()
        if label.body.strip() != label.body:
            print "strip", label.body,
            label.body = label.body.strip()
            label.save()
            print label.body

def filterLabels():
    labels = Label.objects.order_by("body")
    i = 0
    while i < labels.count():
        label = labels[i]

        if label.questions.count() == 0:
            print "No answer", label.body
            label.delete()
            i -= 1
            labels = Label.objects.order_by("body")
        else:
            temps = [list(Label.objects.filter(body=l.body))
                     for l in labels
                     if l.body.lower()[:5] == label.body.lower()[:5]
                     and stringDistance(l.body.lower(), label.body.lower()) < len(l.body) / 10 + 1
                     and l.body.lower()[-1] not in "ivx"]
            temps.append(list(Label.objects.filter(body__iexact=label.body)))

            ls = list(set(reduce(list.__add__, temps)))
            if len(ls) > 1:
                print label.body, len(ls), "Removed duplicates"
                label = utility.combine(list(set(ls)))
                i -= 1
                labels = Label.objects.order_by("body")

        i += 1
def cleanCategory():
    i = 0
    fix = {"Astronomy"                   : "Science -- Astronomy",
           "Biology"                     : "Science -- Biology",
           "Chemistry"                   : "Science -- Chemistry",
           "Earth Science"               : "Science -- Earth Science",
           "Physics"                     : "Science -- Physics",
           "Mathematics"                 : "Science -- Mathematics",
           "Literature -- Language Arts" : "Literature",
           "Fine Arts -- Other"          : "Fine Arts",
           "Other -- Other"              : "Other"}
    for question in Question.objects.filter(category__in=fix):
        question.category = fix[question.category]
        question.save()

def combine(ls):
    qs = []
    for l in ls:
        qs += l.questions.all()

    l = ls[0]
    ls = ls[1:]
    for q in qs:
        l.questions.add(q)
    l.save()

    for l in ls:
        l.delete()

if __name__ == "__main__":
    #cleanCategory()
    #cleanupLabels()
    filterLabels()
