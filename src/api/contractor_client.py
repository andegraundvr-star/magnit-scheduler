# src/api/contractor_client.py
import httpx
from datetime import datetime, timezone, date
import json
import jwt
import aiofiles
from typing import Optional, Dict, Any, List
import asyncio
from pathlib import Path
import anyio



class Token:
    def __init__(
            self, filename: str, client_id: str, client_secret: str, base_url: str, realm: str,
    ) -> None:
        self.token = None
        self.expired_timestamp = None
        self.filename = filename
        self.client_id = client_id
        self.client_secret = client_secret
        self.openid_url = f"{base_url}/auth/realms/{realm}/.well-known/openid-configuration"

    async def _is_token_valid(self) -> bool:
        """Проверка что токен сохраненный в памяти валидный"""
        try:
            timestamp_now = int(datetime.now(tz=timezone.utc).timestamp())
            return self.expired_timestamp and self.expired_timestamp > timestamp_now + 20
        except Exception as e:
            print(f" Ошибка проверки токена: {e}")
            return False

    async def _read_token_from_file(self, filename: str) -> Optional[str]:
        """Достаем токен из файла если токен существует и он валидный"""
        try:
            file_path = anyio.Path(filename)
            if await file_path.exists():
                async with aiofiles.open(filename, 'r') as file:
                    content = json.loads(await file.read())

                current_time = int(datetime.now(tz=timezone.utc).timestamp())
                if content.get("expired_timestamp", 0) > current_time + 20:
                    return content["token"]
            return None
        except Exception as e:
            print(f" Ошибка чтения токена из файла: {e}")
            return None

    async def _fetch_new_token(self, client_id: str, client_secret: str, openid_url: str) -> str:
        """Запрос нового токена из KeyCloak"""
        try:
            async with httpx.AsyncClient(verify=False) as client:
                print(" Получаем конфигурацию OpenID...")
                response = await client.get(url=openid_url)
                response.raise_for_status()

                token_url = response.json().get("token_endpoint")
                data = {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "grant_type": "client_credentials",
                }
                print(" Запрашиваем новый токен...")
                response = await client.post(token_url, data=data)
                response.raise_for_status()

                token_data = response.json()
                return token_data.get("access_token")
        except Exception as e:
            print(f" Ошибка получения токена: {e}")
            raise

    async def _save_token_to_file(self, filename: str) -> None:
        """Сохранение токена и expired_timestamp в файл"""
        try:
            async with aiofiles.open(filename, "w") as file:
                data = {
                    "expired_timestamp": self.expired_timestamp,
                    "token": self.token,
                    "last_update": int(datetime.now(tz=timezone.utc).timestamp())
                }
                await file.write(json.dumps(data, indent=4, ensure_ascii=False))
            print(" Токен сохранен в файл")
        except Exception as e:
            print(f" Ошибка сохранения токена: {e}")

    async def get_token(self) -> str:
        """Получаем токен"""
        print(" Получение токена...")

        if await self._is_token_valid():
            print(" Токен из памяти")
            return self.token

        token_from_file = await self._read_token_from_file(self.filename)
        if token_from_file:
            print(" Токен из файла")
            self.token = token_from_file
            return self.token

        print("Запрос нового токена...")
        self.token = await self._fetch_new_token(self.client_id, self.client_secret, self.openid_url)

        try:
            decoded_token = jwt.decode(self.token, options={"verify_signature": False})
            self.expired_timestamp = decoded_token.get('exp')
            print(f" Токен истекает: {datetime.fromtimestamp(self.expired_timestamp)}")
        except Exception as e:
            print(f" Не удалось декодировать токен: {e}")
            self.expired_timestamp = int(datetime.now(tz=timezone.utc).timestamp()) + 3600

        await self._save_token_to_file(self.filename)
        print(" Новый токен получен и сохранен")
        return self.token
class API:
    def __init__(self, client: httpx.AsyncClient) -> None:
        self.client = client

    async def get_problems_codes(self, token: str):
        """Получение коды проблем"""
        try:
            headers = {"User-Agent": "API Client", "Authorization": f"Bearer {token}"}
            # ВАЖНО: используем переданного клиента (уже с verify=False)
            response: httpx.Response = await self.client.get(url="/problems/codes", headers=headers)
            print(f" Status Code: {response.status_code}")  # ← ДОБАВЬТЕ ЛОГИРОВАНИЕ
            if response.status_code == 200:
                return response.json()
            print(f" Ошибка API: {response.text}")  # ← ЛОГИРУЙТЕ ОШИБКИ
            return response.text
        except Exception as e:
            print(f" Ошибка получения кодов проблем: {e}")
            return f"Error: {e}"

    async def get_merchandisers(self, token: str):
        """Получение списка мерчандайзеров"""
        try:
            headers = {"User-Agent": "API Client", "Authorization": f"Bearer {token}"}
            response: httpx.Response = await self.client.get(url="/merchandisers", headers=headers)
            if response.status_code == 200:
                return response.json()
            return response.text
        except Exception as e:
            print(f" Ошибка получения мерчандайзеров: {e}")
            return f"Error: {e}"

    async def post_merchandisers_schedules(self, token: str, dt: date, shops_data: list = None):
        """Загрузка графиков посещения мерчандайзеров для нескольких магазинов"""
        try:
            headers = {"User-Agent": "API Client", "Authorization": f"Bearer {token}"}

            # Если не переданы данные магазинов, используем стандартные
            if shops_data is None:
                shops_data = [
                    ("993610", "Борисоглебск 1 Матросовская (а)"),
                    ("993613", "Борисоглебск 2 Матросовская (а)"),
                    ("993611", "Воронеж 3 Ростовская (а)"),
                    ("993617", "Воронеж 4 (а)"),
                    ("993614", "Воронеж 5 (а)"),
                    ("994802", "Елец 1 Радиотехническая"),
                    ("994601", "Курск 2 Кулакова (а)"),
                    ("993609", "Лиски 1 Титова (а)"),
                    ("993602", "Нововоронеж 1 Первомайская (а)"),
                    ("997110", "Новомосковск 2 Кукунина"),
                    ("993606", "Россошь 1 Простеева (а)"),
                    ("993608", "Россошь 2 Труда (а)"),
                    ("993101", "Старый Оскол 1 Молодежный (а)"),
                    ("993107", "Старый Оскол 2 Олимпийский (а)"),
                    ("996801", "Тамбов 1 Советская"),
                    ("997108", "Тула 2 Сойфера")
                ]

            data = {
                "schedules": [
                    {
                        "date": dt.strftime("%Y-%m-%d"),
                        "shop_code": code,
                        "shop_name": name,
                        "merch_name": "",
                        "merch_phone": "",
                        "duration": 30,
                        "agency": "",
                        "gr20": ""
                    }
                    for code, name in shops_data
                ]
            }

            response: httpx.Response = await self.client.post(
                url="/merchandisers/schedules",
                headers=headers,
                json=data
            )

            print(f"Status Code: {response.status_code}")

            if response.status_code == 200:
                print(" Успешная загрузка графиков")
                return response.json()
            else:
                print(f" Ошибка: {response.status_code}")
                print(f"Детали: {response.text}")
                return {"error": f"HTTP {response.status_code}"}

        except Exception as e:
            print(f" Исключение при загрузке графиков: {e}")
            return {"error": str(e)}
    async def delete_merchandisers_schedules(self, token: str, dt: date, shop_code: str):
        """Удаление графиков посещения мерчандайзеров"""
        try:
            headers = {"User-Agent": "API Client", "Authorization": f"Bearer {token}"}
            response: httpx.Response = await self.client.delete(
                url=f"/merchandisers/schedules/{str(dt)}/{str(shop_code)}",
                headers=headers
            )
            if response.status_code == 200:
                return response.json()
            return response.text
        except Exception as e:
            print(f" Ошибка удаления графика: {e}")
            return f"Error: {e}"

    async def get_signals(self, token: str, dt: date, limit: int, offset: int):
        """Получение сигналов - с правильным базовым URL"""
        try:
            headers = {
                "User-Agent": "API Client",
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            params = {"limit": limit, "offset": offset}

            print(f" ЗАПРОС СИГНАЛОВ:")
            print(f"   Базовый URL: {self.client.base_url}")
            print(f"   Дата: {dt}")
            print(f"   Limit: {limit}")
            print(f"   Offset: {offset}")

            # Основной endpoint
            url = f"/signals/{dt}"
            print(f"    Пробуем URL: {url}")

            response: httpx.Response = await self.client.get(
                url=url,
                params=params,
                headers=headers,
                timeout=30.0
            )

            print(f"    Статус: {response.status_code}")
            print(f"    Полный URL запроса: {response.url}")

            if response.status_code == 200:
                data = response.json()
                signal_count = len(data.get('signals', []))
                print(f"    УСПЕХ! Найдено сигналов: {signal_count}")

                if signal_count > 0:
                    # Показываем примеры сигналов
                    for i, signal in enumerate(data['signals'][:3]):
                        shop_code = signal.get('shop_code', 'N/A')
                        product_name = signal.get('product_name', 'N/A')[:50]
                        print(f"       Сигнал {i+1}: магазин {shop_code}, товар: {product_name}...")

                return data
            else:
                print(f"    Ошибка: {response.status_code}")
                print(f"    Текст ответа: {response.text}")
                return {"signals": []}

        except Exception as e:
            print(f"    Исключение: {e}")
            return {"signals": []}
    async def post_signals(self, token: str, signals_data: list):
        """Отправка сигналов о посещении мерчандайзеров"""
        try:
            headers = {
                "User-Agent": "API Client",
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }

            # Формируем данные для отправки
            data = {
                "signals": signals_data
            }

            print(f" Отправка {len(signals_data)} сигналов...")
            print(f" Данные: {data}")

            response: httpx.Response = await self.client.post(
                url="/signals",  # Возможно endpoint будет другой, уточните!
                headers=headers,
                json=data,
                timeout=30.0
            )

            print(f" Статус ответа: {response.status_code}")
            print(f" Текст ответа: {response.text}")

            if response.status_code == 200:
                print(" Сигналы успешно отправлены")
                return response.json()
            elif response.status_code == 201:
                print(" Сигналы успешно созданы")
                return response.json()
            else:
                print(f" Ошибка при отправке сигналов: {response.status_code}")
                return {"error": f"HTTP {response.status_code}", "details": response.text}

        except Exception as e:
            print(f" Исключение при отправке сигналов: {e}")
            return {"error": str(e)}