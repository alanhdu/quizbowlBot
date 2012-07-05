from django.contrib.auth import authenticate
from django import forms
from engine.models import *

class PlayerForm(forms.Form):
    username = forms.CharField(max_length=30)
    password = forms.CharField(widget=forms.PasswordInput)

    firstName = forms.CharField(max_length=30, required=False)
    lastName = forms.CharField(max_length=30, required=False)
    email = forms.EmailField()

class loginForm(forms.Form):
    username = forms.CharField(max_length=30)
    password = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super(loginForm, self).clean()
        username = cleaned_data.get("username")
        password = cleaned_data.get("password")

        if username and password:
            user = authenticate(username=username, password=password)
            if user is None:
                raise forms.ValidationError("Username and password aren't correct")
                
        return cleaned_data
