# -*- coding: utf-8 -*-
"""Отвечает на /start и сообщения приветствием с кнопкой Mini App.
Запускается по расписанию GitHub Actions; состояние (offset) хранит сам Telegram:
подтверждаем обработанные апдейты вызовом getUpdates с offset=last+1.
"""
import json
import os
import urllib.request

TOKEN = os.environ["TG_BOT_TOKEN"]
APP_URL = "https://denusa1987-netizen.github.io/kartoteka/app/"

WELCOME = (
    "🗂 <b>Картотека</b> — база объектов риэлтора в телефоне.\n\n"
    "• Карточки объектов: фото, цена, характеристики\n"
    "• 🔒 Приватные данные собственника — видите только вы\n"
    "• Презентация клиенту в один тап: картинка, PDF или текст\n"
    "• Данные хранятся у вас + резервная копия в облаке Telegram\n\n"
    "Жмите кнопку ниже или «Картотека» слева от поля ввода 👇"
)


def api(method, payload=None):
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8") if payload else None
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{TOKEN}/{method}",
        data=data,
        headers={"Content-Type": "application/json"} if data else {},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


def main():
    updates = api("getUpdates", {"timeout": 0, "allowed_updates": ["message"]})
    if not updates.get("ok") or not updates["result"]:
        print("no updates")
        return
    last_id = 0
    replied = set()
    for upd in updates["result"]:
        last_id = max(last_id, upd["update_id"])
        msg = upd.get("message")
        if not msg:
            continue
        chat = msg.get("chat", {})
        if chat.get("type") != "private":
            continue
        chat_id = chat["id"]
        if chat_id in replied:
            continue
        replied.add(chat_id)
        api(
            "sendMessage",
            {
                "chat_id": chat_id,
                "text": WELCOME,
                "parse_mode": "HTML",
                "reply_markup": {
                    "inline_keyboard": [
                        [{"text": "🗂 Открыть Картотеку", "web_app": {"url": APP_URL}}]
                    ]
                },
            },
        )
        print("replied to", chat_id)
    # подтвердить обработку — Telegram больше не отдаст эти апдейты
    api("getUpdates", {"offset": last_id + 1, "limit": 1, "timeout": 0})
    print("confirmed offset", last_id + 1)


if __name__ == "__main__":
    main()
