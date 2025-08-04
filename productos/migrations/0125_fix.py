# productos/migrations/0125_fix.py
from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('productos', '0124_marca_producto_marca_delete_productofinal_and_more'),
    ]

    operations = [
        # Agregar columna variante_id a productos_carritoproducto si no existe
        migrations.RunSQL(
            sql="""
            ALTER TABLE productos_carritoproducto
            ADD COLUMN IF NOT EXISTS variante_id BIGINT
            REFERENCES productos_variante(id) ON DELETE CASCADE;
            """,
            reverse_sql="""
            ALTER TABLE productos_carritoproducto
            DROP COLUMN IF EXISTS variante_id;
            """
        ),
        # Crear la tabla productos_perfilusuario_favoritos si no existe
        migrations.RunSQL(
            sql="""
            CREATE TABLE IF NOT EXISTS productos_perfilusuario_favoritos (
                id BIGSERIAL PRIMARY KEY,
                perfilusuario_id BIGINT NOT NULL REFERENCES productos_perfilusuario(id) ON DELETE CASCADE,
                variante_id BIGINT NOT NULL REFERENCES productos_variante(id) ON DELETE CASCADE,
                UNIQUE (perfilusuario_id, variante_id)
            );
            """,
            reverse_sql="""
            DROP TABLE IF EXISTS productos_perfilusuario_favoritos;
            """
        ),
    ]