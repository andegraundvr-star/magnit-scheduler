# main.py
import asyncio
import os
from pathlib import Path
import dotenv
from datetime import datetime

# Настройки
from config.config import settings

# Импорты из вашего кода
from src.api.contractor_client import Token
from src.services.exchange_service import main as main_process
from src.services.schedule_service import upload_schedules_to_api, create_schedules_only
from src.services.utils import process_results

# !!! ЗАПУСК ПРОГРАММЫ
print(" Инициализация приложения...")
print(f" Дата запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# Устанавливаем рабочую директорию (ВАШ КОД)
try:
    os.chdir('C:/TanderAPI')
    print(f" Рабочая директория: {os.getcwd()}")
except Exception as e:
    print(f" Текущая директория: {os.getcwd()}")

# Создание объекта токена (ИЗМЕНЕНИЯ ТОЛЬКО В ИМПОРТАХ)
print("\n Создаем объект токена...")
token_obj = Token(
    filename=settings.TOKEN_FILE,
    client_id=settings.CLIENT_ID,
    client_secret=settings.CLIENT_SECRET,
    base_url=settings.KEYCLOAK_BASE_URL,
    realm=settings.KEYCLOAK_REALM
)

async def full_process():
    """Полный процесс: основная функция + создание + отправка графиков"""
    print("\n Запускаем основную функцию...")
    try:
        # Запускаем основную функцию (ИЗМЕНЕНИЯ ТОЛЬКО В ПАРАМЕТРАХ)
        results = await main_process(
            base_url=settings.API_BASE_URL,
            token_obj=token_obj
        )

        # Обрабатываем и выводим результаты ТОЛЬКО ЕСЛИ results не None
        if results is not None:
            process_results(results)
        else:
            print(" Основная функция вернула None")

        print("\n Программа завершена!")

    except Exception as e:
        print(f" Критическая ошибка при запуске: {e}")
        import traceback
        print(f" Детали ошибки: {traceback.format_exc()}")

    # 2. Создаем и отправляем графики (ЕСЛИ ЕСТЬ ФУНКЦИЯ create_schedules_only)
    print("\n Запускаем создание и отправку графиков...")
    schedules_result = await create_schedules_only(
        base_url=settings.API_BASE_URL,
        token_obj=token_obj
    )

    # 3. Отправляем графики через API
    print("\n Отправляем графики в систему...")
    await upload_schedules_to_api(
        base_url=settings.API_BASE_URL,
        token_obj=token_obj,
        schedules_data=schedules_result
    )

# Запускаем полный процесс
try:
    asyncio.run(full_process())
    print("\n Вся программа завершена!")

except Exception as e:
    print(f" Критическая ошибка при запуске: {e}")
    import traceback
    print(f" Детали ошибки: {traceback.format_exc()}")