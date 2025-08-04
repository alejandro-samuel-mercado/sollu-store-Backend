from django.urls import path, include
from rest_framework.routers import DefaultRouter
from productos.api.views import configuracion, productos, usuarios, ventas

router = DefaultRouter()

# Configuración
router.register(r'envio', configuracion.EnvioViewSet,basename="envio")
router.register(r'barrios', configuracion.BarrioViewSet,basename="barrios")
router.register(r'reviews', configuracion.ReviewViewSet,basename="reviews")
router.register(r'cupones', configuracion.CuponViewSet,basename="cupones")
router.register(r'componentes', configuracion.ComponentesConfiguracionesViewSet,basename="componentes")
router.register(r'colores', configuracion.ColorViewSet,basename="colores")
router.register(r'temas', configuracion.TemaViewSet,basename="temas")
router.register(r'contenidosWeb', configuracion.ContenidosWebViewSet,basename="contenidosWeb")
router.register(r'informacionWeb', configuracion.InformacionWebViewSet, basename='informacionWeb')
router.register(r'fuentes', configuracion.FuenteViewSet,basename="fuentes")
router.register(r'fuentes-aplicar', configuracion.FuenteAplicarViewSet,basename="fuentes_aplicar")
router.register(r'diseños', configuracion.DiseñosViewSet,basename="diseños")
router.register(r'puntos-club', configuracion.PuntosClubViewSet,basename="puntos_club")

# Productos
router.register(r'productos', productos.ProductoViewSet,basename="productos")
router.register(r'categorias', productos.CategoriaViewSet,basename="categorias")
router.register(r'descuentos', productos.DescuentoViewSet,basename="descuentos")
router.register(r'marcas', productos.MarcaViewSet, basename="marcas")  
router.register(r'reviewsProducts', productos.ReviewProductViewSet, basename='reviewProducts')

# Usuarios
router.register(r'vendedores', usuarios.SuperUsuarioViewSet,basename="vendedores")
router.register(r'perfilesUsuarios', usuarios.PerfilUsuarioViewSet,basename="perfilesUsuarios")
router.register(r'historial-puntos', usuarios.HistorialPuntosViewSet,basename="historial_puntos")
router.register(r'roles', usuarios.RolesViewSet,basename="roles")

# Ventas
router.register(r'ventas', ventas.VentaViewSet,basename="ventas")
router.register(r'estados', ventas.EstadosVentaViewSet,basename="estados_venta")
router.register(r'carrito', ventas.CarritoViewSet, basename='carrito')

urlpatterns = [
    # Configuración
    path('validar-cupon/', configuracion.validar_cupon, name='validar_cupon'),
    path('home-data/', configuracion.get_home_data, name='get_home_data'),

    # Usuarios
    path('registro/', usuarios.RegistroUsuarioView.as_view(), name='registro_usuario'),
    path('auth/token/', usuarios.CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/google/', usuarios.GoogleLoginView.as_view(), name='google_login'),
    path('auth/password-reset/request/', usuarios.PasswordResetRequestView.as_view(), name='password_reset_request'),
    path('auth/password-reset/verify/', usuarios.VerifyCodeView.as_view(), name='verify_code'),
    path('auth/password-reset/confirm/', usuarios.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('auth/token/refresh/', usuarios.RefreshTokenView.as_view(), name='token_refresh'),
    path('usuarios/', usuarios.listar_usuarios, name='listar_usuarios'),
    path('usuarios/<int:user_id>/', usuarios.eliminar_usuario, name='eliminar_usuario'),
    path('enviar-mail/', usuarios.EnviarEmailFormContact, name='enviar_email_contacto'),

    # Ventas
    path('crear-venta/', ventas.crear_venta, name='crear_venta'),
    path('pago/', ventas.crear_preferencia, name='crear_preferencia'),
    path('webhook/', ventas.webhook_mp, name='webhook_mp'),
    path('verificar-pago/', ventas.verificar_pago, name='verificar_pago'),
    path('enviar-pdf/', ventas.enviar_pdf, name='enviar_pdf'),
]

urlpatterns += router.urls