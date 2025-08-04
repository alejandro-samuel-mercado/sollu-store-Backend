from django.http import JsonResponse

class BloquearAccesoDesdeNavegadorMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if "text/html" in request.META.get("HTTP_ACCEPT", ""):
            return JsonResponse({"error": "No tienes permiso para acceder a esta API desde el navegador."}, status=403)
        return self.get_response(request)
