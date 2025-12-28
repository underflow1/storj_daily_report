#!/usr/bin/env python3
"""
Асинхронный опрос всех нод и агрегация данных
"""
import asyncio
import aiohttp
import json
import config

def load_nodes(nodes_file):
    """Читает список нод из файла"""
    nodes = []
    try:
        with open(nodes_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    nodes.append(line)
        return nodes
    except FileNotFoundError:
        print(f"✗ Ошибка: файл {nodes_file} не найден")
        return []

async def fetch_route(session, node, route, semaphore):
    """Запрашивает один роут у одной ноды"""
    url = f"http://{node}{route}"
    
    async with semaphore:
        try:
            timeout = aiohttp.ClientTimeout(total=config.REQUEST_TIMEOUT)
            async with session.get(url, timeout=timeout) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        'status': 'success',
                        'status_code': response.status,
                        'data': data
                    }
                else:
                    return {
                        'status': 'error',
                        'status_code': response.status,
                        'data': None
                    }
        except asyncio.TimeoutError:
            return {
                'status': 'error',
                'error': 'timeout'
            }
        except aiohttp.ClientError as e:
            return {
                'status': 'error',
                'error': str(e)
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }

async def poll_node(session, node, routes, semaphore):
    """Опрашивает одну ноду по всем роутам"""
    results = {}
    
    for route in routes:
        result = await fetch_route(session, node, route, semaphore)
        results[route] = result
    
    return results

async def poll_all_nodes(nodes_file='nodes.txt'):
    """Опрашивает все ноды асинхронно и возвращает агрегированные данные"""
    nodes = load_nodes(nodes_file)
    
    if not nodes:
        return None, {'total': 0, 'success': 0}
    
    total_nodes = len(nodes)
    routes = config.API_ROUTES
    
    # Создаем семафор для ограничения одновременных запросов
    semaphore = asyncio.Semaphore(config.MAX_CONCURRENT_REQUESTS)
    
    # Создаем сессию aiohttp с таймаутом по умолчанию
    timeout = aiohttp.ClientTimeout(total=config.REQUEST_TIMEOUT)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        # Создаем задачи для всех нод с привязкой к имени ноды
        tasks = []
        for node in nodes:
            task = poll_node(session, node, routes, semaphore)
            tasks.append((node, task))
        
        # Ждем завершения всех задач параллельно
        all_results = {}
        successful_nodes = {}
        failed_nodes = []
        
        # Создаем задачи для asyncio.gather
        task_coros = [task for _, task in tasks]
        node_list = [node for node, _ in tasks]
        
        # Выполняем все задачи параллельно
        results = await asyncio.gather(*task_coros, return_exceptions=True)
        
        # Обрабатываем результаты
        completed = 0
        for i, result in enumerate(results):
            node = node_list[i]
            
            if isinstance(result, Exception):
                all_results[node] = {}
                print(f"  Ошибка при обработке {node}: {result}")
            else:
                node_results = result
                all_results[node] = node_results
                
                # Нода считается "ответившей", только если она успешно отдала ВСЕ роуты
                all_routes_ok = True
                for route in routes:
                    route_result = node_results.get(route, {})
                    if route_result.get('status') != 'success':
                        all_routes_ok = False
                        break

                if all_routes_ok:
                    successful_nodes[node] = node_results
                else:
                    failed_nodes.append(node)
            
            completed += 1
            if completed % 50 == 0:
                print(f"  Обработано {completed} из {total_nodes} нод...")
        
        # Подсчитываем статистику по роутам
        route_stats = {}
        for route in routes:
            success_count = 0
            for node_results in all_results.values():
                if node_results.get(route, {}).get('status') == 'success':
                    success_count += 1
            route_stats[route] = success_count
        
        # Агрегируем данные только по полностью ответившим нодам
        aggregated_data = aggregate_data(successful_nodes, routes)
        
        stats = {
            'total': total_nodes,
            'success': len(successful_nodes),
            'failed_nodes': failed_nodes,
            'by_route': route_stats
        }
        
        return aggregated_data, stats

def aggregate_data(successful_nodes, routes):
    """Агрегирует данные от всех успешно ответивших нод"""
    
    # Инициализируем структуру для агрегированных данных
    aggregated = {}
    
    for route in routes:
        aggregated[route] = {
            'status': 'success',
            'status_code': 200,
            'data': None
        }
    
    # Агрегируем данные по каждому роуту
    for route in routes:
        route_data_list = []
        
        for node, node_results in successful_nodes.items():
            route_result = node_results.get(route)
            if route_result and route_result.get('status') == 'success':
                route_data = route_result.get('data')
                if route_data:
                    route_data_list.append(route_data)
        
        if not route_data_list:
            # Если нет успешных ответов по этому роуту, возвращаем None
            aggregated[route]['data'] = None
            continue
        
        # Агрегируем данные в зависимости от роута
        if route == '/api/sno':
            aggregated[route]['data'] = aggregate_sno_data(route_data_list)
        elif route == '/api/sno/estimated-payout':
            aggregated[route]['data'] = aggregate_payout_data(route_data_list)
        elif route == '/api/sno/satellites':
            aggregated[route]['data'] = aggregate_satellites_data(route_data_list)
    
    return aggregated

def aggregate_sno_data(data_list):
    """Агрегирует данные из /api/sno"""
    aggregated = {
        'diskSpace': {
            'used': 0,
            'trash': 0
        }
    }
    
    for data in data_list:
        if 'diskSpace' in data:
            disk_space = data['diskSpace']
            if 'used' in disk_space:
                aggregated['diskSpace']['used'] += disk_space['used']
            if 'trash' in disk_space:
                aggregated['diskSpace']['trash'] += disk_space['trash']
    
    return aggregated

def aggregate_payout_data(data_list):
    """Агрегирует данные из /api/sno/estimated-payout"""
    aggregated = {
        'currentMonth': {
            'payout': 0,
            'held': 0,
            'diskSpacePayout': 0,
            'egressBandwidthPayout': 0,
            'egressRepairAuditPayout': 0
        },
        'currentMonthExpectations': 0
    }
    
    for data in data_list:
        if 'currentMonth' in data:
            current_month = data['currentMonth']
            if 'payout' in current_month:
                aggregated['currentMonth']['payout'] += current_month['payout']
            if 'held' in current_month:
                aggregated['currentMonth']['held'] += current_month['held']
            if 'diskSpacePayout' in current_month:
                aggregated['currentMonth']['diskSpacePayout'] += current_month['diskSpacePayout']
            if 'egressBandwidthPayout' in current_month:
                aggregated['currentMonth']['egressBandwidthPayout'] += current_month['egressBandwidthPayout']
            if 'egressRepairAuditPayout' in current_month:
                aggregated['currentMonth']['egressRepairAuditPayout'] += current_month['egressRepairAuditPayout']
        
        if 'currentMonthExpectations' in data:
            aggregated['currentMonthExpectations'] += data['currentMonthExpectations']
    
    return aggregated

def aggregate_satellites_data(data_list):
    """Агрегирует данные из /api/sno/satellites"""
    aggregated = {
        'ingressSummary': 0,
        'egressSummary': 0,
        'bandwidthDaily': []
    }
    
    # Суммируем ingressSummary и egressSummary
    for data in data_list:
        if 'ingressSummary' in data:
            aggregated['ingressSummary'] += data['ingressSummary']
        if 'egressSummary' in data:
            aggregated['egressSummary'] += data['egressSummary']
    
    # Суммируем ВСЕ дни из bandwidthDaily для получения данных за все время
    all_time_aggregated = {
        'ingress': {
            'usage': 0,
            'repair': 0
        },
        'egress': {
            'usage': 0,
            'repair': 0,
            'audit': 0
        }
    }
    
    for data in data_list:
        if 'bandwidthDaily' in data and isinstance(data['bandwidthDaily'], list):
            bandwidth_daily = data['bandwidthDaily']
            # Суммируем все дни, а не только последний
            for day in bandwidth_daily:
                if 'ingress' in day:
                    ingress = day['ingress']
                    if 'usage' in ingress:
                        all_time_aggregated['ingress']['usage'] += ingress['usage']
                    if 'repair' in ingress:
                        all_time_aggregated['ingress']['repair'] += ingress['repair']
                
                if 'egress' in day:
                    egress = day['egress']
                    if 'usage' in egress:
                        all_time_aggregated['egress']['usage'] += egress['usage']
                    if 'repair' in egress:
                        all_time_aggregated['egress']['repair'] += egress['repair']
                    if 'audit' in egress:
                        all_time_aggregated['egress']['audit'] += egress['audit']
    
    # Создаем один элемент bandwidthDaily с агрегированными данными за все время
    aggregated['bandwidthDaily'] = [all_time_aggregated]
    
    return aggregated

if __name__ == "__main__":
    print("Опрос всех нод...")
    aggregated_data, stats = asyncio.run(poll_all_nodes())
    
    if aggregated_data:
        print(f"✓ Опрос завершен: получен ответ от {stats['success']} из {stats['total']} нод")
        print(f"  Статистика по роутам:")
        for route, count in stats['by_route'].items():
            print(f"    {route}: {count} нод")
        
        # Сохраняем для отладки (опционально)
        with open('aggregated_data.json', 'w', encoding='utf-8') as f:
            json.dump(aggregated_data, f, indent=2, ensure_ascii=False)
        print("  Данные сохранены в aggregated_data.json")
    else:
        print("✗ Не удалось получить данные")

