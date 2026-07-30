# -*- coding: utf-8 -*-
"""Отвечает на сообщения боту в MAX приветствием со ссылкой на Картотеку.

Запускается по расписанию GitHub Actions. Состояние (marker) хранит сам MAX:
после обработки запрашиваем /updates с marker=последний+1.
API MAX: заголовок Authorization: <token> (без Bearer).
"""
import json
import os
import urllib.error
import urllib.request

TOKEN = os.environ["MAX_BOT_TOKEN"]
APP_URL = "https://denusa1987-netizen.github.io/kartoteka/app/"
BASE = "https://botapi.max.ru"

WELCOME = (
    "🗂 Картотека — база объектов и покупателей риэлтора.\n\n"
    "• Карточки объектов: фото, цена, характеристики\n"
    "• 👥 База покупателей: бюджет, что ищет, сроки\n"
    "• 🎯 Автоподбор: какие объекты подходят клиенту\n"
    "• 🔒 Приватные данные — видите только вы\n"
    "• Презентация в один тап: ссылка, картинка, PDF\n\n"
    "Одна база в MAX, Telegram и браузере — включите синхронизацию в профиле.\n\n"
    "Открыть приложение: " + APP_URL
)


def api(method, path, payload=None):
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8") if payload else None
    req = urllib.request.Request(
        BASE + path,
        data=data,
        method=method,
        headers={"Authorization": TOKEN, "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return {"ERR": e.code, "body": e.read().decode()[:200]}


def send(chat_id):
    """Кнопка-ссылка на приложение; если не прошла — простой текст."""
    payload = {
        "text": WELCOME,
        "attachments": [
            {
                "type": "inline_keyboard",
                "payload": {"buttons": [[{"type": "link", "text": "🗂 Открыть Картотеку", "url": APP_URL}]]},
            }
        ],
    }
    r = api("POST", "/messages?chat_id=%s" % chat_id, payload)
    if "ERR" not in r:
        return r
    return api("POST", "/messages?chat_id=%s" % chat_id, {"text": WELCOME})


def main():
    upd = api("GET", "/updates?limit=50&timeout=0")
    if "ERR" in upd:
        print("updates error:", upd)
        return
    updates = upd.get("updates") or []
    if not updates:
        print("no updates")
        return

    replied = set()
    for u in updates:
        # реагируем и на запуск бота ("Начать"), и на обычные сообщения
        msg = u.get("message") or {}
        recipient = msg.get("recipient") or {}
        chat_id = recipient.get("chat_id") or u.get("chat_id")
        if not chat_id or chat_id in replied:
            continue
        replied.add(chat_id)
        res = send(chat_id)
        print("replied to", chat_id, "->", "ok" if "ERR" not in res else res)

    marker = upd.get("marker")
    if marker:
        api("GET", "/updates?marker=%s&limit=1&timeout=0" % marker)
        print("marker confirmed", marker)


if __name__ == "__main__":
    main()
