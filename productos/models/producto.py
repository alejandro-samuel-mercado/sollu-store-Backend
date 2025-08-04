from django.db import models
from django.utils.timezone import now
from decimal import Decimal
from storages.backends.s3boto3 import S3Boto3Storage


class TipoProducto(models.Model):
    nombre = models.CharField(max_length=100)  

    def __str__(self):
        return self.nombre

    class Meta:
        indexes = [models.Index(fields=['nombre'])]


class Marca(models.Model):
    nombre = models.CharField(max_length=100)  

    def __str__(self):
        return self.nombre

    class Meta:
        indexes = [models.Index(fields=['nombre'])]


class Atributo(models.Model):
    nombre = models.CharField(max_length=100,null=True) 
    valor = models.CharField(max_length=100)  

    def __str__(self):
        return f"{self.nombre}: {self.valor}"

    class Meta:
        unique_together = ['nombre', 'valor']
        indexes = [models.Index(fields=['nombre', 'valor'])]


class Producto(models.Model):
    tipo = models.ForeignKey(
        TipoProducto,
        on_delete=models.CASCADE,
        related_name='productos',null=True
    )
    marca = models.ForeignKey(
        Marca,
        on_delete=models.CASCADE,
        related_name='productos',null=True
    )
    categoria = models.ForeignKey('Categoria', on_delete=models.CASCADE, related_name='productos', default=1, null=True, blank=True)
    nombre = models.CharField(max_length=100)
    modelo_talle = models.CharField(max_length=100,null=True)
    descripcion = models.TextField()
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    valor_en_puntos = models.DecimalField(max_digits=10, decimal_places=2, default=0, blank=True, null=True)
    descuento = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        blank=True,
        null=True
    )
    fecha_publicacion = models.DateTimeField(
        default=now,
        null=True,
        blank=True
    )
    imagen = models.ImageField(
        storage=S3Boto3Storage(),
        upload_to='productos/',
        null=True,
        blank=True
    )
    imagen_secundaria = models.ImageField(
        storage=S3Boto3Storage(),
        upload_to='productos/',
        null=True,
        blank=True
    )
    imagen_terciaria = models.ImageField(
        storage=S3Boto3Storage(),
        upload_to='productos/',
        null=True,
        blank=True
    )
    atributos = models.ManyToManyField(
        Atributo,
        through='ProductoAtributo',
        related_name='productos'
    )
    tendencia = models.BooleanField(blank=True, null=True)
    categoria = models.ForeignKey('Categoria', on_delete=models.CASCADE, related_name='productos', default=1, null=True, blank=True)
    puntos_club_acumulables = models.IntegerField(null=True, blank=True)
    qr_code = models.ImageField(storage=S3Boto3Storage(), upload_to='qr_codes/', null=True, blank=True)


    @property
    def stock_total(self):
        return sum(attr.stock for attr in self.producto_atributos.all())

    @property
    def cantidad_vendida_total(self):
        return sum(attr.cantidad_vendida for attr in self.producto_atributos.all())

    def __str__(self):
        marca_nombre = self.marca.nombre if self.marca else "Sin Marca"
        return f"{marca_nombre} {self.nombre} - {self.modelo_talle}"

    class Meta:
        unique_together = ['nombre', 'modelo_talle']
        indexes = [
            models.Index(fields=['nombre', 'modelo_talle']),
            models.Index(fields=['tipo']),
            models.Index(fields=['marca']),
        ]


class ProductoAtributo(models.Model):
    producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,
        related_name='producto_atributos'
    )
    atributo = models.ForeignKey(
        Atributo,
        on_delete=models.CASCADE,
        related_name='producto_atributos'
    )
    stock = models.PositiveIntegerField(default=0)
    cantidad_vendida = models.PositiveIntegerField(default=0)
    imagen = models.ImageField(
        storage=S3Boto3Storage(),
        upload_to='atributos/',
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.producto} - {self.atributo}"

    class Meta:
        unique_together = ['producto', 'atributo']
        indexes = [models.Index(fields=['producto', 'atributo'])]


class ReviewProduct(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='reviewsProduct')
    product = models.ForeignKey('Producto', on_delete=models.CASCADE, related_name='reviews')
    comment = models.TextField()
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Reseña de {self.user.username} para {self.product.nombre} - {self.rating} estrellas"