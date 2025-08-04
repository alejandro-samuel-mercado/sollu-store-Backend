from productos.api.common import *
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from productos.models.usuario import SuperUsuario, PerfilUsuario, HistorialPuntos, Roles, PasswordResetCode
from productos.api.serializers.usuarios import (
    SuperUsuarioSerializer, PerfilUsuarioSerializer, HistorialPuntosSerializer, 
    RolesSerializer, UserRegisterSerializer, CustomTokenObtainPairSerializer
)
from productos.api.serializers.productos import ProductoSerializer
from productos.models.producto import Producto,ProductoAtributo
import random
import string
import re
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, auth

# Configuración de Firebase
cred = credentials.Certificate("tienda_ropa/credentials/credential.json")
firebase_admin.initialize_app(cred)

class RolesViewSet(viewsets.ModelViewSet):
    queryset = Roles.objects.all()
    serializer_class = RolesSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

class SuperUsuarioViewSet(viewsets.ModelViewSet):
    queryset = SuperUsuario.objects.all()
    serializer_class = SuperUsuarioSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            self.permission_classes = [AllowAny]
        elif self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAuthenticated, IsAdminUser]
        return super().get_permissions()

    def get_serializer_context(self):
        return {'request': self.request}

    @action(detail=False, methods=['GET'], url_path='mi-perfil')
    def mi_perfil(self, request):
        try:
            usuario = request.user
            vendedor = SuperUsuario.objects.filter(usuario=usuario)
            serializer = SuperUsuarioSerializer(vendedor, many=True, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error en mi_perfil: {str(e)}")
            return Response({"error": "Ocurrió un error al procesar la solicitud"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PerfilUsuarioViewSet(viewsets.ModelViewSet):
    queryset = PerfilUsuario.objects.all()
    serializer_class = PerfilUsuarioSerializer

    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy', 'create']:
            self.permission_classes = [IsAuthenticated, IsAdminUser]
        else:
            self.permission_classes = [AllowAny]
        return super().get_permissions()

    def partial_update(self, request, *args, **kwargs):
        logger.debug(f"Solicitud PATCH recibida para ID: {kwargs.get('pk')}")
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        try:
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            logger.info(f"PerfilUsuario ID {instance.id} actualizado con éxito")
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error al actualizar PerfilUsuario ID {instance.id}: {str(e)}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['GET'], url_path='puntos/(?P<username>[^/.]+)')
    def obtener_puntos(self, request, username=None):
        perfil = get_object_or_404(PerfilUsuario, usuario__username=username)
        return Response({'puntos_acumulados': perfil.puntos_acumulados}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['GET'], url_path='mi-perfil')
    def mi_perfil(self, request):
        try:
            usuario = request.user
            if not usuario.is_authenticated:
                return Response({"error": "Usuario no autenticado"}, status=status.HTTP_401_UNAUTHORIZED)
            usuario_perfil = get_object_or_404(PerfilUsuario, usuario=usuario)
            serializer = PerfilUsuarioSerializer(usuario_perfil, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error en mi_perfil: {str(e)}")
            return Response({"error": "Ocurrió un error al procesar la solicitud"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['PATCH'], url_path='editar-mi-perfil')
    def editar_mi_perfil(self, request):
        try:
            usuario = request.user
            if not usuario.is_authenticated:
                return Response({"error": "Usuario no autenticado"}, status=status.HTTP_401_UNAUTHORIZED)
            perfil = get_object_or_404(PerfilUsuario, usuario=usuario)
            allowed_fields = {'nombre_apellido', 'dni', 'imagen', 'telefono', 'barrio', 'domicilio', 'pais'}
            data = {k: v for k, v in request.data.items() if k in allowed_fields}
            serializer = PerfilUsuarioSerializer(perfil, data=data, partial=True, context={'request': request})
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error en editar_mi_perfil: {str(e)}")
            return Response({"error": "Ocurrió un error al procesar la solicitud"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    @action(detail=False, methods=['POST'], url_path='toggle-favorito')
    def toggle_favorito(self, request):
        try:
            usuario = request.user
            if not usuario.is_authenticated:
                return Response({"error": "Usuario no autenticado"}, status=status.HTTP_401_UNAUTHORIZED)

            perfil = get_object_or_404(PerfilUsuario, usuario=usuario)
            producto_id = request.data.get('producto_id')

            if not producto_id:
                return Response({"error": "Se requiere el ID del producto"}, status=status.HTTP_400_BAD_REQUEST)

            producto = get_object_or_404(Producto, id=producto_id)

            producto_atributos = ProductoAtributo.objects.filter(producto=producto)

            if not producto_atributos.exists():
                return Response({"error": "No se encontraron atributos para este producto"}, status=status.HTTP_400_BAD_REQUEST)

            favoritos_actuales = perfil.favoritos.all()
            todos_en_favoritos = all(pa in favoritos_actuales for pa in producto_atributos)

            if todos_en_favoritos:
                for pa in producto_atributos:
                    perfil.favoritos.remove(pa)
                action = "removido"
            else:
                for pa in producto_atributos:
                    if pa not in favoritos_actuales:
                        perfil.favoritos.add(pa)
                action = "agregado"

            return Response({
                "message": f"Producto {action} de favoritos",
                "producto_id": producto_id,
                "favoritos": [p.id for p in perfil.favoritos.all()]
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error en toggle_favorito: {str(e)}")
            return Response({"error": "Ocurrió un error al procesar la solicitud"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    @action(detail=False, methods=['GET'], url_path='mis-favoritos')
    def mis_favoritos(self, request):
        try:
            usuario = request.user
            if not usuario.is_authenticated:
                return Response({"error": "Usuario no autenticado"}, status=status.HTTP_401_UNAUTHORIZED)

            perfil = get_object_or_404(PerfilUsuario, usuario=usuario)
            # Obtenemos los ProductoAtributo favoritos
            favoritos = perfil.favoritos.all()
            # Agrupamos por Producto
            productos_favoritos = Producto.objects.filter(producto_atributos__in=favoritos).distinct()
            serializer = ProductoSerializer(productos_favoritos, many=True, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error en mis_favoritos: {str(e)}")
            return Response({"error": "Ocurrió un error al procesar la solicitud"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            

class HistorialPuntosViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = HistorialPuntosSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return HistorialPuntos.objects.filter(perfil__usuario=self.request.user).order_by('-id')

class RegistroUsuarioView(APIView):
    permission_classes = [AllowAny]

    @method_decorator(ratelimit(key='ip', rate='2/m', block=True))
    def post(self, request):
        data = request.data
        username = data.get("username")
        email = data.get("email")
        password = data.get("password")

        if User.objects.filter(username=username).exists() and User.objects.filter(email=email).exists():
            return Response({"error": "El usuario y el correo ya están registrados"}, status=status.HTTP_400_BAD_REQUEST)
        if User.objects.filter(username=username).exists():
            return Response({"error": "El usuario ya existe"}, status=status.HTTP_400_BAD_REQUEST)
        if User.objects.filter(email=email).exists():
            return Response({"error": "El correo ya está registrado"}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.create_user(username=username, email=email, password=password)
        return Response({"message": "Usuario registrado con éxito"}, status=status.HTTP_201_CREATED)

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class GoogleLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        id_token = request.data.get("id_token")
        if not id_token:
            return Response({"error": "No se proporcionó id_token"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            decoded_token = auth.verify_id_token(id_token)
            email = decoded_token["email"]
            uid = decoded_token["uid"]
            user, created = User.objects.get_or_create(
                email=email,
                defaults={"username": email.split("@")[0]}
            )
            refresh = RefreshToken.for_user(user)
            access = str(refresh.access_token)
            return Response({
                "access": access,
                "refresh": str(refresh),
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "is_staff": user.is_staff,
                }
            }, status=status.HTTP_200_OK)
        except auth.InvalidIdTokenError:
            return Response({"error": "Token de Firebase inválido"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]

    @method_decorator(ratelimit(key='ip', rate='5/m', block=True))
    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({"error": "El correo es obligatorio"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "El correo no está registrado"}, status=status.HTTP_400_BAD_REQUEST)

        verification_code = ''.join(random.choices(string.digits, k=6))
        PasswordResetCode.objects.filter(user=user).delete()
        PasswordResetCode.objects.create(user=user, code=verification_code)

        logger.info(f"Código generado: {verification_code}, para el correo: {email}")
        try:
            send_mail(
                'Código de Verificación para Recuperar Contraseña',
                f'Tu código de verificación es: {verification_code}',
                'alesamu.am@gmail.com',
                [email],
                fail_silently=False,
            )
        except Exception as e:
            logger.error(f"Error al enviar el correo: {str(e)}")
            return Response({"error": f"Error al enviar el correo: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({"message": "Código de verificación enviado al correo"}, status=status.HTTP_200_OK)

class VerifyCodeView(APIView):
    permission_classes = [AllowAny]

    @method_decorator(ratelimit(key='ip', rate='5/m', block=True))
    def post(self, request):
        code = request.data.get('code')
        email = request.data.get('email')

        logger.info(f"Recibido código: {code}, email: {email}")
        if not code:
            return Response({"error": "Código no proporcionado"}, status=status.HTTP_400_BAD_REQUEST)
        if not email:
            return Response({"error": "Correo no proporcionado"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "El correo no está registrado"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            reset_code = PasswordResetCode.objects.get(user=user, code=code)
            if reset_code.expires_at < timezone.now():
                reset_code.delete()
                return Response({"error": "El código ha expirado"}, status=status.HTTP_400_BAD_REQUEST)
        except PasswordResetCode.DoesNotExist:
            logger.error(f"Código incorrecto para email: {email}, código recibido: {code}")
            return Response({"error": "Código incorrecto"}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"message": "Código verificado correctamente"}, status=status.HTTP_200_OK)

class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    @method_decorator(ratelimit(key='ip', rate='5/m', block=True))
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        confirm_password = request.data.get('confirm_password')

        if not email:
            return Response({"error": "Correo no proporcionado"}, status=status.HTTP_400_BAD_REQUEST)
        if not password or not confirm_password:
            return Response({"error": "Las contraseñas son obligatorias"}, status=status.HTTP_400_BAD_REQUEST)
        if password != confirm_password:
            return Response({"error": "Las contraseñas no coinciden"}, status=status.HTTP_400_BAD_REQUEST)
        if not re.match(r'^(?=.*[A-Za-z])(?=.*\d)(?=.*[A-Z])[A-Za-z\d]{8,}$', password):
            return Response({"error": "La contraseña debe tener al menos 8 caracteres, con letras, números y mayúsculas."}, 
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
            user.set_password(password)
            user.save()
            PasswordResetCode.objects.filter(user=user).delete()
            return Response({"message": "Contraseña cambiada con éxito"}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({"error": "Usuario no encontrado"}, status=status.HTTP_400_BAD_REQUEST)

class RefreshTokenView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response({"error": "No refresh token provided"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            refresh = RefreshToken(refresh_token)
            new_access_token = str(refresh.access_token)
            return Response({"access": new_access_token})
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAdminUser])
def listar_usuarios(request):
    usuarios = User.objects.all().values('id', 'username', 'email', 'is_active')
    return Response(usuarios, status=status.HTTP_200_OK)

@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def eliminar_usuario(request, user_id):
    try:
        usuario = User.objects.get(id=user_id)
        usuario.delete()
        return Response({"message": "Usuario eliminado con éxito."}, status=status.HTTP_204_NO_CONTENT)
    except User.DoesNotExist:
        return Response({"error": "Usuario no encontrado."}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([AllowAny])
@require_POST
def EnviarEmailFormContact(request):
    try:
        correoUsuario = request.data.get('email')
        nombreUsuario = request.data.get('nombre')
        mensaje = request.data.get('mensaje')

        email = EmailMessage(
            subject="Mensaje de contacto",
            body=f"Email: {correoUsuario},\n\nNombre: {nombreUsuario} \n\nMensaje: {mensaje}",
            to=[os.getenv('EMAIL_HOST')],
        )
        email.send()

        if not correoUsuario:
            logger.error("No se pudo obtener el correo")
        elif not nombreUsuario:
            logger.error("No se pudo obtener el nombre")
        
        return Response({"mensaje": "Mensaje enviado con éxito."}, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Error al enviar el correo: {str(e)}")
        return Response({"error": "No se pudo mandar el correo"}, status=status.HTTP_400_BAD_REQUEST)