# VapaNet — Network Intelligence Suite

Herramienta de diagnóstico y monitorización de red para Windows,
diseñada con la identidad visual de Vapa (verde lima sobre fondo azul-noche).

---

## Herramientas incluidas

| Herramienta       | Descripción                                              |
|-------------------|----------------------------------------------------------|
| Speed Test        | Mide descarga, subida y latencia reales                  |
| Ping              | Comprueba conectividad y latencia a cualquier host       |
| Escáner de Puertos| Escanea puertos TCP en paralelo con presets comunes      |
| DNS Lookup        | Consulta registros A, AAAA, MX, NS, TXT, CNAME, SOA     |
| Traceroute        | Traza la ruta completa con latencia por salto            |
| Batch Ping        | Ping simultáneo a listas de hosts                        |
| Sentinel          | Monitor continuo con ping periódico y alertas            |
| Monitor URLs      | Comprueba disponibilidad HTTP/HTTPS de servicios web     |
| Subnet Calculator | Calcula parámetros completos de subredes CIDR            |
| WHOIS             | Consulta información de registro de dominios             |

---

## Requisitos

- Python 3.10 o superior (recomendado 3.12)
- Windows 10/11 (para el .exe)
- Conexión a internet para speed test, DNS, WHOIS

---

## Instalación y ejecución (modo desarrollo)

```bash
# 1. Clona o descomprime el proyecto
cd vapanet

# 2. Crea un entorno virtual (recomendado)
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac

# 3. Instala dependencias
pip install -r requirements.txt

# 4. Ejecuta el programa
python main.py
```

---

## Compilar a .exe

```bash
# Con el entorno virtual activado y dependencias instaladas:
pyinstaller build.spec

# El ejecutable quedará en:
#   dist/VapaNet.exe
```

### Notas sobre la compilación

- El proceso tarda entre 2 y 5 minutos la primera vez.
- Si PyInstaller falla por módulos de flet no encontrados, añade al spec:
  ```
  hiddenimports=['flet_desktop', 'flet_runtime', ...]
  ```
- Para personalizar el icono: reemplaza `assets/icon.ico` con tu .ico
  (256x256 recomendado, formato ICO).
- Si el EXE da error de antivirus falso positivo, añade una excepción
  en Windows Defender (es normal en ejecutables PyInstaller nuevos).

---

## Estructura del proyecto

```
vapanet/
├── main.py                  # Punto de entrada
├── build.spec               # Configuración PyInstaller
├── requirements.txt
├── vapanet.db               # Base de datos SQLite (se crea al ejecutar)
├── assets/
│   └── icon.ico             # Icono de la app
├── core/
│   ├── __init__.py
│   ├── db.py                # Gestor de base de datos SQLite
│   └── network.py           # Todas las operaciones de red
└── ui/
    ├── __init__.py
    ├── app.py               # Shell principal (sidebar + navegación)
    ├── theme.py             # Sistema de diseño (colores, componentes)
    └── views/
        ├── __init__.py
        ├── dashboard.py     # Pantalla de inicio
        ├── speedtest.py     # Test de velocidad
        ├── ping.py          # Ping individual
        ├── ports.py         # Escáner de puertos
        ├── dns.py           # DNS Lookup
        ├── traceroute.py    # Traceroute en tiempo real
        ├── batch.py         # Batch Ping
        ├── sentinel.py      # Monitor continuo de hosts
        ├── monitor.py       # Monitor de URLs HTTP
        ├── subnet.py        # Calculadora de subredes
        └── whois.py         # WHOIS de dominios
```

---

## Base de datos

El programa crea automáticamente `vapanet.db` (SQLite) en la misma
carpeta del ejecutable. Guarda:

- Historial de speed tests
- Historial de pings
- Hosts del Sentinel
- URLs del Monitor
- Resultados de batch ping
- Historial DNS
- Resultados de escaneos de puertos

---

## Sin instalación de librerías externas de red

Todas las operaciones de red usan únicamente la **biblioteca estándar
de Python** (`socket`, `subprocess`, `urllib`). No se necesita nmap,
scapy, ni ninguna otra librería externa de red.

---

## Licencia

Desarrollado para uso interno de Vapa.
