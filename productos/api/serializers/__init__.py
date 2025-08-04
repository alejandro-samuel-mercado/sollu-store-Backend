from .productos import (
    CategoriaSerializer, DescuentoSerializer, ProductoSimpleSerializer,
    AtributoSerializer,ProductoSerializer
)
from .usuarios import (
    RolesSerializer, SuperUsuarioSerializer, UserRegisterSerializer,
    PerfilUsuarioSerializer, HistorialPuntosSerializer, CustomTokenObtainPairSerializer
)
from .ventas import (
    CarritoProductoSerializer,
    CarritoSerializer, DetalleVentaSerializer, EstadosVentaSerializer, VentaSerializer
)
from .configuracion import (
    ReviewSerializer, Componentes_ConfiguracionesSerializer, EnvioSerializer, BarrioSerializer, CuponSerializer,
    ColorSerializer, FuenteSerializer, FuenteAplicarSerializer, TemaSerializer,
    ContenidosWebSerializer, InformacionWebSerializer, PuntosClubSerializer,
    DiseñosSerializer
)