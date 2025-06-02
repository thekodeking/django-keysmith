from django import forms

from keysmith.models import APIToken


class APITokenForm(forms.ModelForm):
    class Meta:
        model = APIToken
        fields = ['name', 'description', 'token_type', 'user', 'scopes', 'expires_at']
