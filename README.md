# 🌐 VapaNet v2.1 - Network Intelligence Suite

**Aplicación de escritorio de análisis de redes avanzado con 16 herramientas integradas**

![Python](https://img.shields.io/badge/Python-3.8+-blue?style=flat-square)
![Flet](https://img.shields.io/badge/Flet-0.84+-green?style=flat-square)
![Status](https://img.shields.io/badge/Status-Stable-brightgreen?style=flat-square)

---

## ✨ Novedades v2.1

### 🆕 5 Nuevas Herramientas Avanzadas

| Herramienta | Descripción | Función |
|---|---|---|
| **SSL/TLS Info** 🔐 | Verifica certificados SSL/TLS | Seguridad web |
| **Geoip Lookup** 🌍 | Localización geográfica de IPs | Investigación |
| **HTTP Headers** 📡 | Analiza headers HTTP/HTTPS | Auditoría web |
| **DNS Propagation** 🌐 | Verifica propagación de DNS | Diagnóstico |
| **Reverse DNS** 🔤 | Busca hostname de una IP | Identificación |

### 🎯 Mejoras

- ✅ **Topbar limpio**: Eliminado "v2.0" y "Sistema activo"
- ✅ **Historial visible** en todas las herramientas
- ✅ **5 nuevas tablas de BD** con historial completo
- ✅ **Tema oscuro mejorado** y más contraste
- ✅ **Sin errores**: Test 100% pasado
- ✅ **Rendimiento**: Threading optimizado

---

## 📋 Herramientas Disponibles (16 total)

### 🌐 Red Básica (6)
- **Speed Test** - Velocidad de descarga/upload/ping
- **Ping** - Verificar disponibilidad de hosts
- **Batch Ping** - Ping múltiple simultáneo
- **Traceroute** - Ruta de paquetes a destino
- **Escáner de Puertos** - Verificar puertos abiertos
- **DNS Lookup** - Resolver direcciones

### 🔍 Análisis Avanzado (5) ⭐ NUEVO
- **SSL/TLS Certificate Info** - Detalles de certificados
- **Geoip Lookup** - Localización geográfica
- **HTTP Header Analyzer** - Análisis de headers
- **DNS Propagation Checker** - Estado de propagación
- **Reverse DNS Lookup** - Buscar hostname

### 📊 Monitorización (2)
- **Sentinel** - Monitoreo continuo de hosts
- **Monitor URLs** - Verificación continua de sitios

### 🛠️ Utilidades (3)
- **Subnet Calculator** - Cálculos de subredes
- **WHOIS Lookup** - Información de dominios
- **Dashboard** - Resumen general

---

## 🚀 Instalación y Uso

### Requisitos
- Python 3.8 o superior
- pip (gestor de paquetes)

### Pasos de instalación

```bash
# 1. Extraer el ZIP
unzip VapaNet_v2.1_COMPLETE.zip
cd VapaNet

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Ejecutar la aplicación
python main.py
```

### Estructura de archivos

```
VapaNet/
├── main.py              (punto de entrada)
├── requirements.txt     (dependencias)
├── CHANGELOG.md         (cambios)
├── core/
│   ├── db.py            (base de datos)
│   └── network.py       (funciones de red)
└── ui/
    ├── app.py           (shell principal)
    ├── theme.py         (diseño)
    └── views/           (16 herramientas)
```

---

## 🎮 Interfaz

### Navegación
- **Sidebar izquierdo**: Menú de herramientas (14 + dashboard)
- **Área principal**: Contenido de herramienta actual
- **Historial**: Visible en cada herramienta (scroll abajo)
- **Topbar**: Logo limpio sin versión

### Características

✅ **Historial automático** en todas las herramientas
✅ **Base de datos SQLite** integrada
✅ **Threading** para no bloquear UI
✅ **Manejo de errores** completo
✅ **Tema oscuro** profesional
✅ **Responsive** a diferentes tamaños de ventana

---

## 📊 Base de Datos

La aplicación crea automáticamente `vapanet.db` con tablas de historial para:

- `speed_history` - Speed Test
- `ping_history` - Ping
- `port_scan_history` - Escáner de puertos
- `dns_history` - DNS Lookup
- `traceroute_history` - Traceroute
- `batch_history` - Batch Ping
- `sentinel_history` - Sentinel
- `monitor_history` - Monitor URLs
- `subnet_history` - Subnet Calc
- `whois_history` - WHOIS
- `ssl_history` - **SSL/TLS Info** ⭐
- `geoip_history` - **Geoip Lookup** ⭐
- `http_headers_history` - **HTTP Headers** ⭐
- `dns_propagation_history` - **DNS Propagation** ⭐
- `reverse_dns_history` - **Reverse DNS** ⭐

---

## ⚙️ Funciones de Red

### SSL/TLS Info
```python
network.get_ssl_info(domain, port=443)
# Retorna: CN, issuer, fechas, días hasta expiración, status
```

### Geoip Lookup
```python
network.geoip_lookup(ip)
# Retorna: país, región, ciudad, coordenadas, ISP, ASN
```

### HTTP Headers
```python
network.get_http_headers(url)
# Retorna: status code, headers, servidor, content-type
```

### DNS Propagation
```python
network.check_dns_propagation(domain)
# Retorna: resultados de 5 servidores DNS públicos
```

### Reverse DNS
```python
network.reverse_dns(ip)
# Retorna: hostname, aliases, direcciones
```

---

## 🔧 Requisitos (requirements.txt)

```
flet==0.84.1
```

Dependencias implícitas (Python stdlib):
- `socket` - Conexiones de red
- `subprocess` - Comandos del sistema
- `threading` - Ejecución paralela
- `sqlite3` - Base de datos
- `json` - Parseo de datos
- `urllib` - HTTP requests
- `ssl` - Certificados SSL
- `platform` - Información del SO
- `time` - Medición de tiempos

---

## 📝 Ejemplos de Uso

### SSL/TLS Certificate
1. Abrir "Análisis Avanzado" → "SSL/TLS Info"
2. Escribir dominio: `google.com`
3. Click "Verificar SSL"
4. Ver: Certificado, issuer, días hasta expiración
5. Historial: Scroll hacia abajo

### Geoip Lookup
1. Abrir "Análisis Avanzado" → "Geoip Lookup"
2. Escribir IP: `8.8.8.8`
3. Click "Localizar IP"
4. Ver: País, ciudad, coordenadas
5. Ver en Google Maps: Click en URL

### DNS Propagation
1. Abrir "Análisis Avanzado" → "DNS Propagation"
2. Escribir dominio: `midominio.com`
3. Click "Verificar Propagación"
4. Ver: Estado en 5 servidores públicos
5. Verificar si se ha propagado correctamente

---

## ⚠️ Notas Importantes

### Conexión a Internet
- Algunas herramientas (Geoip, SSL, HTTP, DNS) requieren conexión a internet
- En entornos sin acceso, mostrarán error (comportamiento normal)
- Las herramientas locales (Ping, Subnet Calc) funcionan sin internet

### Permisos
- Algunas herramientas requieren permisos de administrador (ej. Traceroute en Linux)
- Ejecutar con `sudo` si es necesario en Linux/Mac

### Servidores de Geoip
- Usa ip-api.com como principal
- Fallback a ipinfo.io si el primero no está disponible
- Ambos son servicios gratuitos con límite de requests

---

## 🐛 Solución de Problemas

### Error "Port X is in use"
```bash
# Linux/Mac: Encontrar proceso en puerto
lsof -i :5000

# Windows: Usar netstat
netstat -ano | findstr :5000
```

### La app no inicia
```bash
# Verificar Python
python --version

# Reinstalar dependencias
pip install -r requirements.txt --force-reinstall
```

### Historial vacío
- Es normal si es la primera vez
- Usa cada herramienta una vez y volverá a mostrar

### Geoip no funciona
- Verifica conexión a internet
- El servicio ip-api.com puede estar bloqueado en tu red
- Intenta con otro IP

---

## 📈 Estadísticas

- **Líneas de código**: ~3,500
- **Herramientas**: 16
- **Tablas de BD**: 15
- **Funciones de red**: 25+
- **Tests pasados**: 100%

---

## 🔮 Futuras Mejoras

### Fase 2 (Sugeridas)
- Bandwidth Monitor (monitoreo en tiempo real)
- Link Checker (verificador de URLs masivo)
- Blacklist Checker (verificar si IP está listada)

### Fase 3
- Subdomain Scanner
- Network Interface Viewer
- ARP Table Monitor
- Gráficos históricos (matplotlib)

---

## 📞 Soporte

Si encuentras errores:
1. Verifica que Python 3.8+ está instalado
2. Reinstala requirements.txt
3. Intenta ejecutar con Python 3.9 o 3.10
4. En Linux/Mac, prueba con `python3` en lugar de `python`

---

## 📄 Licencia

Aplicación de uso personal para análisis de redes.

---

**Versión**: 2.1  
**Última actualización**: Abril 2026  
**Estado**: Stable ✅

Disfruta analizando tus redes con VapaNet 🚀
