from django.contrib import admin
from productos.models import (
    Producto, Categoria, SuperUsuario, Envio, Barrio, Marca,
    Cupon, Descuento, Review,ReviewProduct, Color, Tema, Componentes_Configuraciones, 
    ContenidosWeb, Venta, Fuente, PuntosClub, FuenteAplicar, PerfilUsuario, 
    HistorialPuntos, Carrito, CarritoProducto, EstadosVenta, Roles, Diseños, Atributo, TipoProducto,ProductoAtributo
)
from django.utils.html import format_html
from storages.backends.s3boto3 import S3Boto3Storage
from django import forms

from rest_framework import serializers
from productos.models.producto import Producto, Atributo, ProductoAtributo

# Inline para ProductoAtributo dentro de Producto
class ProductoAtributoInline(admin.TabularInline):
    model = ProductoAtributo
    extra = 1
    fields = ['atributo', 'stock', 'cantidad_vendida', 'imagen']


# Registro de Producto con el Inline para ProductoAtributo
@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    inlines = [ProductoAtributoInline]
    list_display = ['nombre', 'modelo_talle', 'marca', 'tipo', 'precio', 'stock_total', 'cantidad_vendida_total']
    search_fields = ['nombre', 'modelo_talle', 'marca__nombre']
    list_filter = ['tipo', 'marca', 'tendencia', 'categoria']
    fieldsets = (
        (None, {
            'fields': ('tipo', 'marca', 'nombre', 'modelo_talle', 'descripcion', 'precio', 'descuento', 'valor_en_puntos')
        }),
        ('Imágenes', {
            'fields': ('imagen', 'imagen_secundaria', 'imagen_terciaria', 'qr_code')
        }),
        ('Otros', {
            'fields': ('fecha_publicacion', 'tendencia', 'categoria', 'puntos_club_acumulables')
        }),
    )

@admin.register(Marca)
class MarcaAdmin(admin.ModelAdmin):
    list_display = ['nombre']
    search_fields = ['nombre']

@admin.register(Atributo)
class AtributoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'valor']
    search_fields = ['nombre', 'valor']
    list_filter = ['nombre']


@admin.register(TipoProducto)
class TipoProductoAdmin(admin.ModelAdmin):
    list_display = ['nombre']
    search_fields = ['nombre']
    

@admin.register(ReviewProduct)
class ReviewProductAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'comment', 'rating', 'approved', 'created_at']
    list_filter = ['approved', 'product', 'rating']
    search_fields = ['user__username', 'product__nombre', 'comment']
    readonly_fields = ['created_at']
    actions = ['approve_reviews', 'reject_reviews']

    def approve_reviews(self, request, queryset):
        queryset.update(approved=True)
        self.message_user(request, "Las reseñas seleccionadas han sido aprobadas.")
    approve_reviews.short_description = "Aprobar reseñas seleccionadas"

    def reject_reviews(self, request, queryset):
        queryset.delete()
        self.message_user(request, "Las reseñas seleccionadas han sido rechazadas y eliminadas.")
    reject_reviews.short_description = "Rechazar y eliminar reseñas seleccionadas"


@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = ['id', 'comprador', 'fecha_venta', 'precio_total', 'comprobante_pdf_link']
    readonly_fields = ['comprobante_pdf_link']

    def comprobante_pdf_link(self, obj):
        if obj.comprobante_pdf:
            url = obj.comprobante_pdf.url
            return format_html('<a href="{}" target="_blank">Descargar PDF</a>', url)
        return "No disponible"
    comprobante_pdf_link.short_description = "Comprobante PDF"
@admin.register(CarritoProducto)
class CarritoProductoAdmin(admin.ModelAdmin):
    list_display = ('id', 'carrito', 'producto_display', 'atributo_display', 'cantidad')
    list_filter = ('carrito',)
    search_fields = ('producto_atributo__producto__nombre', 'carrito__usuario__username')

    def producto_display(self, obj):
        return obj.producto_atributo.producto.nombre
    producto_display.short_description = "Producto"

    def atributo_display(self, obj):
        return f"{obj.producto_atributo.atributo.nombre}: {obj.producto_atributo.atributo.valor}"
    atributo_display.short_description = "Atributo"

@admin.register(Color)
class ColorAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'codigo_hex', 'mostrar_color')

    def mostrar_color(self, obj):
        color_code = obj.codigo_hex if obj.codigo_hex.startswith('#') else f'#{obj.codigo_hex}'
        return format_html(
            '<div style="width: 50px; height: 20px; background-color: {}; border: 1px solid #000;"></div>',
            color_code
        )
    mostrar_color.short_description = 'Vista de Color'

@admin.register(Tema)
class TemaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'mostrar_tema', 'activo')

    def mostrar_tema(self, obj):
        colores = [obj.primario1, obj.primario2, obj.secundario1, obj.secundario2, obj.terciario, obj.cuarto, obj.fondo1, obj.fondo2, obj.fondo3, obj.fondo4, obj.fondo5]
        return format_html(''.join([
            f'<div style="display:inline-block;width:30px;height:30px;margin-right:5px;background-color:{c.codigo_hex};border-radius:5px;"></div>'
            for c in colores if c
        ]))
    mostrar_tema.short_description = 'Colores del Tema'

admin.site.register(Roles)
admin.site.register(Categoria)
admin.site.register(SuperUsuario)
admin.site.register(Envio)
admin.site.register(Barrio)
admin.site.register(Cupon)
admin.site.register(Descuento)
admin.site.register(Review)
admin.site.register(Componentes_Configuraciones)
admin.site.register(ContenidosWeb)
admin.site.register(Fuente)
admin.site.register(FuenteAplicar)
admin.site.register(Diseños)
admin.site.register(PuntosClub)
admin.site.register(PerfilUsuario)
admin.site.register(HistorialPuntos)
admin.site.register(Carrito)
admin.site.register(EstadosVenta)