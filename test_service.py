import requests
import time

# Поместим несколько взаимодействий для пользователя
recommendations_url = "http://127.0.0.1:8000"
events_store_url = "http://127.0.0.1:8020"
headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}

# Взаимодействие пользоватея с айтемом
def add_event(user_id: int, item_id: int):
    params = {"user_id": user_id, "item_id": item_id}
    resp = requests.post(events_store_url + "/put", headers=headers, params=params)
    if resp.status_code == 200:
        result = resp.json()
    else:
        result = None
        print(f"status code: {resp.status_code}")
    print(result)

# Посмотрим на все взаимодействия пользователи (макс 10 последних)
def get_user_events(user_id: int):
    params = {"user_id": user_id}
    resp = requests.post(events_store_url + "/get", headers=headers, params=params)
    if resp.status_code == 200:
        result = resp.json()
    else:
        result = None
        print(f"status code: {resp.status_code}")
        
    print(result)

# Рекомендуем k айтемов для трех последних, сортируем по score
def get_online_user_recommendations(user_id: int, k=100):
    params = {"user_id": user_id, 'k': k}
    resp = requests.post(recommendations_url + "/recommendations_online", headers=headers, params=params)
    online_recs = resp.json()
    print(online_recs)

# Смотрим на бленд рекомендация (offline и online)
def get_all_user_recs(user_id, k):
    params = {"user_id": user_id, 'k': k}
    resp_offline = requests.post(recommendations_url + "/recommendations_offline", headers=headers, params=params)
    resp_online = requests.post(recommendations_url + "/recommendations_online", headers=headers, params=params)
    resp_blended = requests.post(recommendations_url + "/recommendations", headers=headers, params=params)

    recs_offline = resp_offline.json()["recs"]
    recs_online = resp_online.json()["recs"]
    recs_blended = resp_blended.json()["recs"]

    print(recs_offline)
    print(recs_online)
    print(recs_blended)


if __name__ == "__main__":
    # Взаимодействие 1
    add_event(26, 78194999)
    time.sleep(0.1)

    # Взаимодействие 2
    add_event(26, 84099295)
    time.sleep(0.1)

    # Взаимодействие 3
    add_event(26, 100736375)
    time.sleep(0.1)

    # Взаимодействие 4
    add_event(26, 33307667)
    time.sleep(0.1)

    # Проверим наличие events у пользователя
    get_user_events(26)
    time.sleep(0.1)

    # Проверим online рекомендации, рекомендуем 5 похожих из similar_items для каждого из 3-х последних item_id пользователя
    get_online_user_recommendations(26, k=5)

    print()
    get_all_user_recs(26, 5)










