# RegaloLab — PC2

Aplicación pequeña de regalos personalizados para Sistemas Operativos. Usa Python 3.10+, FastAPI, Jinja2, Bootstrap 5 y psycopg. Consulta y registra productos en la tabla existente `productos` de PostgreSQL 16. No crea tablas ni datos de ejemplo.

## 1. Crear el entorno virtual

Desde la raíz del proyecto, en Windows (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

En Ubuntu:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## 2. Instalar las dependencias

Con el entorno activo:

```bash
python -m pip install -r requirements.txt
```

## 3. Configurar la conexión

Copia `.env.example` como `.env`:

```powershell
# Windows
Copy-Item .env.example .env
```

```bash
# Ubuntu
cp .env.example .env
chmod 600 .env
```

Edita `.env` y completa `DB_HOST`, `DB_USER` y `DB_PASSWORD` con tus valores. `DB_PORT` normalmente es `5432` y `DB_NAME` es `regalos_db`. Si la contraseña contiene espacios o `#`, escríbela entre comillas. También puedes definir las cinco variables directamente en el entorno del proceso: tienen prioridad sobre `.env`.

El usuario de PostgreSQL necesita permisos para consultar e insertar en `productos` y utilizar su secuencia de identidad. No subas `.env` ni credenciales a Git.

## 4. Ejecutar localmente

```bash
uvicorn app.main:app --reload
```

Abre http://127.0.0.1:8000 y entra en **Productos**. Para acceder a Data EC2 desde tu PC, necesitas una ruta de red disponible: por ejemplo, una VPN o un túnel SSH. Una IP privada de EC2 no es accesible directamente desde Internet. Si ya tienes acceso público configurado, limita el puerto de PostgreSQL a tu IP de desarrollo.

## 5. Ejecutar en Ubuntu EC2

En la instancia **Application EC2**, con Ubuntu Server 24.04:

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip
```

Copia el proyecto a esa instancia, entra en su carpeta y sigue los pasos 1 a 3 para Ubuntu. No necesitas instalar el servidor PostgreSQL en Application EC2. Configura `DB_HOST` con la IP privada o el DNS privado de **Data EC2**, siempre que ambas instancias tengan comunicación por su VPC.

Con el entorno virtual activo, ejecuta desde la raíz:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Visita `http://IP_PUBLICA_APPLICATION_EC2:8000`. Este comando corre en primer plano; detenerlo o cerrar la sesión puede detener la aplicación. Es suficiente para las pruebas de la PC2.

## 6. Puertos y conexión entre instancias

```text
Navegador → Application EC2 (FastAPI, TCP 8000)
                     → Data EC2 (PostgreSQL, TCP 5432, regalos_db)
```

- **8000:** permite entrada en el Security Group de Application EC2 desde la IP desde la que harás las pruebas.
- **5432:** permite entrada en el Security Group de Data EC2 desde el Security Group de Application EC2. Verifica también que la salida de Application EC2 permita esa conexión.
- En Data EC2, PostgreSQL debe escuchar en la interfaz privada (`listen_addresses`) y `pg_hba.conf` debe permitir la base, el usuario y el origen de Application EC2. Los cambios en `listen_addresses` requieren reiniciar PostgreSQL; los de `pg_hba.conf`, recargar su configuración.
- Si utilizas firewall del sistema, sus reglas también deben permitir esos puertos. No es necesario abrir PostgreSQL a todo Internet.

## Comprobación rápida

1. `/` muestra RegaloLab incluso sin conexión a PostgreSQL.
2. `/productos` consulta los seis campos de la tabla existente.
3. Envía el formulario: guarda un producto con `activo = TRUE` y redirige a la lista.
4. Si la base no está disponible, la página muestra un mensaje entendible sin revelar credenciales.

El nombre es obligatorio (máximo 120 caracteres); el precio acepta valores no negativos con hasta dos decimales y el stock acepta enteros no negativos. La descripción es opcional. Bootstrap se carga por CDN y necesita conexión a Internet para aplicar sus estilos.
