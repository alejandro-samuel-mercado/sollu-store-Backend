from productos.api.common import *
from productos.models.configuracion import (
    Envio, Barrio, Cupon, Componentes_Configuraciones,Review,
    Color, Tema, ContenidosWeb, Fuente, FuenteAplicar, Diseños, PuntosClub,Review,InformacionWeb
)
from productos.models.producto import Producto
from productos.models.categoria import Categoria,Descuento
from productos.api.serializers.configuracion import (
    EnvioSerializer, BarrioSerializer,ReviewSerializer,
    CuponSerializer, Componentes_ConfiguracionesSerializer,
    ColorSerializer, TemaSerializer, ContenidosWebSerializer, FuenteSerializer,
    FuenteAplicarSerializer, DiseñosSerializer, PuntosClubSerializer,InformacionWebSerializer
)


class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer

    def get_permissions(self):
        if self.action in ['create']:
            self.permission_classes = [IsAuthenticated]
        elif self.action in ['update', 'partial_update', 'destroy']:
            self.permission_classes =[IsAuthenticated]
        else:
            self.permission_classes = [AllowAny]
        return super().get_permissions()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['GET'], url_path='mis-comentarios')
    def mis_comentarios(self, request):
        try:
            usuario = request.user
            if not usuario.is_authenticated:
                return Response({"error": "Usuario no autenticado"}, status=status.HTTP_401_UNAUTHORIZED)
            comentarios = Review.objects.filter(user=usuario)
            serializer = ReviewSerializer(comentarios, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            print(f"Error en mis_comentarios: {str(e)}")
            return Response({"error": "Ocurrió un error al procesar la solicitud"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        user = request.user

        if instance.user != user and not user.is_staff:
            return Response(
                {"error": "No tienes permiso para editar esta reseña"},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
        
    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        user = request.user

        if instance.user != user and not user.is_staff:
            return Response(
                {"error": "No tienes permiso para editar esta reseña"},
                status=status.HTTP_403_FORBIDDEN
            )  
        if user.is_staff and 'action' in request.data:
            action = request.data.get('action')
            if action == 'approve':
                instance.approved = True
                instance.save()
                return Response({'status': 'Reseña aprobada'}, status=status.HTTP_200_OK)
            elif action == 'reject':
                instance.delete()
                return Response({'status': 'Reseña rechazada'}, status=status.HTTP_204_NO_CONTENT)
            else:
                return Response({'error': 'Acción no válida'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        user = request.user

        if instance.user != user and not user.is_staff:
            return Response(
                {"error": "No tienes permiso para eliminar esta reseña"},
                status=status.HTTP_403_FORBIDDEN
            )

        instance.delete()
        return Response({"status": "Reseña eliminada"}, status=status.HTTP_204_NO_CONTENT)


class EnvioViewSet(viewsets.ModelViewSet):
    queryset = Envio.objects.all()
    serializer_class = EnvioSerializer
    permission_classes = [AllowAny]

class BarrioViewSet(viewsets.ModelViewSet):
    queryset = Barrio.objects.all()
    serializer_class = BarrioSerializer
    permission_classes = [AllowAny]

class CuponViewSet(viewsets.ModelViewSet):
    queryset = Cupon.objects.all()
    serializer_class = CuponSerializer
    permission_classes = [IsAdminUser]

@api_view(['POST'])
@permission_classes([AllowAny])
def validar_cupon(request):
    codigo_cupon = request.data.get('codigo')
    if not codigo_cupon:
        return Response({'error': 'No se proporcionó un código de cupón.'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        cupon = Cupon.objects.get(codigo=codigo_cupon)
    except Cupon.DoesNotExist:
        return Response({'error': 'El código de cupón no es válido.'}, status=status.HTTP_404_NOT_FOUND)

    if cupon.fecha_expiracion and cupon.fecha_expiracion < timezone.now():
        return Response({'error': 'El cupón ha expirado.'}, status=status.HTTP_400_BAD_REQUEST)
    
    return Response({'descuento': str(cupon.descuento)}, status=status.HTTP_200_OK)



class ComponentesConfiguracionesViewSet(viewsets.ModelViewSet):
    queryset = Componentes_Configuraciones.objects.all()
    serializer_class = Componentes_ConfiguracionesSerializer

    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy', 'create']:
            self.permission_classes = [IsAuthenticated, IsAdminUser]
        else:
            self.permission_classes = [AllowAny]
        return super().get_permissions()

class ColorViewSet(viewsets.ModelViewSet):
    queryset = Color.objects.all()
    serializer_class = ColorSerializer
    permission_classes = [AllowAny]

class TemaViewSet(viewsets.ModelViewSet):
    queryset = Tema.objects.all()
    serializer_class = TemaSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

    @action(detail=False, methods=['get'])
    def activo(self, request):
        tema = Tema.objects.filter(activo=True).first()
        serializer = self.get_serializer(tema)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def activar(self, request, pk=None):
        Tema.objects.update(activo=False)
        tema = self.get_object()
        tema.activo = True
        tema.save()
        return Response(self.get_serializer(tema).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['patch'], url_path='actualizar-fuente')
    def actualizar_fuente(self, request, pk=None):
        tema = self.get_object()
        fuente_campo = request.data.get('fuente_campo')
        fuente_id = request.data.get('fuente_id')
        color_id = request.data.get('color_id')

        if fuente_campo not in ['fuente_primaria', 'fuente_secundaria', 'fuente_terciaria']:
            return Response({"error": "Campo de fuente inválido"}, status=status.HTTP_400_BAD_REQUEST)

        fuente_aplicar = getattr(tema, fuente_campo)
        if not fuente_aplicar:
            fuente_aplicar = FuenteAplicar()

        if fuente_id:
            fuente_aplicar.fuente = Fuente.objects.get(id=fuente_id)
        if color_id:
            fuente_aplicar.color = Color.objects.get(id=color_id)
        fuente_aplicar.save()

        setattr(tema, fuente_campo, fuente_aplicar)
        tema.save()
        return Response(self.get_serializer(tema).data, status=status.HTTP_200_OK)

class ContenidosWebViewSet(viewsets.ModelViewSet):
    queryset = ContenidosWeb.objects.all()
    serializer_class = ContenidosWebSerializer

    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy', 'create']:
            self.permission_classes = [IsAuthenticated, IsAdminUser]
        else:
            self.permission_classes = [AllowAny]
        return super().get_permissions()

class InformacionWebViewSet(ModelViewSet):
    queryset = InformacionWeb.objects.all()
    serializer_class = InformacionWebSerializer
    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy','create']: 
            self.permission_classes = [IsAuthenticated, IsAdminUser]
        else:
            self.permission_classes = [AllowAny]
        return super().get_permissions()

class FuenteViewSet(viewsets.ModelViewSet):
    queryset = Fuente.objects.all()
    serializer_class = FuenteSerializer
    permission_classes = [AllowAny]

class FuenteAplicarViewSet(viewsets.ModelViewSet):
    queryset = FuenteAplicar.objects.all()
    serializer_class = FuenteAplicarSerializer
    permission_classes = [AllowAny]

class DiseñosViewSet(viewsets.ModelViewSet):
    queryset = Diseños.objects.all()
    serializer_class = DiseñosSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

    @action(detail=False, methods=['get'])
    def activo(self, request):
        diseño = Diseños.objects.filter(activo=True).first()
        serializer = self.get_serializer(diseño)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def activar(self, request, pk=None):
        Diseños.objects.update(activo=False)
        diseño = self.get_object()
        diseño.activo = True
        diseño.save()
        return Response(self.get_serializer(diseño).data, status=status.HTTP_200_OK)

class PuntosClubViewSet(viewsets.ModelViewSet):
    queryset = PuntosClub.objects.all()
    serializer_class = PuntosClubSerializer

    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy', 'create']:
            self.permission_classes = [IsAuthenticated, IsAdminUser]
        else:
            self.permission_classes = [AllowAny]
        return super().get_permissions()



@api_view(['GET'])
@permission_classes([AllowAny])
def get_home_data(request):
    colores = Color.objects.all().values()
    tema_activo = Tema.objects.filter(activo=True).values().first()
    diseño_activo = Diseños.objects.filter(activo=True).values().first()
    fuente_activa = Fuente.objects.filter(activo=True).values().first()

    return Response({
        "colores": colores,
        "diseño_activo": diseño_activo,
        "tema_activo": tema_activo,
        "fuente_activa": fuente_activa,
    })