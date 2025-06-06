import logging

from fastapi import FastAPI
from contextlib import asynccontextmanager
from utils.recommendations import Recommendations
import os
import requests

features_store_url = "http://127.0.0.1:8010"
events_store_url = "http://127.0.0.1:8020"

rec_store = Recommendations()
logger = logging.getLogger("uvicorn.error")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # код ниже (до yield) выполнится только один раз при запуске сервиса
    logger.info("Starting")
    # Зашгружаем рекомендации
    rec_store.load(
        "personal",
        os.path.join(os.getcwd(), "recommendations/recommendations.parquet"),
        columns=["user_id", "item_id", "rank"],
    )
    rec_store.load(
        "default",
        os.path.join(os.getcwd(), "recommendations/top_popular.parquet"),
        columns=["item_id"],
    )
    yield
    # этот код выполнится только один раз при остановке сервиса
    logger.info("Stopping")
    rec_store.stats()


# создаём приложение FastAPI
app = FastAPI(title="recommendations", lifespan=lifespan)


@app.post("/recommendations_offline")
async def recommendations_offline(user_id: int, k: int = 100):
    """
    Возвращает список рекомендаций длиной k для пользователя user_id
    """

    recs = rec_store.get(user_id, k)

    return {"recs": recs}


def dedup_ids(ids):
    """
    Дедублицирует список идентификаторов, оставляя только первое вхождение
    """
    seen = set()
    ids = [id for id in ids if not (id in seen or seen.add(id))]

    return ids


@app.post("/recommendations_online")
async def recommendations_online(user_id: int, k: int = 100):
    # получаем список последних событий пользователя, возьмём три последних
    params = {"user_id": user_id, "k": 3}
    headers = {"Content-type": "application/json", "Accept": "text/plain"}

    # ваш код здесь
    resp = requests.post(events_store_url + "/get", headers=headers, params=params)
    events = resp.json()
    events = events["events"]

    # получаем список айтемов, похожих на последние три, с которыми взаимодействовал пользователь
    items = []
    scores = []
    for item_id in events:
        # для каждого item_id получаем список похожих в item_similar_items
        # k + 1 так как первое значение - сам айтем, убираем его, значит требуется на 1 элемент больше
        params = {"item_id": item_id, "k": k+1}
        resp = requests.post(features_store_url + "/similar_items", headers=headers, params=params)
        item_similar_items = resp.json()
        
        # В recommendations первый item - запрашиваемый, поэтому исключаем его
        items += item_similar_items["item_id_2"][1:k+1]
        scores += item_similar_items["score"][1:k+1]
    # сортируем похожие объекты по scores в убывающем порядке
    # для старта это приемлемый подход
    combined = list(zip(items, scores))
    combined = sorted(combined, key=lambda x: x[1], reverse=True)
    combined = [item for item, _ in combined]

    # удаляем дубликаты, чтобы не выдавать одинаковые рекомендации
    recs = dedup_ids(combined)

    return {"recs": recs}


@app.post("/recommendations")
async def recommendations(user_id: int, k: int = 100):
    """
    Возвращает список рекомендаций длиной k для пользователя user_id
    """
    recs_offline = await recommendations_offline(user_id, k)
    recs_online = await recommendations_online(user_id, k)

    recs_offline = recs_offline["recs"]
    recs_online = recs_online["recs"]

    recs_blended = []

    min_length = min(len(recs_offline), len(recs_online))
    for i in range(min_length):
        if i % 2 == 0:  # Нечетная позиция 
            recs_blended.append(recs_online[i])
        else:  # Четная позиция 
            recs_blended.append(recs_offline[i])

    # Добавляем оставшиеся элементы (если один из списков длиннее)
    if len(recs_online) > min_length:
        recs_blended.extend(recs_online[min_length:])
    elif len(recs_offline) > min_length:
        recs_blended.extend(recs_offline[min_length:])

    # Удаляем дубликаты
    recs_blended = dedup_ids(recs_blended)

    # Обрезаем до k рекомендаций
    recs_blended = recs_blended[:k]

    return {"recs": recs_blended}