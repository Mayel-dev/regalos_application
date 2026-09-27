from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Annotated

import psycopg
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.database import get_connection

BASE_DIR = Path(__file__).resolve().parent
app = FastAPI(title="RegaloLab")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


def products_page(request, error=None, form=None, status_code=200):
    products = []
    try:
        with get_connection() as connection:
            products = connection.execute(
                "SELECT id_producto, nombre, descripcion, precio, stock, activo "
                "FROM productos ORDER BY id_producto"
            ).fetchall()
    except (psycopg.Error, ValueError):
        error = error or (
            "No se pudieron cargar los productos. Revisa las variables de entorno "
            "y la conexión con PostgreSQL e inténtalo nuevamente."
        )
        status_code = 503

    return templates.TemplateResponse(
        request=request,
        name="productos.html",
        context={"products": products, "error": error, "form": form or {}},
        status_code=status_code,
    )


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


@app.get("/productos", response_class=HTMLResponse)
def list_products(request: Request):
    return products_page(request)


@app.post("/productos", response_class=HTMLResponse)
def create_product(
    request: Request,
    nombre: Annotated[str, Form()] = "",
    descripcion: Annotated[str, Form()] = "",
    precio: Annotated[str, Form()] = "",
    stock: Annotated[str, Form()] = "",
):
    form = {"nombre": nombre, "descripcion": descripcion, "precio": precio, "stock": stock}
    try:
        name = nombre.strip()
        if not name or len(name) > 120:
            raise ValueError("El nombre es obligatorio y debe tener como máximo 120 caracteres.")
        try:
            price = Decimal(precio)
        except InvalidOperation:
            raise ValueError("Ingresa un precio válido.") from None
        if not price.is_finite() or not Decimal("0") <= price <= Decimal("99999999.99"):
            raise ValueError("El precio debe estar entre 0 y 99999999.99.")
        if price != price.quantize(Decimal("0.01")):
            raise ValueError("El precio debe tener como máximo dos decimales.")
        try:
            quantity = int(stock)
        except ValueError:
            raise ValueError("El stock debe ser un número entero.") from None
        if not 0 <= quantity <= 2147483647:
            raise ValueError("El stock debe estar entre 0 y 2147483647.")
    except ValueError as error:
        return products_page(request, error=str(error), form=form, status_code=422)

    try:
        with get_connection() as connection:
            connection.execute(
                "INSERT INTO productos (nombre, descripcion, precio, stock, activo) "
                "VALUES (%s, %s, %s, %s, TRUE)",
                (name, descripcion.strip() or None, price, quantity),
            )
    except (psycopg.Error, ValueError):
        return products_page(
            request,
            error="No se pudo registrar el producto. Revisa la conexión y la configuración de PostgreSQL.",
            form=form,
            status_code=503,
        )

    return RedirectResponse(url="/productos", status_code=303)
