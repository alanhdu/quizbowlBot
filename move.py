import sqlite3

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
        except UnicodeEncodeError:
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

fout1 = open("labels.csv", "w")
fout2 = open("mapping.csv", "w")
conn1 = sqlite3.connect("questions.db")
c1 = conn1.cursor()

loadLabels(fout1, fout2, c1)
fout1.close()
fout2.close()
