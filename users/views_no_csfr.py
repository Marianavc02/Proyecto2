from django.views.decorators.csrf import csrf_exempt
from allauth.socialaccount.providers.microsoft.provider import MicrosoftOAuth2Adapter

from allauth.socialaccount.providers.oauth2.views import OAuth2LoginView, OAuth2CallbackView


@csrf_exempt
class MicrosoftCallbackView(OAuth2CallbackView):
   adapter_class = MicrosoftOAuth2Adapter
