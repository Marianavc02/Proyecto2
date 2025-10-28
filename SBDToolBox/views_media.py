from django.conf import settings
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.static import serve as static_serve


@xframe_options_exempt
def serve_media_noframeblock(request, path):
    return static_serve(request, path, document_root=settings.MEDIA_ROOT)
