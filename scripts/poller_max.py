# -*- coding: utf-8 -*-
"""Отвечает на запуск бота и сообщения в MAX приветствием.

Запускается по расписанию GitHub Actions. Состояние (marker) хранит сам MAX:
после обработки запрашиваем /updates с marker=последний.
API MAX: заголовок Authorization: <token> (без Bearer).

Кнопок в сообщении нет: приложение открывается кнопкой «Старт» / кнопкой меню бота,
привязанной к мини-приложению в кабинете MAX.
"""
import json
import os
import urllib.error
import urllib.request

TOKEN = os.environ["MAX_BOT_TOKEN"]
BASE = "https://botapi.max.ru"

WELCOME = (
    "🗂 Картотека — база объектов и покупателей риэлтора.\n\n"
    "• Карточки объектов: фото, цена, характеристики\n"
    "• 👥 База покупателей: бюджет, что ищет, сроки\n"
    "• 🎯 Автоподбор: какие объекты подходят клиенту\n"
    "• 🔒 Приватные данные — видите только вы\n"
    "• Презентация в один тап: ссылка, картинка, PDF\n\n"
    "👉 Нажмите кнопку «Старт» — приложение откроется прямо здесь, в MAX.\n\n"
    "Одна база в MAX, Telegram и браузере: включите синхронизацию в профиле приложения."
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
        # реагируем и на запуск бота ("Начать" -> bot_started), и на обычные сообщения
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
