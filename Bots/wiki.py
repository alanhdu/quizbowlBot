import re
import urllib
import unicodedata
import xml.dom.minidom
import sys
import os
# Take care of relative imports
_p, _name = os.path.split(sys.path[0])
sys.path.insert(0, _p)

# Allow Django imports
if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Database.quizBowl.importSettings")
from Database.engine.models import *

def getWikipedia(title):
    try:
        title = title.decode('utf-8')
    except UnicodeEncodeError:
        title = title.encode('utf-8')
        title = title.decode('utf-8')
    url = u"http://en.wikipedia.org/w/index.php?action=raw&title={0}".format(title)

    title = title.encode('utf-8')
    if os.path.exists("wiki/{0}".format(title)):
        return (title, "", 1)

    text = urllib.urlopen(url.encode("utf-8")).read()

    if len(text) == 0:
        title = title.decode('utf-8')
        url = u"http://en.wikipedia.org/w/api.php?action=opensearch&search={0}".format(title)
        text = urllib.urlopen(url.encode("utf-8")).read()

        text = text.replace(r'\"', "''")
        l = re.findall(r'".*?"', text)
        if len(l) > 1:
            newTitle = l[1].replace('"', "")
            newTitle = eval('u"""{0}"""'.format(newTitle))
            newTitle = newTitle.replace(" ", "_")
            newTitle = newTitle.replace("''", '"')

            return getWikipedia(newTitle)
        else:
            url = u"http://en.wikipedia.org/w/api.php?action=query&list=search&srprop=timestamp&format=xml&srsearch={0}".format(title)

            text = urllib.urlopen(url.encode("utf-8")).read()

            doc = xml.dom.minidom.parseString(text)

            suggestion = doc.getElementsByTagName("searchinfo")[0]
            if suggestion.hasAttribute("suggestion"):
                newTitle = suggestion.getAttribute("suggestion")

            else:
                nodes = doc.getElementsByTagName("search")[0].childNodes
                if len(nodes) > 0:
                    newTitle = nodes[0].getAttribute("title")
                else:
                    return (title, "", -1)

            return getWikipedia(newTitle)

    if "#REDIRECT" in text.upper():
        newTitle = re.findall("\[\[.*]]", text)[0]
        newTitle = newTitle.replace("[", "").replace("]", "")

        return getWikipedia(newTitle)

    else:
        l = ["{{disambig", "{{surname", "{{hndis", "{{geodis"]
        for search in l:
            if search in text:
                return (title, "", -1)

    text = re.sub(r"==( )?[Ss]ee [Aa]lso( )?==(.|\n)*$", "", text)
    text = re.sub(r"==( )?[Nn]otes( )?==(.|\n)*$", "", text)
    text = re.sub(r"==( )?[Ee]xternal [Ll]inks( )?==(.|\n)*$", "", text)
    text = re.sub(r"==( )?[Rr]eferences( )?==(.|\n)*$", "", text)
    text = re.sub(r"==.*==", "", text)

    text = re.sub(r"<!(.|\n)*?>", "", text) 
    text = re.sub(r"<.*?/>", "", text)
    text = re.sub(r"<.*?>(.|\n)*?</.*?>", "", text)

    text = re.sub(r"\[\[:Image.*?]]", "", text)
    text = re.sub(r"\[\[Image.*]]", "", text)

    text = re.sub(r"\[\[File.*]]", "", text)
    text = re.sub(r"\[\[File(.|\n)*?]]", "", text)

    text = re.sub(r"{{.*?}}", "", text)
    text = re.sub(r"{\|(.|\n)*?}", "", text)

    text = re.sub(r"\[\[[^\]]*?\|", "", text)
    text = re.sub(r"(\n)+", "\n", text)

    text = text.replace("&nbsp;", " ")
    text = text.translate(None, "[]")

    text = unicodeNormalize(text)

    return (title, text.strip(), 0)

def unicodeNormalize(text):
    text = unicode(str(text), "utf-8")
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore")

    return text

if __name__ == "__main__":
    ls = sorted(Label.objects.all(), key=lambda l: l.questions.count(), reverse=True)[:100]
    for l in ls:
        title, text, status = getWikipedia(l.body)
        title = unicodeNormalize(title)
        if status == 0:
            fout = open("../wiki/{0}".format(title.replace(" ", "_")), "w")
            fout.write(text)
            fout.close()
        print title, l.body
        l.body = title.replace("_", " ")
        l.save()
