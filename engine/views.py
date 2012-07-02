from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.views.decorators.csrf import csrf_exempt
from django.core.context_processors import csrf
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from engine.models import *
from engine.forms import *
from engine.signals import *
import engine.views
import random as r


def play(request):
    matchStarted.send(sender=request)
    return render_to_response("play.html", 
            {"user":request.user})

def questionDetail(request, question_id):
    q = get_object_or_404(Question, pk=question_id)
    return render_to_response("questionDetail.html", 
            {"user":request.user, "q":q})

def playQuestion(request, question_id):
    q = get_object_or_404(Question, pk=question_id)
    return render_to_response("playQuestion.html",
            {"user":request.user, "q":q})

@csrf_exempt
def random(request):
    if request.method == "POST":
        data = request.POST
        q = Question.objects.get(pk=int(data[u"qid"]))
        a = Answer.objects.create(question=q, body=data[u"answer"],
                                  numWords=int(data[u"buzzTime"]), 
                                  isCorrect=False) 
        if (request.user.is_authenticated()):
            a.user = request.user
            a.save()

        a.correct()

    return redirect(engine.views.playQuestion, question_id=r.randint(0, 10000))

def createPlayer(request):
    if request.method == "POST":
        form = PlayerForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            u = User.objects.create(username=data["username"], 
                                    first_name=data["firstName"],
                                    last_name=data["lastName"],
                                    email=data["email"])
            u.set_password(data["password"])
            u.save()

            for s in ("username", "firstName", "lastName", "password", "email"):
                del data[s]
            data["user"] = u

            UserProfile.objects.create(**data)
            return redirect(engine.views.playerLogin)
    else:
        form = PlayerForm()

    c = {"user":request.user, "form":form}
    c.update(csrf(request))

    return render_to_response("createPlayer.html", c)

def playerDetail(request, username):
    u = get_object_or_404(User, username=username)
    profile = UserProfile.objects.get(user=u)

    return render_to_response("playerDetail.html", 
            {"user":request.user, "player":profile})

def playerLogin(request):
    if request.method == "POST":
        form = loginForm(request.POST)
        
        if form.is_valid():
            data = form.cleaned_data
            user = authenticate(username=data["username"], 
                                password=data["password"])
            login(request, user)
            return HttpResponseRedirect(user.profile.get_absolute_url())
    else:
        form = loginForm()

    c = {"form":form}
    c.update(csrf(request))

    return render_to_response("login.html", c)

def playerLogout(request):
    logout(request)
    return redirect("engine.views.playerLogin")
