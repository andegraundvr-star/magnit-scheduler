# src/services/utils.py
import pandas as pd
from datetime import datetime
import os
from typing import Dict, Any

def save_to_network_folder(results: dict):
    """
    Сохраняет все DataFrame в Excel файл в сетевую папку
    """
    import pandas as pd
    from datetime import datetime

    # Создаем имя файла с timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"PAO_Magnit_{timestamp}.xlsx"

    # Путь к сетевой папке
    network_path = r"\\vra.local\root\Public\ОИС\ПАО_Магнит"

    # Полный путь к файлу
    full_path = os.path.join(network_path, filename)

    try:
        # Создаем Excel writer
        with pd.ExcelWriter(full_path, engine='openpyxl') as writer:
            # Коды проблем
            if 'problems' in results and 'problem_codes' in results['problems']:
                problems_df = pd.DataFrame(results['problems']['problem_codes'])
                problems_df.to_excel(writer, sheet_name='Problems', index=False)
                print(f" Problems сохранены ({len(problems_df)} строк)")

            # Сигналы
            if 'signals' in results and 'signals' in results['signals']:
                signals_df = pd.DataFrame(results['signals']['signals'])
                if not signals_df.empty:
                    signals_df.to_excel(writer, sheet_name='Signals', index=False)
                    print(f" Signals сохранены ({len(signals_df)} строк)")
                else:
                    # ДОБАВЛЕНО: Записываем информацию о пустых сигналах
                    empty_signals_df = pd.DataFrame([{
                        'info': 'Сигналы не получены',
                        'дата_проверки': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        'статус': 'Требуется уточнение endpoint у контрагента'
                    }])
                    empty_signals_df.to_excel(writer, sheet_name='Signals', index=False)
                    print(" Signals: записана информация об отсутствии данных")

            # Мерчандайзеры
            if 'merchandisers' in results:
                merchandisers = results['merchandisers']
                if isinstance(merchandisers, dict) and 'merchandisers' in merchandisers:
                    merchandisers_df = pd.DataFrame(merchandisers['merchandisers'])
                else:
                    merchandisers_df = pd.DataFrame([merchandisers])
                merchandisers_df.to_excel(writer, sheet_name='Merchandisers', index=False)
                print(f" Merchandisers сохранены ({len(merchandisers_df)} строк)")

        print(f" Файл сохранен: {full_path}")

        # ДОБАВЛЕНО: Записываем лог проблемы с сигналами
        log_problem_with_signals()

        return full_path

    except Exception as e:
        print(f" Ошибка сохранения файла: {e}")
        # ... остальной код обработки ошибок

def log_problem_with_signals():
    """Логирует проблему с получением сигналов"""
    log_entry = {
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'problem': 'Сигналы не получаются через API',
        'status': 'endpoint /signals/{date} возвращает пустой список',
        'action_required': 'Уточнить у контрагента правильный endpoint и параметры'
    }

    # Сохраняем в отдельный лог-файл
    log_filename = f"signal_problem_log_{datetime.now().strftime('%Y%m%d')}.txt"
    with open(log_filename, 'a', encoding='utf-8') as f:
        f.write(f"{log_entry}\n")

    print(" Проблема с сигналами записана в лог")
def process_results(results: dict):
    """
    Обрабатывает результаты и выводит статистику
    """
    print("\n" + "="*60)
    print(" ОБРАБОТКА РЕЗУЛЬТАТОВ")
    print("="*60)

    # Коды проблем
    if 'problems' in results:
        problems = results['problems']
        if 'problem_codes' in problems:
            problem_count = len(problems['problem_codes'])
            print(f" Коды проблем: {problem_count} записей")

    # Сигналы
    if 'signals' in results:
        signals = results['signals']
        if isinstance(signals, dict) and 'signals' in signals:
            signal_count = len(signals['signals'])
            print(f" Сигналы: {signal_count}")

            if signal_count > 0:
                print(" Примеры сигналов:")
                for i, signal in enumerate(signals['signals'][:3]):
                    shop_code = signal.get('shop_code', 'N/A')
                    problem_code = signal.get('problem_code', 'N/A')
                    product_name = signal.get('product_name', 'N/A')[:50]
                    print(f"   {i+1}. Магазин {shop_code}, Проблема: {problem_code}")
                    print(f"      Товар: {product_name}...")
        else:
            print(f" Сигналы: {signals}")

    # Мерчандайзеры
    if 'merchandisers' in results:
        merchandisers = results['merchandisers']
        if isinstance(merchandisers, dict) and 'merchandisers' in merchandisers:
            merch_count = len(merchandisers['merchandisers'])
            print(f" Мерчандайзеры: {merch_count} записей")
        else:
            print(" Мерчандайзеры: получены")

    # Результаты создания графиков
    if 'schedule' in results:
        schedule_count = len(results['schedule'])
        success_schedule = sum(1 for item in results['schedule']
                               if 'Данные отправлены на загрузку' in str(item.get('result', '')))
        print(f" Создание графиков: {success_schedule}/{schedule_count} успешно")

    # Результаты удаления
    if 'delete_result' in results:
        delete_count = len(results['delete_result'])
        success_delete = sum(1 for item in results['delete_result']
                             if 'Данные отправлены на удаление' in str(item.get('result', '')))
        print(f" Удаление графиков: {success_delete}/{delete_count} успешно")

    # Сохранение в сетевую папку
    save_to_network_folder(results)

#что это за функция надо разобраться
def prepare_signal_data(
        shop_code: str,
        shop_name: str,
        product_code: str,
        product_name: str,
        is_available: bool,
        is_virtual_rest_risk: bool,
        amount_virtual_rest_detected: int,
        is_product_missing: bool,
        is_expiration_date_exceeded: bool
) -> Dict[str, Any]:
    """Подготовка данных сигнала для отправки"""
    return {
        "shop_code": shop_code,
        "shop_name": shop_name,
        "product_code": product_code,
        "product_name": product_name,
        "is_available": is_available,
        "is_virtual_rest_risk": is_virtual_rest_risk,
        "amount_virtual_rest_detected": amount_virtual_rest_detected,
        "is_product_missing": is_product_missing,
        "is_expiration_date_exceeded": is_expiration_date_exceeded,
        "timestamp": datetime.now().isoformat()
    }