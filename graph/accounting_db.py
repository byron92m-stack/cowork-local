"""CRUD para facturas electrónicas (SRI Ecuador)."""
import os, logging
import asyncpg
from asyncpg import create_pool
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
DB_NAME = os.getenv("POSTGRES_DB", "coworkdb")
DB_USER = os.getenv("POSTGRES_USER", "cowork")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "coworkpass")

_pool = None

async def get_pool():
    global _pool
    if _pool is None:
        _pool = await create_pool(
            host=DB_HOST, port=DB_PORT, database=DB_NAME,
            user=DB_USER, password=DB_PASSWORD
        )
    return _pool

async def init_invoices_table():
    """Crea la tabla invoices si no existe."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS invoices (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                numero_factura TEXT NOT NULL,
                ruc_emisor TEXT NOT NULL,
                razon_social TEXT,
                fecha_emision DATE,
                subtotal DECIMAL(12,2),
                iva DECIMAL(12,2),
                total DECIMAL(12,2),
                source_email TEXT,
                attachment_path TEXT,
                raw_data JSONB,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                UNIQUE(numero_factura, ruc_emisor)
            )
        """)
        logger.info("Tabla invoices verificada/creada")

async def save_invoice(data: dict) -> dict:
    """Guarda una factura en la DB. Retorna la fila creada o None si es duplicado."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        try:
            row = await conn.fetchrow(
                """INSERT INTO invoices 
                   (numero_factura, ruc_emisor, razon_social, fecha_emision,
                    subtotal, iva, total, source_email, attachment_path, raw_data)
                   VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                   ON CONFLICT (numero_factura, ruc_emisor) DO NOTHING
                   RETURNING *""",
                data.get('numero_factura', ''),
                data.get('ruc_emisor', ''),
                data.get('razon_social', ''),
                data.get('fecha_emision'),
                data.get('subtotal'),
                data.get('iva'),
                data.get('total'),
                data.get('source_email', ''),
                data.get('attachment_path', ''),
                data.get('raw_data', {})
            )
            return dict(row) if row else None
        except Exception as e:
            logger.error(f"Error guardando factura: {e}")
            return None

async def invoice_exists(numero_factura: str, ruc_emisor: str) -> bool:
    """Verifica si una factura ya existe."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id FROM invoices WHERE numero_factura=$1 AND ruc_emisor=$2",
            numero_factura, ruc_emisor
        )
        return row is not None
