#!/usr/bin/env python3
"""
Главный скрипт для генерации ежедневного отчета:
1. Опрашивает все ноды асинхронно
2. Агрегирует данные
3. Генерирует SVG из шаблона
4. Конвертирует SVG в PNG
5. Отправляет в Telegram
"""
import asyncio
import os
import uuid
import tempfile
import sys

# Добавляем папку lib в путь для импорта модулей
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'lib'))

import config
from poll_all_nodes import poll_all_nodes
from generate_from_svg import generate_svg_from_data
from svg_to_png import svg_to_png
from telegram_sender import send_to_telegram

def build_telegram_caption(stats):
    """Собирает caption для Telegram с учетом лимита 1024 символа."""
    def node_name_only(node):
        # nodes.txt у нас обычно в формате host:port, для caption нужен только host
        if not node:
            return node
        s = str(node).strip()
        # [ipv6]:port
        if s.startswith('[') and ']' in s:
            return s[1:s.index(']')]
        # host:port (или ipv4:port)
        if ':' in s:
            left, right = s.rsplit(':', 1)
            if right.isdigit():
                return left
        return s

    success_count = stats.get('success', 0)
    total_count = stats.get('total', 0)
    failed_nodes = stats.get('failed_nodes', []) or []

    if success_count >= total_count:
        return None

    if not failed_nodes:
        return None

    # Формат:
    # не получен ответ от X нод:
    # node101
    # node202
    # ...
    failed_count = total_count - success_count
    header = f"не получен ответ от {failed_count} нод:"
    # Телега: caption до 1024 символов — оставим небольшой запас
    max_len = 1000

    lines = [header]
    shown_count = 0

    for node in failed_nodes:
        name = node_name_only(node)
        candidate_lines = lines + [name]
        candidate_caption = "\n".join(candidate_lines)
        if len(candidate_caption) > max_len:
            break
        lines.append(name)
        shown_count += 1

    remaining = len(failed_nodes) - shown_count
    if remaining > 0:
        tail = f"... (+{remaining} more)"
        candidate_caption = "\n".join(lines + [tail])
        if len(candidate_caption) <= 1024:
            lines.append(tail)

    return "\n".join(lines)

def main():
    # Всегда работаем из папки проекта, чтобы относительные пути были стабильны
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    # Используем системную папку temp
    temp_dir = tempfile.gettempdir()

    # Генерируем UUID v4 для имен файлов
    file_uuid = str(uuid.uuid4())

    template_file = getattr(config, 'TEMPLATE_PATH', 'templates/default/index.svg')
    nodes_file = getattr(config, 'NODES_FILE', 'nodes.txt')
    output_svg = os.path.join(temp_dir, f"{file_uuid}.svg")
    output_png = os.path.join(temp_dir, f"{file_uuid}.png")
    
    print("=" * 60)
    print("Генерация ежедневного отчета Storj")
    print("=" * 60)
    
    # Шаг 1: Опрос всех нод
    print("\n1. Опрос всех нод...")
    aggregated_data, stats = asyncio.run(poll_all_nodes(nodes_file=nodes_file))
    
    if not aggregated_data:
        print("✗ Не удалось получить данные от нод")
        return False
    
    success_count = stats['success']
    total_count = stats['total']
    
    print(f"✓ Опрос завершен: получен ответ от {success_count} из {total_count} нод")
    
    # Проверяем, что есть данные для генерации карточки
    sno_data = aggregated_data.get('/api/sno', {}).get('data')
    payout_data = aggregated_data.get('/api/sno/estimated-payout', {}).get('data')
    satellites_data = aggregated_data.get('/api/sno/satellites', {}).get('data')
    
    if not sno_data or not payout_data or not satellites_data:
        print("✗ Недостаточно данных для генерации карточки")
        print(f"  /api/sno: {'✓' if sno_data else '✗'}")
        print(f"  /api/sno/estimated-payout: {'✓' if payout_data else '✗'}")
        print(f"  /api/sno/satellites: {'✓' if satellites_data else '✗'}")
        return False
    
    # Шаг 2: Генерация SVG
    print(f"\n2. Генерация SVG из шаблона {template_file}...")
    try:
        generate_svg_from_data(aggregated_data, template_file, output_svg, stats=stats)
        print(f"✓ SVG сохранен: {output_svg}")
    except Exception as e:
        print(f"✗ Ошибка при генерации SVG: {e}")
        return False
    
    # Шаг 3: Конвертация SVG в PNG
    print(f"\n3. Конвертация SVG в PNG...")
    if not svg_to_png(output_svg, output_png):
        print("✗ Не удалось сгенерировать PNG")
        return False
    
    # Шаг 4: Отправка в Telegram
    print(f"\n4. Отправка в Telegram...")
    
    # Формируем текст к картинке, если не все ноды ответили
    caption = build_telegram_caption(stats)
    
    if not send_to_telegram(output_png, caption):
        print("✗ Не удалось отправить в Telegram")
        return False
    
    print("\n" + "=" * 60)
    print("✓ Отчет успешно сгенерирован и отправлен!")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)

