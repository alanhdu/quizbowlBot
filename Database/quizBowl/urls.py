from django.conf.urls import patterns, include, url
import engine.views

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    url(r"^play/$", engine.views.play),

    url(r"^login/$", engine.views.playerLogin),
    url(r"^logout/$", engine.views.playerLogout),
    url(r"^createPlayer/$", engine.views.createPlayer),
    url(r"^player/(?P<username>[A-Za-z0-9+_.@]{1,30})/$", engine.views.playerDetail),

    url(r"^questions/(?P<question_id>\d+)/$", engine.views.questionDetail),
    url(r"^questions/play/(?P<question_id>\d+)/$", engine.views.playQuestion),
    url(r"^questions/play/$", engine.views.random),
)
