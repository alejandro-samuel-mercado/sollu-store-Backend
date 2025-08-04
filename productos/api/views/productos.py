from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.exceptions import ValidationError
from productos.api.common import *
from productos.models.producto import Producto, Marca,Atributo,ReviewProduct
from productos.models.categoria import Categoria, Descuento
from productos.api.serializers.productos import ProductoSerializer, CategoriaSerializer, DescuentoSerializer,MarcaSerializer,AtributoSerializer,ReviewProductSerializer
import qrcode
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
import sys


class MarcaViewSet(viewsets.ModelViewSet):
    queryset = Marca.objects.all()
    serializer_class = MarcaSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            self.permission_classes = [AllowAny]
        elif self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAuthenticated, IsAdminUser]
        return super().get_permissions()

class ProductoViewSet(viewsets.ModelViewSet):
    queryset = Producto.objects.all()
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    serializer_class = ProductoSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            self.permission_classes = [AllowAny]
        elif self.action in ['create', 'destroy']:
            self.permission_classes = [IsAuthenticated, IsAdminUser]
        elif self.action in ['update', 'partial_update']:
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()

    def get_queryset(self):
        queryset = Producto.objects.all()
        categoria = self.request.query_params.get('categoria')
        if categoria:
            return queryset.filter(categoria__nombre=categoria)
        return queryset

    def generar_qr(self, producto):
        try:
            qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
            qr.add_data(f"PRODUCTO_ID:{producto.id}")
            qr.make(fit=True)
            img = qr.make_image(fill='black', back_color='white')
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            buffer.seek(0)
            file_name = f'qr_{producto.id}.png'
            django_file = InMemoryUploadedFile(buffer, None, file_name, 'image/png', sys.getsizeof(buffer), None)
            producto.qr_code.save(file_name, django_file, save=True)
            producto.save()
        except Exception as e:
            logger.error(f"Error al generar QR para producto {producto.id}: {str(e)}")
            raise ValidationError({"qr_code": "Error al generar el código QR."})

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        producto = serializer.save()

        self.generar_qr(producto)
        atributos_data = request.data.get('atributos', [])
        if not atributos_data:
            raise ValidationError({"atributos": "Debe proporcionar al menos un atributo para el producto."})

        for atributo_data in atributos_data:
            atributo_id = atributo_data.get('atributo_id')
            stock = atributo_data.get('stock', 0)
            if not atributo_id:
                raise ValidationError({"atributos": "Cada atributo debe tener un 'atributo_id' válido."})
            try:
                atributo = Atributo.objects.get(id=atributo_id)
            except Atributo.DoesNotExist:
                raise ValidationError({"atributos": f"Atributo con ID {atributo_id} no encontrado."})
            ProductoAtributo.objects.update_or_create(
                producto=producto,
                atributo=atributo,
                defaults={'stock': stock}
            )
        serializer = self.get_serializer(producto)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='gestionar-atributos')
    def gestionar_atributos(self, request, pk=None):
        producto = self.get_object()
        atributos_data = request.data.get('atributos', [])
        if not atributos_data:
            raise ValidationError({"atributos": "Debe proporcionar al menos un atributo para gestionar."})
        for atributo_data in atributos_data:
            atributo_id = atributo_data.get('atributo_id')
            stock = atributo_data.get('stock', 0)
            if not atributo_id:
                raise ValidationError({"atributos": "Cada atributo debe tener un 'atributo_id' válido."})
            try:
                atributo = Atributo.objects.get(id=atributo_id)
            except Atributo.DoesNotExist:
                raise ValidationError({"atributos": f"Atributo con ID {atributo_id} no encontrado."})
            ProductoAtributo.objects.update_or_create(
                producto=producto,
                atributo=atributo,
                defaults={'stock': stock}
            )
        return Response({'message': 'Atributos actualizados'}, status=status.HTTP_200_OK)

class CategoriaViewSet(viewsets.ModelViewSet):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer
    permission_classes = []

class DescuentoViewSet(viewsets.ModelViewSet):
    queryset = Descuento.objects.all()
    serializer_class = DescuentoSerializer
    permission_classes = []

class ReviewProductViewSet(viewsets.ModelViewSet):
    queryset = ReviewProduct.objects.all()
    serializer_class = ReviewProductSerializer

    def get_permissions(self):
        if self.action in ['create']:
            self.permission_classes = [IsAuthenticated]
        elif self.action in ['update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAuthenticated]
        else:
            self.permission_classes = [AllowAny]
        return super().get_permissions()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_queryset(self):
        queryset = ReviewProduct.objects.all()
        product_id = self.request.query_params.get('product_id')
        if product_id:
            queryset = queryset.filter(product_id=product_id, approved=True)
        return queryset

    @action(detail=False, methods=['GET'], url_path='mis-comentarios')
    def mis_comentarios(self, request):
        try:
            usuario = request.user
            if not usuario.is_authenticated:
                return Response({"error": "Usuario no autenticado"}, status=status.HTTP_401_UNAUTHORIZED)
            comentarios = ReviewProduct.objects.filter(user=usuario)
            serializer = ReviewProductSerializer(comentarios, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            print(f"Error en mis_comentarios: {str(e)}")
            return Response({"error": "Ocurrió un error al procesar la solicitud"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['GET'], url_path='overall-rating/(?P<product_id>\d+)')
    def overall_rating(self, request, product_id=None):
        try:
            reviews = ReviewProduct.objects.filter(product_id=product_id, approved=True)
            if not reviews.exists():
                return Response({"average_rating": 0, "total_reviews": 0}, status=status.HTTP_200_OK)
            average_rating = reviews.aggregate(Avg('rating'))['rating__avg']
            total_reviews = reviews.count()
            return Response({
                "average_rating": round(average_rating, 1),
                "total_reviews": total_reviews
            }, status=status.HTTP_200_OK)
        except Exception as e:
            print(f"Error en overall_rating: {str(e)}")
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