# src/services/exchange_service.py
import asyncio
import httpx
from datetime import datetime, timezone, date, timedelta
from typing import Dict, Any, Optional
import pandas as pd

from src.api.contractor_client import Token, API
from src.services.utils import process_results
async def main(base_url: str, token_obj: Token) -> dict:
    """Основная функция БЕЗ создания графиков - только получение данных"""
    print(" Запуск основной функции (без создания графиков)...")
    print(f"    Базовый URL API: {base_url}")
    # Создаем клиент и API
    async with httpx.AsyncClient(base_url=base_url, verify=False, timeout=30.0) as client:
        api = API(client=client)
        token = await token_obj.get_token()
        date_of_visit_shop = datetime.now(tz=timezone.utc).date()

        results = {}

        try:
            # 1.  Получаем коды проблем
            print("\n1.  Получаем коды проблем...")
            results['problems'] = await api.get_problems_codes(token=token)
            print(f"    Получено {len(results['problems'].get('problem_codes', []))} кодов проблем")

            # 2.  Получаем список мерчандайзеров
            print("\n2.  Получаем список мерчандайзеров...")
            results['merchandisers'] = await api.get_merchandisers(token=token)
            print("    Мерчандайзеры получены")

            # 3.  Получаем сигналы за несколько дат
            print("\n3.  Получаем сигналы за последние 3 дня...")
            all_signals = []

            dates_to_check = [
                date_of_visit_shop,
                date_of_visit_shop - timedelta(days=1),
                date_of_visit_shop - timedelta(days=2)
            ]

            for check_date in dates_to_check:
                print(f"    Проверяем дату {check_date}...")

                signals_data = await api.get_signals(
                    token=token,
                    dt=check_date,
                    limit=100,
                    offset=0
                )

                # ДИАГНОСТИКА: выводим полный ответ API
                print(f"       Ответ API: {signals_data}")

                # Проверяем разные возможные структуры ответа
                if isinstance(signals_data, dict):
                    print(f"       Тип ответа: dict, ключи: {list(signals_data.keys())}")

                    # Проверяем разные возможные ключи
                    if 'signals' in signals_data:
                        signals_list = signals_data['signals']
                        print(f"       Найдено сигналов в 'signals': {len(signals_list) if signals_list else 0}")
                    elif 'data' in signals_data:
                        signals_list = signals_data['data']
                        print(f"       Найдено сигналов в 'data': {len(signals_list) if signals_list else 0}")
                    elif 'items' in signals_data:
                        signals_list = signals_data['items']
                        print(f"       Найдено сигналов в 'items': {len(signals_list) if signals_list else 0}")
                    else:
                        print(f"       Другие ключи в ответе: {signals_data}")
                        signals_list = []
                else:
                    print(f"      ️  Неожиданный тип ответа: {type(signals_data)}")
                    signals_list = []

                # Обрабатываем найденные сигналы
                if signals_list:
                    for signal in signals_list[:3]:  # Показываем только первые 3 для примера
                        shop_code = signal.get('shop_code', 'N/A')
                        problem_code = signal.get('problem_code', 'N/A')
                        product_name = signal.get('product_name', 'N/A')
                        print(f"          Пример сигнала: Магазин {shop_code}, Проблема {problem_code}, Товар: {product_name}")

                    # Добавляем дату запроса к каждому сигналу
                    for signal in signals_list:
                        signal['request_date'] = str(check_date)
                    all_signals.extend(signals_list)
                    print(f"       Добавлено {len(signals_list)} сигналов")
                else:
                    print(f"       Сигналов нет для даты {check_date}")

            print(f"    Всего собрано сигналов: {len(all_signals)}")
            results['signals'] = {'signals': all_signals}

            # ВОЗВРАЩАЕМ РЕЗУЛЬТАТЫ ПРИ УСПЕШНОМ ВЫПОЛНЕНИИ
            return results

        except Exception as e:
            print(f" Ошибка в main: {e}")
            import traceback
            print(f" Детали ошибки: {traceback.format_exc()}")
            # Возвращаем пустые результаты при ошибке
            return results
