# sensors.py
import config as C
import controller as ctrl  # ctrl.rs 재사용

PIN_ULTRA_FRONT = 2     # 디지털 2
PIN_IR_LEFT     = 13    # 디지털 13
PIN_IR_RIGHT    = 12    # 디지털 12

_LOG = False  # 필요할 때 True로

def _norm(v: int) -> int:
    """보드 반환값 v를 C.IR_ACTIVE 기준으로 0/1 정규화 (1=장애물)"""
    try:
        return 1 if int(v) == int(getattr(C, "IR_ACTIVE", 1)) else 0
    except Exception:
        return 0


def read_ultra_front() -> int:
    try:
        raw = ctrl.rs.digital_read(PIN_ULTRA_FRONT)
        val = _norm(raw)
        if _LOG: print(f"[SENS] UF raw={raw} -> {val}")
        return val
    except Exception:
        return 0

def read_ir_left() -> int:
    try:
        raw = ctrl.rs.digital_read(PIN_IR_LEFT)
        val = _norm(raw)
        if _LOG: print(f"[SENS] IL raw={raw} -> {val}")
        return val
    except Exception:
        return 0

def read_ir_right() -> int:
    try:
        raw = ctrl.rs.digital_read(PIN_IR_RIGHT)
        val = _norm(raw)
        if _LOG: print(f"[SENS] IR raw={raw} -> {val}")
        return val
    except Exception:
        return 0

def read_proximity():
    """(ultra_front, ir_left, ir_right)  각 0/1 리턴"""
    uf = read_ultra_front()
    il = read_ir_left()
    ir = read_ir_right()
    if _LOG: print(f"[SENS] prox=(UF:{uf}, L:{il}, R:{ir})")
    return uf, il, ir