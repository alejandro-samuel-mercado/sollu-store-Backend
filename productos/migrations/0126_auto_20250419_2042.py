# productos/migrations/0126_remove_obsolete_columns.py
from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('productos', '0125_fix'),  # Ajusta según la última migración
    ]

    operations = [
        # Eliminar columna producto_talle_id
        migrations.RunSQL(
            sql="""
            ALTER TABLE productos_carritoproducto
            DROP COLUMN IF EXISTS producto_talle_id;
            """,
            reverse_sql="""
            ALTER TABLE productos_carritoproducto
            ADD COLUMN producto_talle_id BIGINT;
            """
        ),
        # Eliminar columna producto_final_id
        migrations.RunSQL(
            sql="""
            ALTER TABLE productos_carritoproducto
            DROP COLUMN IF EXISTS producto_final_id;
            """,
            reverse_sql="""
            ALTER TABLE productos_carritoproducto
            ADD COLUMN producto_final_id BIGINT NOT NULL;
            """
        ),
    ]