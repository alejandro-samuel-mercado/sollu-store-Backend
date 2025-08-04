from rest_framework.permissions import BasePermission

class SoloLecturaUsuario(BasePermission):
    """
    Permiso personalizado para permitir solo lectura a los usuarios no administradores.
    """
    def has_permission(self, request, view):
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        return False