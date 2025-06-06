import requests
import time
import logging
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler('test_service.log'),
        logging.StreamHandler()  # Также выводим в консоль
    ]
)

# Поместим несколько взаимодействий для пользователя
recommendations_url = "http://127.0.0.1:8000"
events_store_url = "http://127.0.0.1:8020"
headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}

def log_response(action: str, response):
    """Логирует результат запроса"""
    if response.status_code == 200:
        logging.info(f"{action} - Успешно: {response.json()}")
    else:
        logging.error(f"{action} - Ошибка {response.status_code}: {response.text}")

# Взаимодействие пользователя с айтемом
def add_event(user_id: int, item_id: int):
    params = {"user_id": user_id, "item_id": item_id}
    resp = requests.post(events_store_url + "/put", headers=headers, params=params)
    log_response(f"Добавление события (user={user_id}, item={item_id})", resp)

# Получение взаимодействий пользователя
def get_user_events(user_id: int):
    params = {"user_id": user_id}
    resp = requests.post(events_store_url + "/get", headers=headers, params=params)
    log_response(f"Получение событий пользователя {user_id}", resp)

# Онлайн-рекомендации
def get_online_user_recommendations(user_id: int, k=100):
    params = {"user_id": user_id, 'k': k}
    resp = requests.post(recommendations_url + "/recommendations_online", headers=headers, params=params)
    log_response(f"Онлайн-рекомендации для пользователя {user_id} (k={k})", resp)

# Смешанные рекомендации
def get_all_user_recs(user_id, k):
    params = {"user_id": user_id, 'k': k}
    
    resp_offline = requests.post(recommendations_url + "/recommendations_offline", headers=headers, params=params)
    resp_online = requests.post(recommendations_url + "/recommendations_online", headers=headers, params=params)
    resp_blended = requests.post(recommendations_url + "/recommendations", headers=headers, params=params)

    log_response(f"Офлайн-рекомендации для пользователя {user_id}", resp_offline)
    log_response(f"Онлайн-рекомендации для пользователя {user_id}", resp_online)
    log_response(f"Смешанные рекомендации для пользователя {user_id}", resp_blended)

# Получаем все рекомендации для пользователя
def compute_recs(user_id, is_events=False):
    logging.info("="*50)
    logging.info(f"Начало тестирования в {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logging.info("="*50)

    if is_events:
        # Взаимодействия
        add_event(user_id, 78194999)
        time.sleep(0.1)
        add_event(user_id, 84099295)
        time.sleep(0.1)
        add_event(user_id, 100736375)
        time.sleep(0.1)
        add_event(user_id, 33307667)
        time.sleep(0.1)

    # Проверка событий
    get_user_events(user_id)
    time.sleep(0.1)

    # Онлайн-рекомендации
    get_online_user_recommendations(user_id, k=5)

    # Все рекомендации
    logging.info("\nПолучение всех рекомендаций:")
    get_all_user_recs(user_id, 5)

    logging.info("="*50)
    logging.info(f"Тестирование завершено в {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logging.info("="*50)

if __name__ == "__main__":
    # Как персональные, так и онлайн рекомендации
    compute_recs(26, is_events=True)
    # Только персональные рекомендации
    compute_recs(76, is_events=False)
    # Только онлайн рекомендации, без персональных, вместо них будут использоваться top_popular
    compute_recs(3, is_events=True)