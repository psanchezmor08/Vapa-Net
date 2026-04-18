"""
VapaNet — Operaciones de red
Ping, traceroute, DNS, escáner de puertos, subnet calc, speedtest
"""

import socket
import subprocess
import platform
import time
import re
import threading
import struct
import os
from typing import Callable, Optional


# ──────────────────────────────────────────────
# PING
# ──────────────────────────────────────────────

def ping_host(host: str, count: int = 4, timeout: int = 1) -> dict:
    """
    Lanza ping al host. Devuelve dict con avg_ms, packet_loss, status, raw.
    Funciona en Windows y Linux/Mac.
    """
    sys = platform.system().lower()
    if sys == "windows":
        cmd = ["ping", "-n", str(count), "-w", str(timeout * 1000), host]
    else:
        cmd = ["ping", "-c", str(count), "-W", str(timeout), host]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=count * (timeout + 2)
        )
        output = result.stdout + result.stderr
        avg_ms = _parse_ping_avg(output, sys)
        loss = _parse_ping_loss(output, sys)
        status = "up" if result.returncode == 0 else "down"
        return {"host": host, "avg_ms": avg_ms, "packet_loss": loss, "status": status, "raw": output}
    except subprocess.TimeoutExpired:
        return {"host": host, "avg_ms": 0.0, "packet_loss": 100.0, "status": "timeout", "raw": "Timeout"}
    except FileNotFoundError:
        return {"host": host, "avg_ms": 0.0, "packet_loss": 100.0, "status": "error", "raw": "ping no disponible"}
    except Exception as e:
        return {"host": host, "avg_ms": 0.0, "packet_loss": 100.0, "status": "error", "raw": str(e)}


def _parse_ping_avg(output: str, sys: str) -> float:
    patterns = [
        r"Average\s*=\s*([\d.]+)\s*ms",           # Windows
        r"avg.*?=\s*[\d.]+/([\d.]+)/",             # Linux
        r"round-trip.*?=\s*[\d.]+/([\d.]+)/",      # macOS
        r"tiempo\s*=\s*([\d.]+)\s*ms",             # Windows ES
        r"([\d.]+)\s*ms",                          # fallback
    ]
    for p in patterns:
        m = re.search(p, output, re.IGNORECASE)
        if m:
            try:
                return float(m.group(1))
            except ValueError:
                pass
    return 0.0


def _parse_ping_loss(output: str, sys: str) -> float:
    patterns = [
        r"(\d+)%\s*(?:packet\s*)?loss",
        r"(\d+)%\s*perdidos",
        r"(\d+)%\s*de\s*pérdida",
    ]
    for p in patterns:
        m = re.search(p, output, re.IGNORECASE)
        if m:
            try:
                return float(m.group(1))
            except ValueError:
                pass
    return 0.0


# ──────────────────────────────────────────────
# TRACEROUTE
# ──────────────────────────────────────────────

def traceroute(host: str, max_hops: int = 20, timeout: int = 2,
               on_hop: Optional[Callable] = None) -> list:
    """
    Ejecuta traceroute/tracert y devuelve lista de hops.
    on_hop(hop_dict) se llama por cada salto en tiempo real.
    """
    sys = platform.system().lower()
    if sys == "windows":
        cmd = ["tracert", "-h", str(max_hops), "-w", str(timeout * 1000), host]
    else:
        cmd = ["traceroute", "-m", str(max_hops), "-w", str(timeout), host]

    hops = []
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        hop_re = re.compile(
            r"^\s*(\d+)\s+"
            r"(?:([\d.]+)\s*ms\s*)?"
            r"(?:([\d.]+)\s*ms\s*)?"
            r"(?:([\d.]+)\s*ms\s*)?"
            r"(?:(\S+)\s*\(?([\d.]+)\)?)?"
        )
        for line in proc.stdout:
            line = line.strip()
            if not line:
                continue
            m = hop_re.match(line)
            if m:
                num = int(m.group(1))
                times = [float(t) for t in [m.group(2), m.group(3), m.group(4)] if t]
                avg = sum(times) / len(times) if times else None
                ip = m.group(6) or m.group(5) or "*"
                hop = {"hop": num, "ip": ip, "avg_ms": avg, "raw": line}
                hops.append(hop)
                if on_hop:
                    on_hop(hop)
        proc.wait()
    except FileNotFoundError:
        hops = [{"hop": 0, "ip": "error", "avg_ms": None, "raw": "traceroute no disponible"}]
    except Exception as e:
        hops = [{"hop": 0, "ip": "error", "avg_ms": None, "raw": str(e)}]
    return hops


# ──────────────────────────────────────────────
# DNS
# ──────────────────────────────────────────────

COMMON_RECORD_TYPES = ["A", "AAAA", "MX", "NS", "TXT", "CNAME", "SOA", "PTR"]


def dns_lookup(domain: str, record_type: str = "A") -> dict:
    """
    Resolución DNS usando nslookup (no requiere dnspython).
    Devuelve dict con result, resolve_ms, raw.
    """
    start = time.monotonic()
    try:
        sys = platform.system().lower()
        if record_type == "PTR":
            cmd = ["nslookup", domain]
        elif sys == "windows":
            cmd = ["nslookup", f"-type={record_type}", domain]
        else:
            cmd = ["nslookup", f"-type={record_type}", domain]

        res = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        elapsed = (time.monotonic() - start) * 1000
        output = res.stdout + res.stderr
        records = _parse_nslookup(output, record_type)
        return {
            "domain": domain,
            "record_type": record_type,
            "result": records,
            "resolve_ms": round(elapsed, 2),
            "raw": output,
            "success": bool(records)
        }
    except subprocess.TimeoutExpired:
        return {"domain": domain, "record_type": record_type, "result": [], "resolve_ms": 5000.0, "raw": "Timeout", "success": False}
    except Exception as e:
        elapsed = (time.monotonic() - start) * 1000
        return {"domain": domain, "record_type": record_type, "result": [], "resolve_ms": round(elapsed, 2), "raw": str(e), "success": False}


def _parse_nslookup(output: str, rtype: str) -> list:
    lines = output.splitlines()
    records = []
    patterns = {
        "A":     r"Address(?:es)?:\s*([\d.]+)",
        "AAAA":  r"Address(?:es)?:\s*([0-9a-f:]+)",
        "MX":    r"mail exchanger\s*=\s*(.+)",
        "NS":    r"nameserver\s*=\s*(.+)",
        "TXT":   r"text\s*=\s*[\"']?(.+?)[\"']?\s*$",
        "CNAME": r"canonical name\s*=\s*(.+)",
        "SOA":   r"primary name server\s*=\s*(.+)",
    }
    pat = patterns.get(rtype, r"Address:\s*(.+)")
    for line in lines:
        m = re.search(pat, line, re.IGNORECASE)
        if m:
            val = m.group(1).strip()
            if val and val not in records:
                records.append(val)
    if not records:
        for line in lines:
            if "Address:" in line and not line.strip().startswith("Server:"):
                parts = line.split(":", 1)
                if len(parts) == 2:
                    val = parts[1].strip()
                    if val and val not in records:
                        records.append(val)
    return records


def resolve_simple(host: str) -> str:
    """Resolución rápida sin nslookup, para uso interno."""
    try:
        return socket.gethostbyname(host)
    except Exception:
        return ""


# ──────────────────────────────────────────────
# ESCÁNER DE PUERTOS
# ──────────────────────────────────────────────

COMMON_PORTS = {
    21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP", 53: "DNS",
    80: "HTTP", 110: "POP3", 143: "IMAP", 443: "HTTPS", 445: "SMB",
    3306: "MySQL", 3389: "RDP", 5432: "PostgreSQL", 5900: "VNC",
    6379: "Redis", 8080: "HTTP-Alt", 8443: "HTTPS-Alt", 27017: "MongoDB",
    1433: "MSSQL", 5000: "Flask/Dev", 8888: "Jupyter", 9200: "Elasticsearch"
}


def scan_ports(host: str, ports: list, timeout: float = 0.5,
               on_result: Optional[Callable] = None) -> list:
    """
    Escanea lista de puertos TCP en paralelo (máx 50 threads).
    on_result(result_dict) callback por puerto.
    """
    results = []
    lock = threading.Lock()
    semaphore = threading.Semaphore(50)

    def scan_one(port):
        with semaphore:
            status = "closed"
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(timeout)
                r = s.connect_ex((host, port))
                s.close()
                status = "open" if r == 0 else "closed"
            except Exception:
                status = "error"
            res = {"port": port, "status": status, "service": COMMON_PORTS.get(port, "")}
            with lock:
                results.append(res)
            if on_result:
                on_result(res)

    threads = [threading.Thread(target=scan_one, args=(p,), daemon=True) for p in ports]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=timeout + 1)

    return sorted(results, key=lambda x: x["port"])


def parse_port_range(port_str: str) -> list:
    """
    Convierte '22,80,443,8000-8100' en lista de ints.
    Limita a 1000 puertos máximo.
    """
    ports = set()
    for part in port_str.split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-", 1)
            try:
                ports.update(range(int(a), int(b) + 1))
            except ValueError:
                pass
        else:
            try:
                ports.add(int(part))
            except ValueError:
                pass
    result = [p for p in sorted(ports) if 1 <= p <= 65535]
    return result[:1000]


# ──────────────────────────────────────────────
# CALCULADORA DE SUBREDES
# ──────────────────────────────────────────────

def subnet_calc(cidr: str) -> dict:
    """
    Calcula info completa de una subred CIDR (ej: '192.168.1.0/24').
    También acepta 'IP mascara' (ej: '192.168.1.0 255.255.255.0').
    """
    try:
        cidr = cidr.strip()
        if " " in cidr:
            ip_str, mask_str = cidr.split(None, 1)
            prefix = _mask_to_prefix(mask_str)
            cidr = f"{ip_str}/{prefix}"

        if "/" not in cidr:
            cidr += "/32"

        ip_str, prefix_str = cidr.split("/")
        prefix = int(prefix_str)

        if not (0 <= prefix <= 32):
            return {"error": "Prefijo fuera de rango (0-32)"}

        ip_int = _ip_to_int(ip_str)
        mask_int = (0xFFFFFFFF << (32 - prefix)) & 0xFFFFFFFF
        network_int = ip_int & mask_int
        broadcast_int = network_int | (~mask_int & 0xFFFFFFFF)
        first_host = network_int + 1 if prefix < 31 else network_int
        last_host = broadcast_int - 1 if prefix < 31 else broadcast_int
        total_hosts = max(0, broadcast_int - network_int - 1) if prefix < 31 else 1

        return {
            "input": cidr,
            "network": _int_to_ip(network_int),
            "broadcast": _int_to_ip(broadcast_int),
            "mask": _int_to_ip(mask_int),
            "wildcard": _int_to_ip(~mask_int & 0xFFFFFFFF),
            "prefix": prefix,
            "first_host": _int_to_ip(first_host),
            "last_host": _int_to_ip(last_host),
            "total_hosts": total_hosts,
            "host_bits": 32 - prefix,
            "ip_class": _ip_class(ip_str),
            "is_private": _is_private(network_int),
            "binary_mask": _int_to_binary(mask_int),
            "binary_network": _int_to_binary(network_int),
            "error": None
        }
    except Exception as e:
        return {"error": f"Formato inválido: {e}"}


def _ip_to_int(ip: str) -> int:
    parts = ip.split(".")
    if len(parts) != 4:
        raise ValueError(f"IP inválida: {ip}")
    return sum(int(p) << (24 - 8 * i) for i, p in enumerate(parts))


def _int_to_ip(n: int) -> str:
    return ".".join(str((n >> (24 - 8 * i)) & 0xFF) for i in range(4))


def _int_to_binary(n: int) -> str:
    return ".".join(f"{(n >> (24 - 8 * i)) & 0xFF:08b}" for i in range(4))


def _mask_to_prefix(mask: str) -> int:
    return bin(_ip_to_int(mask)).count("1")


def _ip_class(ip: str) -> str:
    first = int(ip.split(".")[0])
    if first < 128:
        return "A"
    elif first < 192:
        return "B"
    elif first < 224:
        return "C"
    elif first < 240:
        return "D (Multicast)"
    return "E (Reservada)"


def _is_private(ip_int: int) -> bool:
    private_ranges = [
        (_ip_to_int("10.0.0.0"), _ip_to_int("10.255.255.255")),
        (_ip_to_int("172.16.0.0"), _ip_to_int("172.31.255.255")),
        (_ip_to_int("192.168.0.0"), _ip_to_int("192.168.255.255")),
        (_ip_to_int("127.0.0.0"), _ip_to_int("127.255.255.255")),
    ]
    return any(start <= ip_int <= end for start, end in private_ranges)


# ──────────────────────────────────────────────
# SPEEDTEST (nativo sin librería externa)
# ──────────────────────────────────────────────

def speedtest_native(on_progress: Optional[Callable] = None) -> dict:
    """
    Test de velocidad usando descarga de archivo de prueba real.
    on_progress(phase, value) para updates.
    No requiere speedtest-cli.
    """
    import urllib.request
    import time

    test_files = [
        ("https://speed.cloudflare.com/__down?bytes=25000000", 25_000_000),
        ("https://httpbin.org/bytes/10000000", 10_000_000),
    ]

    # Ping
    if on_progress:
        on_progress("ping", 0)
    ping_ms = _measure_ping("1.1.1.1")

    # Download
    if on_progress:
        on_progress("download", 0)

    download_mbps = 0.0
    for url, expected_bytes in test_files:
        try:
            start = time.monotonic()
            with urllib.request.urlopen(url, timeout=15) as resp:
                downloaded = 0
                chunk_size = 65536
                while True:
                    chunk = resp.read(chunk_size)
                    if not chunk:
                        break
                    downloaded += len(chunk)
                    if on_progress:
                        pct = min(100, int(downloaded / expected_bytes * 100))
                        on_progress("download", pct)
            elapsed = time.monotonic() - start
            if elapsed > 0 and downloaded > 0:
                download_mbps = round((downloaded * 8) / (elapsed * 1_000_000), 2)
                break
        except Exception:
            continue

    # Upload (simulated via POST a httpbin)
    if on_progress:
        on_progress("upload", 0)

    upload_mbps = 0.0
    try:
        import urllib.request
        data = os.urandom(5_000_000)
        req = urllib.request.Request(
            "https://httpbin.org/post",
            data=data,
            method="POST",
            headers={"Content-Type": "application/octet-stream"}
        )
        start = time.monotonic()
        with urllib.request.urlopen(req, timeout=15) as resp:
            resp.read()
        elapsed = time.monotonic() - start
        if elapsed > 0:
            upload_mbps = round((len(data) * 8) / (elapsed * 1_000_000), 2)
        if on_progress:
            on_progress("upload", 100)
    except Exception:
        upload_mbps = 0.0

    return {
        "download_mbps": download_mbps,
        "upload_mbps": upload_mbps,
        "ping_ms": ping_ms,
        "server": "Cloudflare / httpbin.org"
    }


def _measure_ping(host: str) -> float:
    try:
        start = time.monotonic()
        s = socket.create_connection((host, 80), timeout=2)
        s.close()
        return round((time.monotonic() - start) * 1000, 1)
    except Exception:
        return 0.0


# ──────────────────────────────────────────────
# MONITOR HTTP
# ──────────────────────────────────────────────

def check_url(url: str, timeout: int = 5) -> dict:
    """Comprueba disponibilidad de una URL HTTP/HTTPS."""
    import urllib.request
    import urllib.error

    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    start = time.monotonic()
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "VapaNet/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            code = resp.getcode()
        ms = round((time.monotonic() - start) * 1000, 1)
        status = "up" if 200 <= code < 400 else "degraded"
        return {"url": url, "status": status, "code": code, "ms": ms}
    except urllib.error.HTTPError as e:
        ms = round((time.monotonic() - start) * 1000, 1)
        return {"url": url, "status": "degraded", "code": e.code, "ms": ms}
    except Exception as e:
        ms = round((time.monotonic() - start) * 1000, 1)
        return {"url": url, "status": "down", "code": 0, "ms": ms, "error": str(e)}


# ──────────────────────────────────────────────
# WHOIS (básico sin librería)
# ──────────────────────────────────────────────

def whois_lookup(domain: str) -> dict:
    """Consulta WHOIS básica por socket TCP al puerto 43."""
    tld = domain.split(".")[-1].lower()
    servers = {
        "com": "whois.verisign-grs.com",
        "net": "whois.verisign-grs.com",
        "org": "whois.pir.org",
        "es":  "whois.nic.es",
        "io":  "whois.nic.io",
        "dev": "whois.nic.google",
        "app": "whois.nic.google",
    }
    server = servers.get(tld, "whois.iana.org")

    start = time.monotonic()
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        s.connect((server, 43))
        s.sendall(f"{domain}\r\n".encode())
        response = b""
        while True:
            data = s.recv(4096)
            if not data:
                break
            response += data
        s.close()
        ms = round((time.monotonic() - start) * 1000, 1)
        text = response.decode("utf-8", errors="replace")
        return {"domain": domain, "server": server, "raw": text, "ms": ms, "success": True}
    except Exception as e:
        ms = round((time.monotonic() - start) * 1000, 1)
        return {"domain": domain, "server": server, "raw": str(e), "ms": ms, "success": False}


# ──────────────────────────────────────────────
# BATCH PING
# ──────────────────────────────────────────────

def batch_ping(hosts: list, count: int = 2, timeout: int = 1,
               on_result: Optional[Callable] = None) -> list:
    """
    Ping en paralelo a lista de hosts.
    on_result(result_dict) callback por host.
    """
    results = []
    lock = threading.Lock()
    semaphore = threading.Semaphore(20)

    def do_ping(host):
        with semaphore:
            host = host.strip()
            if not host or host.startswith("#"):
                return
            res = ping_host(host, count=count, timeout=timeout)
            with lock:
                results.append(res)
            if on_result:
                on_result(res)

    threads = [threading.Thread(target=do_ping, args=(h,), daemon=True) for h in hosts]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=count * (timeout + 3) + 5)

    return results


def parse_hosts_file(content: str) -> list:
    """Parsea texto con hosts (uno por línea, # como comentario)."""
    hosts = []
    for line in content.splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            hosts.append(line.split()[0])
    return list(dict.fromkeys(hosts))


# ──────────────────────────────────────────────
# ESCÁNER LOCAL DE RED
# ──────────────────────────────────────────────

def discover_local_hosts(network_prefix: str, on_found: Optional[Callable] = None) -> list:
    """
    Descubre hosts activos en un /24 (ej: '192.168.1').
    Usa ping rápido con 1 paquete.
    """
    found = []
    lock = threading.Lock()
    semaphore = threading.Semaphore(50)

    def probe(ip):
        with semaphore:
            res = ping_host(ip, count=1, timeout=1)
            if res["status"] == "up":
                hostname = ""
                try:
                    hostname = socket.gethostbyaddr(ip)[0]
                except Exception:
                    pass
                entry = {"ip": ip, "hostname": hostname, "ms": res["avg_ms"]}
                with lock:
                    found.append(entry)
                if on_found:
                    on_found(entry)

    threads = []
    for i in range(1, 255):
        ip = f"{network_prefix}.{i}"
        t = threading.Thread(target=probe, args=(ip,), daemon=True)
        threads.append(t)
        t.start()

    for t in threads:
        t.join(timeout=30)

    return sorted(found, key=lambda x: int(x["ip"].split(".")[-1]))


def get_local_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"
