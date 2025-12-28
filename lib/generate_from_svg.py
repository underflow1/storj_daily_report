#!/usr/bin/env python3
"""
Генерация отчета из SVG шаблона: SVG → PNG
"""
import json
import math
import os
import sys
from datetime import datetime

# Импорт из той же папки
sys.path.insert(0, os.path.dirname(__file__))
from svg_to_png import svg_to_png

def bytes_to_gb(bytes_value):
    """Конвертирует байты в GB"""
    return bytes_value / (1000 ** 3)  # Основание 10

def format_storage_gb(gb_value):
    """Форматирует значение: максимум трехзначные числа, округление до сотых, конвертирует в более крупные единицы при необходимости (основание 10)"""
    if gb_value < 1000:
        return f"{round(gb_value, 2):.2f}", "GB"
    elif gb_value < 1000000:
        tb_value = gb_value / 1000
        if tb_value < 1000:
            return f"{round(tb_value, 2):.2f}", "TB"
        else:
            pb_value = tb_value / 1000
            return f"{round(pb_value, 2):.2f}", "PB"
    else:
        pb_value = gb_value / 1000000
        return f"{round(pb_value, 2):.2f}", "PB"

def cents_to_dollars(cents_value):
    """Конвертирует центы в доллары"""
    return cents_value / 100

def load_node_data(json_file):
    """Загружает данные ноды из JSON файла"""
    with open(json_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def generate_svg_from_data(data, template_file, output_svg_file, stats=None):
    """Генерирует SVG из шаблона с подстановкой данных"""
    
    # Читаем шаблон
    with open(template_file, 'r', encoding='utf-8') as f:
        svg_content = f.read()
    
    # Извлекаем данные из API ответов
    sno_data = data['/api/sno']['data']
    payout_data = data['/api/sno/estimated-payout']['data']
    satellites_data = data['/api/sno/satellites']['data']
    
    # Получаем последний элемент bandwidthDaily
    bandwidth_daily = satellites_data['bandwidthDaily']
    last_day = bandwidth_daily[-1] if bandwidth_daily else {}
    
    # === ЗАГОЛОВОК ===
    current_date = datetime.now().strftime('%d.%m.%Y')
    svg_content = svg_content.replace('{{strDateCurrent}}', current_date)

    # Статистика по нодам (для заголовка)
    nodes_success = None
    nodes_total = None
    if stats:
        nodes_success = stats.get('success')
        nodes_total = stats.get('total')

    if nodes_success is None:
        nodes_success = 0
    if nodes_total is None:
        nodes_total = 0

    # Количество нод всегда красным цветом
    svg_content = svg_content.replace('{{strHeaderNodesSuccess}}', str(nodes_success))
    svg_content = svg_content.replace('{{strHeaderNodesTotal}}', str(nodes_total))
    
    # === EARNINGS ===
    paid = round(cents_to_dollars(payout_data['currentMonth']['payout']), 2)
    held = round(cents_to_dollars(payout_data['currentMonth']['held']), 2)
    total_expected = round(cents_to_dollars(payout_data['currentMonthExpectations']), 2)
    
    storage_earnings = round(cents_to_dollars(payout_data['currentMonth']['diskSpacePayout']), 2)
    egress_earnings = round(cents_to_dollars(payout_data['currentMonth']['egressBandwidthPayout']), 2)
    repair_audit_earnings = round(cents_to_dollars(payout_data['currentMonth']['egressRepairAuditPayout']), 2)
    
    # Заменяем значения earnings
    svg_content = svg_content.replace('{{fltEarningsPaid}}', f'{paid:.2f}')
    svg_content = svg_content.replace('{{fltEarningsHeld}}', f'{held:.2f}')
    svg_content = svg_content.replace('{{fltEarningsTotalExpected}}', f'{total_expected:.2f}')
    svg_content = svg_content.replace('{{fltEarningsStorage}}', f'{storage_earnings:.2f}')
    svg_content = svg_content.replace('{{fltEarningsEgress}}', f'{egress_earnings:.2f}')
    svg_content = svg_content.replace('{{fltEarningsRepairAudit}}', f'{repair_audit_earnings:.2f}')
    
    # Вычисляем ширины полос earnings
    bar_width = 880
    storage_width = int((storage_earnings / total_expected) * bar_width) if total_expected > 0 else 0
    egress_width = int((egress_earnings / total_expected) * bar_width) if total_expected > 0 else 0
    repair_audit_width = int((repair_audit_earnings / total_expected) * bar_width) if total_expected > 0 else 0
    held_width = int((held / total_expected) * bar_width) if total_expected > 0 else 0
    
    # Вычисляем X координаты
    egress_x = 22 + storage_width
    repair_audit_x = 22 + storage_width + egress_width
    held_x = 22 + storage_width + egress_width + repair_audit_width
    
    # Заменяем ширины и координаты earnings
    svg_content = svg_content.replace('{{intEarningsBarWidthStorage}}', str(storage_width))
    svg_content = svg_content.replace('{{intEarningsBarWidthEgress}}', str(egress_width))
    svg_content = svg_content.replace('{{intEarningsBarWidthRepairAudit}}', str(repair_audit_width))
    svg_content = svg_content.replace('{{intEarningsBarWidthHeld}}', str(held_width))
    svg_content = svg_content.replace('{{intEarningsBarXEgress}}', str(egress_x))
    svg_content = svg_content.replace('{{intEarningsBarXRepairAudit}}', str(repair_audit_x))
    svg_content = svg_content.replace('{{intEarningsBarXHeld}}', str(held_x))
    
    # === STORAGE ===
    storage_used = bytes_to_gb(sno_data['diskSpace']['used'])
    storage_trash = bytes_to_gb(sno_data['diskSpace']['trash'])
    storage_total = storage_used + storage_trash
    
    storage_total_value, storage_total_unit = format_storage_gb(storage_total)
    storage_used_value, storage_used_unit = format_storage_gb(storage_used)
    storage_trash_value, storage_trash_unit = format_storage_gb(storage_trash)
    
    # Вычисляем процент trash от used
    storage_trash_percent = round((storage_trash / storage_used) * 100, 2) if storage_used > 0 else 0.0
    
    # Заменяем значения storage
    svg_content = svg_content.replace('{{strStorageTotalValue}}', storage_total_value)
    svg_content = svg_content.replace('{{strStorageTotalUnit}}', storage_total_unit)
    svg_content = svg_content.replace('{{strStorageUsedValue}}', storage_used_value)
    svg_content = svg_content.replace('{{strStorageUsedUnit}}', storage_used_unit)
    svg_content = svg_content.replace('{{strStorageTrashValue}}', storage_trash_value)
    svg_content = svg_content.replace('{{strStorageTrashUnit}}', storage_trash_unit)
    svg_content = svg_content.replace('{{fltStorageTrashPercent}}', f'{storage_trash_percent:.2f}')
    
    # Вычисляем ширины полос storage
    storage_bar_width = 880
    used_width = int((storage_used / storage_total) * storage_bar_width) if storage_total > 0 else 0
    trash_width = storage_bar_width - used_width
    trash_x = 22 + used_width
    
    svg_content = svg_content.replace('{{intStorageBarWidthUsed}}', str(used_width))
    svg_content = svg_content.replace('{{intStorageBarWidthTrash}}', str(trash_width))
    svg_content = svg_content.replace('{{intStorageBarXTrash}}', str(trash_x))
    
    # === BANDWIDTH ===
    # Данные за все время (суммируются все дни из bandwidthDaily)
    ingress_usage = bytes_to_gb(last_day.get('ingress', {}).get('usage', 0))
    ingress_repair = bytes_to_gb(last_day.get('ingress', {}).get('repair', 0))
    egress_usage = bytes_to_gb(last_day.get('egress', {}).get('usage', 0))
    egress_repair = bytes_to_gb(last_day.get('egress', {}).get('repair', 0))
    egress_audit = bytes_to_gb(last_day.get('egress', {}).get('audit', 0))
    egress_repair_audit_total = egress_repair + egress_audit
    
    # Total для заголовка - сумма за все время
    ingress_total = ingress_usage + ingress_repair
    egress_total = egress_usage + egress_repair_audit_total
    
    ingress_total_value, ingress_total_unit = format_storage_gb(ingress_total)
    egress_total_value, egress_total_unit = format_storage_gb(egress_total)
    ingress_usage_value, ingress_usage_unit = format_storage_gb(ingress_usage)
    ingress_repair_value, ingress_repair_unit = format_storage_gb(ingress_repair)
    egress_usage_value, egress_usage_unit = format_storage_gb(egress_usage)
    egress_repair_audit_value, egress_repair_audit_unit = format_storage_gb(egress_repair_audit_total)
    
    # Вычисляем общий total (ingress + egress)
    bandwidth_total = ingress_total + egress_total
    bandwidth_total_value, bandwidth_total_unit = format_storage_gb(bandwidth_total)
    
    # Заменяем значения bandwidth
    svg_content = svg_content.replace('{{strBandwidthIngressTotalValue}}', ingress_total_value)
    svg_content = svg_content.replace('{{strBandwidthIngressTotalUnit}}', ingress_total_unit)
    svg_content = svg_content.replace('{{strBandwidthEgressTotalValue}}', egress_total_value)
    svg_content = svg_content.replace('{{strBandwidthEgressTotalUnit}}', egress_total_unit)
    svg_content = svg_content.replace('{{strBandwidthIngressUsageValue}}', ingress_usage_value)
    svg_content = svg_content.replace('{{strBandwidthIngressUsageUnit}}', ingress_usage_unit)
    svg_content = svg_content.replace('{{strBandwidthIngressRepairValue}}', ingress_repair_value)
    svg_content = svg_content.replace('{{strBandwidthIngressRepairUnit}}', ingress_repair_unit)
    svg_content = svg_content.replace('{{strBandwidthEgressUsageValue}}', egress_usage_value)
    svg_content = svg_content.replace('{{strBandwidthEgressUsageUnit}}', egress_usage_unit)
    svg_content = svg_content.replace('{{strBandwidthEgressRepairAuditValue}}', egress_repair_audit_value)
    svg_content = svg_content.replace('{{strBandwidthEgressRepairAuditUnit}}', egress_repair_audit_unit)
    svg_content = svg_content.replace('{{strBandwidthTotalValue}}', bandwidth_total_value)
    svg_content = svg_content.replace('{{strBandwidthTotalUnit}}', bandwidth_total_unit)
    
    # Вычисляем ширины полос bandwidth
    bandwidth_bar_width = 713
    ingress_total_for_bar = ingress_usage + ingress_repair
    ingress_usage_width = int((ingress_usage / ingress_total_for_bar) * bandwidth_bar_width) if ingress_total_for_bar > 0 else 0
    ingress_repair_width = int((ingress_repair / ingress_total_for_bar) * bandwidth_bar_width) if ingress_total_for_bar > 0 else 0
    
    egress_total_for_bar = egress_usage + egress_repair_audit_total
    egress_usage_width = int((egress_usage / egress_total_for_bar) * bandwidth_bar_width) if egress_total_for_bar > 0 else 0
    egress_repair_audit_width = int((egress_repair_audit_total / egress_total_for_bar) * bandwidth_bar_width) if egress_total_for_bar > 0 else 0
    
    ingress_repair_x = 189 + ingress_usage_width
    egress_repair_audit_x = 189 + egress_usage_width
    
    svg_content = svg_content.replace('{{intBandwidthBarWidthIngressUsage}}', str(ingress_usage_width))
    svg_content = svg_content.replace('{{intBandwidthBarWidthIngressRepair}}', str(ingress_repair_width))
    svg_content = svg_content.replace('{{intBandwidthBarWidthEgressUsage}}', str(egress_usage_width))
    svg_content = svg_content.replace('{{intBandwidthBarWidthEgressRepairAudit}}', str(egress_repair_audit_width))
    svg_content = svg_content.replace('{{intBandwidthBarXIngressRepair}}', str(ingress_repair_x))
    svg_content = svg_content.replace('{{intBandwidthBarXEgressRepairAudit}}', str(egress_repair_audit_x))
    
    # Вычисляем углы для круговой диаграммы
    total_bandwidth = ingress_total + egress_total
    if total_bandwidth > 0:
        ingress_angle_deg = (ingress_total / total_bandwidth * 360)
    else:
        ingress_angle_deg = 0
    
    radius = 66
    ingress_angle_rad = math.radians(ingress_angle_deg)
    ingress_end_x = radius * math.sin(ingress_angle_rad)
    ingress_end_y = -radius * math.cos(ingress_angle_rad)
    
    large_arc = 1 if ingress_angle_deg > 180 else 0
    
    ingress_path = f'M 0 0 L 0 -{radius} A {radius} {radius} 0 {large_arc} 1 {ingress_end_x:.2f} {ingress_end_y:.2f} Z'
    egress_path = f'M 0 0 L {ingress_end_x:.2f} {ingress_end_y:.2f} A {radius} {radius} 0 {1 - large_arc if ingress_angle_deg < 180 else 0} 1 0 -{radius} Z'
    
    svg_content = svg_content.replace('{{strBandwidthPiePathIngress}}', ingress_path)
    svg_content = svg_content.replace('{{strBandwidthPiePathEgress}}', egress_path)
    
    # Сохраняем SVG
    with open(output_svg_file, 'w', encoding='utf-8') as f:
        f.write(svg_content)
    
    return True

if __name__ == "__main__":
    template_file = "templates/default/index.svg"
    json_file = "node101_api_results.json"
    output_svg = "storj_card_generated.svg"
    output_png = "storj_card_generated.png"
    
    print(f"Загрузка данных из {json_file}...")
    data = load_node_data(json_file)
    
    print(f"Генерация SVG из шаблона {template_file}...")
    generate_svg_from_data(data, template_file, output_svg)
    
    print(f"Генерация PNG из {output_svg}...")
    svg_to_png(output_svg, output_png)
    
    print("✓ Готово!")

