import sqlite3

def loadQuestions(fout, c):
    l = []
    for row in c.execute("select question_id, body, category, author, tournament from questions"):
        try:
            l.append( "|".join((str(x).strip() for x in row)))
        except UnicodeEncodeError:
            print "Problem w/", row[0]
    fout.write("\n".join(l))

def loadCorrectAnswers(fout, c):
    l = []
    i = 0

    mapping = {}
    for (qid, aid) in c.execute("select * from question_mapping"):
        if aid in mapping:
            mapping[aid].append(qid)
        else:
            mapping[aid] = [qid]

    for (aid, text) in c.execute("select answer_id, answer_text from cannonical_answer"):
        for qid in mapping[aid]:
            try:
                l.append("|".join([str(i), str(qid), str(text)]))
                i += 1
            except UnicodeEncodeError:
                pass

    for (qid, text) in c.execute("select question_id, answer_text from answers where is_reference=1"):
        try:
            l.append("|".join([str(i), str(qid), str(text)]))
            i += 1
        except UnicodeEncodeError:
            pass

    fout.write("\n".join(l))

fout = open("correctAnswers.csv", "w")
conn1 = sqlite3.connect("questions.db")
c1 = conn1.cursor()

loadCorrectAnswers(fout, c1)
fout.close()
