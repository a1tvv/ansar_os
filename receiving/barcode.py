"""
Генерация настоящего штрихкода EAN-13 в виде SVG.

Зачем не картинкой и не библиотекой: этикетки печатаются на складе,
где интернета может не быть, а лишняя зависимость — лишний риск при
деплое. Здесь чистый Python + SVG, работает всегда.

Раньше полоски рисовались "на глаз" — красиво, но сканер такое не читает.
Теперь кодировка настоящая, по стандарту EAN-13.
"""

# Таблицы кодирования EAN-13
_L = {'0': '0001101', '1': '0011001', '2': '0010011', '3': '0111101', '4': '0100011',
      '5': '0110001', '6': '0101111', '7': '0111011', '8': '0110111', '9': '0001011'}
_G = {'0': '0100111', '1': '0110011', '2': '0011011', '3': '0100001', '4': '0011101',
      '5': '0111001', '6': '0000101', '7': '0010001', '8': '0001001', '9': '0010111'}
_R = {'0': '1110010', '1': '1100110', '2': '1101100', '3': '1000010', '4': '1011100',
      '5': '1001110', '6': '1010000', '7': '1000100', '8': '1001000', '9': '1110100'}
# Какая половина первой группы кодируется таблицей G — задаётся первой цифрой
_PARITY = {
    '0': 'LLLLLL', '1': 'LLGLGG', '2': 'LLGGLG', '3': 'LLGGGL', '4': 'LGLLGG',
    '5': 'LGGLLG', '6': 'LGGGLL', '7': 'LGLGLG', '8': 'LGLGGL', '9': 'LGGLGL',
}


def ean13_checksum(digits12: str) -> str:
    """Контрольная цифра: нечётные позиции ×1, чётные ×3."""
    total = sum(int(d) * (3 if i % 2 else 1) for i, d in enumerate(digits12))
    return str((10 - total % 10) % 10)


def normalize(code: str) -> str | None:
    """
    Приводит штрихкод к 13 цифрам. Возвращает None, если это не EAN-13
    (например, внутренний артикул или пустое поле) — тогда рисовать
    штрихкод нельзя, и шаблон покажет только текст.
    """
    if not code:
        return None
    digits = ''.join(ch for ch in str(code) if ch.isdigit())
    if len(digits) == 12:
        return digits + ean13_checksum(digits)
    if len(digits) == 13:
        # если контрольная цифра неверна — пересчитываем, чтобы код был валиден
        return digits[:12] + ean13_checksum(digits[:12])
    return None


def ean13_modules(code13: str) -> str:
    """Строка из 95 модулей: '1' — чёрная полоса, '0' — пробел."""
    first, left, right = code13[0], code13[1:7], code13[7:]
    pattern = _PARITY[first]
    out = ['101']                                   # стартовый маркер
    for ch, p in zip(left, pattern):
        out.append(_L[ch] if p == 'L' else _G[ch])
    out.append('01010')                             # центральный маркер
    for ch in right:
        out.append(_R[ch])
    out.append('101')                               # конечный маркер
    return ''.join(out)


def ean13_svg(code: str, width_mm: float = 22, height_mm: float = 12) -> str | None:
    """
    Готовый SVG со штрихкодом и подписью цифрами.
    Ширина одного модуля = width_mm / 95 — так штрихкод всегда
    вписывается в отведённое место и остаётся пропорциональным.
    """
    code13 = normalize(code)
    if not code13:
        return None

    modules = ean13_modules(code13)
    mw = width_mm / 95.0
    bar_h = height_mm - 3.2          # снизу оставляем место под цифры
    guard_h = height_mm - 1.6        # маркеры чуть длиннее — как в стандарте
    guard_pos = set(range(0, 3)) | set(range(45, 50)) | set(range(92, 95))

    rects = []
    for i, m in enumerate(modules):
        if m == '1':
            h = guard_h if i in guard_pos else bar_h
            rects.append(
                f'<rect x="{i * mw:.3f}" y="0" width="{mw:.3f}" height="{h:.2f}" fill="#000"/>'
            )

    fs = min(2.6, width_mm / 9)
    text = (
        f'<text x="0" y="{height_mm - 0.3:.2f}" font-size="{fs:.2f}" '
        f'font-family="monospace" fill="#000">{code13[0]}</text>'
        f'<text x="{3 * mw + (42 * mw) / 2:.2f}" y="{height_mm - 0.3:.2f}" font-size="{fs:.2f}" '
        f'font-family="monospace" fill="#000" text-anchor="middle" letter-spacing="0.4">{code13[1:7]}</text>'
        f'<text x="{50 * mw + (42 * mw) / 2:.2f}" y="{height_mm - 0.3:.2f}" font-size="{fs:.2f}" '
        f'font-family="monospace" fill="#000" text-anchor="middle" letter-spacing="0.4">{code13[7:]}</text>'
    )
    return (
        f'<svg viewBox="0 0 {width_mm} {height_mm}" width="{width_mm}mm" height="{height_mm}mm" '
        f'xmlns="http://www.w3.org/2000/svg">{"".join(rects)}{text}</svg>'
    )
