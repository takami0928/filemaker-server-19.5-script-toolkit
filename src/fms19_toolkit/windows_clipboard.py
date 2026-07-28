from __future__ import annotations

import ctypes
from ctypes import wintypes
import re
import struct
import sys
import time
import xml.etree.ElementTree as ET

from .snippet import strip_xml_declaration, validate_snippet_text

GMEM_MOVEABLE = 0x0002
DEFAULT_FORMAT = "Mac-XMSS"


def _require_windows() -> None:
    if sys.platform != "win32":
        raise RuntimeError("FileMaker clipboard operations require native Windows Python")


def _api():
    _require_windows()
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

    user32.OpenClipboard.argtypes = [wintypes.HWND]
    user32.OpenClipboard.restype = wintypes.BOOL
    user32.CloseClipboard.argtypes = []
    user32.CloseClipboard.restype = wintypes.BOOL
    user32.EmptyClipboard.argtypes = []
    user32.EmptyClipboard.restype = wintypes.BOOL
    user32.RegisterClipboardFormatW.argtypes = [wintypes.LPCWSTR]
    user32.RegisterClipboardFormatW.restype = wintypes.UINT
    user32.SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]
    user32.SetClipboardData.restype = wintypes.HANDLE
    user32.GetClipboardData.argtypes = [wintypes.UINT]
    user32.GetClipboardData.restype = wintypes.HANDLE
    user32.EnumClipboardFormats.argtypes = [wintypes.UINT]
    user32.EnumClipboardFormats.restype = wintypes.UINT
    user32.GetClipboardFormatNameW.argtypes = [wintypes.UINT, wintypes.LPWSTR, ctypes.c_int]
    user32.GetClipboardFormatNameW.restype = ctypes.c_int

    kernel32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
    kernel32.GlobalAlloc.restype = wintypes.HGLOBAL
    kernel32.GlobalLock.argtypes = [wintypes.HGLOBAL]
    kernel32.GlobalLock.restype = wintypes.LPVOID
    kernel32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
    kernel32.GlobalUnlock.restype = wintypes.BOOL
    kernel32.GlobalFree.argtypes = [wintypes.HGLOBAL]
    kernel32.GlobalFree.restype = wintypes.HGLOBAL
    kernel32.GlobalSize.argtypes = [wintypes.HGLOBAL]
    kernel32.GlobalSize.restype = ctypes.c_size_t
    return user32, kernel32



def _open_clipboard(user32, attempts: int = 10, delay_seconds: float = 0.05) -> None:
    last_error = 0
    for _ in range(attempts):
        if user32.OpenClipboard(None):
            return
        last_error = ctypes.get_last_error()
        time.sleep(delay_seconds)
    raise ctypes.WinError(last_error)


def build_windows_payload(xml_text: str) -> bytes:
    errors = [f for f in validate_snippet_text(xml_text) if f.severity == "error"]
    if errors:
        raise ValueError("invalid fmxmlsnippet: " + "; ".join(f.message for f in errors))
    clean = strip_xml_declaration(xml_text).strip()
    xml_bytes = clean.encode("utf-8")
    return struct.pack("<I", len(xml_bytes)) + xml_bytes


def parse_windows_payload(payload: bytes) -> str:
    if len(payload) < 4:
        raise ValueError("clipboard payload is too short")
    expected = struct.unpack("<I", payload[:4])[0]
    body = payload[4:]
    if expected > len(body):
        raise ValueError(f"length prefix {expected} exceeds payload body {len(body)}")
    # GlobalAlloc can expose trailing zero bytes; honor the length prefix.
    text = body[:expected].decode("utf-8")
    ET.fromstring(text)
    return text


def write_xml(xml_text: str, format_name: str = DEFAULT_FORMAT) -> None:
    if not re.fullmatch(r"[A-Za-z0-9_-]+", format_name):
        raise ValueError("format name contains unsupported characters")
    payload = build_windows_payload(xml_text)
    user32, kernel32 = _api()
    fmt = user32.RegisterClipboardFormatW(format_name)
    if not fmt:
        raise ctypes.WinError(ctypes.get_last_error())
    _open_clipboard(user32)

    handle = None
    try:
        if not user32.EmptyClipboard():
            raise ctypes.WinError(ctypes.get_last_error())
        handle = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(payload))
        if not handle:
            raise ctypes.WinError(ctypes.get_last_error())
        pointer = kernel32.GlobalLock(handle)
        if not pointer:
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            ctypes.memmove(pointer, payload, len(payload))
        finally:
            kernel32.GlobalUnlock(handle)
        if not user32.SetClipboardData(fmt, handle):
            raise ctypes.WinError(ctypes.get_last_error())
        # Clipboard owns the handle after SetClipboardData succeeds.
        handle = None
    finally:
        user32.CloseClipboard()
        if handle:
            kernel32.GlobalFree(handle)


def read_xml(format_name: str = DEFAULT_FORMAT) -> str:
    user32, kernel32 = _api()
    fmt = user32.RegisterClipboardFormatW(format_name)
    if not fmt:
        raise ctypes.WinError(ctypes.get_last_error())
    _open_clipboard(user32)
    try:
        handle = user32.GetClipboardData(fmt)
        if not handle:
            raise RuntimeError(f"clipboard does not contain {format_name}")
        size = kernel32.GlobalSize(handle)
        pointer = kernel32.GlobalLock(handle)
        if not pointer:
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            payload = ctypes.string_at(pointer, size)
        finally:
            kernel32.GlobalUnlock(handle)
    finally:
        user32.CloseClipboard()
    return parse_windows_payload(payload)


def detect_formats() -> list[tuple[int, str]]:
    user32, _ = _api()
    _open_clipboard(user32)
    found: list[tuple[int, str]] = []
    try:
        current = 0
        while True:
            current = user32.EnumClipboardFormats(current)
            if current == 0:
                break
            buffer = ctypes.create_unicode_buffer(256)
            length = user32.GetClipboardFormatNameW(current, buffer, len(buffer))
            if length:
                found.append((current, buffer.value))
    finally:
        user32.CloseClipboard()
    return found
