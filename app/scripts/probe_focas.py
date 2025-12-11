import sys
import os
import ctypes
import platform
from pathlib import Path

"""
=== FOCAS PROBE TOOL ===
Ferramenta de diagnóstico isolada para validar conectividade FOCAS.
Uso: python probe_focas.py [IP_DA_MAQUINA]

Requisitos:
- Python 3.x
- Fwlib32.dll ou Fwlib64.dll na pasta ../fanuc-driver/
- Rede configurada e pingando para o IP alvo.

Códigos de Retorno Comuns:
 0: Sucesso (EW_OK)
-1: Busy (EW_BUSY)
-8: Handle Error (EW_HANDLE) - Verifique se já há conexões demais.
-15: DLL Error (EW_DLL) - DLL não encontrada ou incompatível.
-16: Socket Error (EW_SOCKET) - Erro de Rede/Porta/Firewall.
"""

# ODBST Structure for cnc_statinfo (Simplified)
class ODBST(ctypes.Structure):
    _fields_ = [
        ("dummy", ctypes.c_short), 
        ("type", ctypes.c_short),  # 0: M series, 1: T series
        ("const", ctypes.c_short), # Max controlled axes
        ("ext_no", ctypes.c_short),# Number of external axes
        ("axis", ctypes.c_short),  # Number of controlled axes
        ("mach", ctypes.c_short),  # CNC type
        ("series", ctypes.c_short),# CNC series
        ("version", ctypes.c_short),# CNC version
        ("dummy2", ctypes.c_short),
    ]

def get_focas_error_msg(ret):
    errors = {
        -16: "EW_SOCKET (Socket Error - Check IP/Port/Firewall)",
        -15: "EW_DLL (DLL Error - Check version/path)",
        -8:  "EW_HANDLE (Handle Error - Connection lost or not open)",
        -1:  "EW_BUSY (CNC Busy)",
        0:   "EW_OK (Success)"
    }
    return errors.get(ret, f"Unknown Error ({ret})")

def probe_focas(ip="192.168.1.1", port=8193, timeout=10):
    print(f"=== FOCAS Probe Tool (StdCall) ===")
    print(f"Target: {ip}:{port} (Timeout: {timeout}s)")
    
    arch = platform.architecture()[0]
    print(f"Python Architecture: {arch}")
    
    dll_name = "Fwlib64.dll" if "64" in arch else "Fwlib32.dll"
    base_dir = Path(__file__).resolve().parent.parent.parent
    dll_path = base_dir / "fanuc-driver" / dll_name
    
    if not dll_path.exists():
        print(f"[CRITICAL] DLL not found at {dll_path}")
        return

    print(f"Loading DLL: {dll_path}")
    try:
        # IMPORTANT: Use WinDLL for __stdcall convention (Windows/FOCAS standard)
        # cdll is for __cdecl and might fail or corrupt stack.
        focas = ctypes.WinDLL(str(dll_path))
    except OSError as e:
        print(f"[CRITICAL] Failed to load DLL: {e}")
        print("Tip: Ensure Visual C++ Redistributables are installed.")
        return

    # --- Define Signatures (ArgTypes) ---
    # short cnc_allclibhndl3(const char *ip, unsigned short port, long timeout, long *FlibHndl);
    focas.cnc_allclibhndl3.argtypes = [ctypes.c_char_p, ctypes.c_ushort, ctypes.c_long, ctypes.POINTER(ctypes.c_long)]
    focas.cnc_allclibhndl3.restype = ctypes.c_short
    
    # short cnc_freelibhndl(long FlibHndl);
    focas.cnc_freelibhndl.argtypes = [ctypes.c_long]
    focas.cnc_freelibhndl.restype = ctypes.c_short
    
    # short cnc_statinfo(long FlibHndl, ODBST *statinfo);
    focas.cnc_statinfo.argtypes = [ctypes.c_long, ctypes.POINTER(ODBST)]
    focas.cnc_statinfo.restype = ctypes.c_short

    # --- Connection ---
    lib_handle = ctypes.c_long(0)
    ip_bytes = ip.encode('ascii')
    
    print(f"1. Connecting to {ip}...")
    ret = focas.cnc_allclibhndl3(ip_bytes, port, timeout, ctypes.byref(lib_handle))
    
    if ret == 0:
        print(f"[SUCCESS] Connected! Handle: {lib_handle.value}")
        
        # --- Read Status (Real Data Proof) ---
        print("2. Reading CNC Status (cnc_statinfo)...")
        stat = ODBST()
        ret_stat = focas.cnc_statinfo(lib_handle, ctypes.byref(stat))
        
        if ret_stat == 0:
            print(f"[SUCCESS] Read Status OK!")
            print(f"   Axes: {stat.axis}")
            print(f"   Series: {stat.series}")
            print(f"   Version: {stat.version}")
            print(f"   Type: {'T Series (Lathe)' if stat.type == 1 else 'M Series (Milling)' if stat.type == 0 else 'Unknown'}")
        else:
            print(f"[FAIL] Connected but failed to read status: {get_focas_error_msg(ret_stat)}")

        # --- Disconnect ---
        print("3. Disconnecting...")
        focas.cnc_freelibhndl(lib_handle)
        print("[DONE] Session closed.")
    else:
        print(f"[FAIL] Connection failed: {get_focas_error_msg(ret)}")
        print("Check: IP Ping, Port 8193, Firewall, Physical Cable, Valid FOCAS License.")

if __name__ == "__main__":
    target_ip = sys.argv[1] if len(sys.argv) > 1 else "192.168.1.1"
    probe_focas(ip=target_ip)
