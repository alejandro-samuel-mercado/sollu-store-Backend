from django.db import models
from storages.backends.s3boto3 import S3Boto3Storage

class Categoria(models.Model):
    nombre = models.CharField(max_length=50)
    imagen = models.ImageField(storage=S3Boto3Storage(), upload_to='categorias/', null=True, blank=True)

    def __str__(self):
        return self.nombre

class Descuento(models.Model):
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, related_name='descuentos')
    porcentaje = models.DecimalField(max_digits=4, decimal_places=2, blank=True, null=True)

    def __str__(self):
        return f"{self.categoria.nombre} - {self.porcentaje}%"


