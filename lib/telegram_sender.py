#!/usr/bin/env python3
"""
Модуль для отправки сообщений в Telegram
"""
import requests
import os

def send_to_telegram(image_path, caption=None):
    """Отправляет изображение в Telegram
    
    Args:
        image_path: путь к изображению
        caption: опциональный текст к картинке
    """
    try:
        import config
    except ImportError:
        print("✗ Ошибка: config.py не найден")
        return False
    
    if not os.path.exists(image_path):
        print(f"✗ Ошибка: файл {image_path} не найден")
        return False
    
    chat_id = getattr(config, 'TELEGRAM_CHAT_ID', None)
    bot_token = getattr(config, 'TELEGRAM_BOT_TOKEN', None)
    
    if not chat_id or chat_id == "your_chat_id_here":
        print("✗ Ошибка: TELEGRAM_CHAT_ID не настроен в config.py")
        return False
    
    if not bot_token or bot_token == "your_bot_token_here":
        print("✗ Ошибка: TELEGRAM_BOT_TOKEN не настроен в config.py")
        return False
    
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
        
        with open(image_path, 'rb') as photo:
            files = {'photo': photo}
            data = {'chat_id': chat_id}
            
            if caption:
                data['caption'] = caption
            
            response = requests.post(url, files=files, data=data)
            response.raise_for_status()
            
            print(f"✓ Изображение успешно отправлено в Telegram")
            return True
            
    except requests.exceptions.RequestException as e:
        print(f"✗ Ошибка при отправке в Telegram")
        # Не выводим детали ошибки, чтобы не палить токен или другую чувствительную информацию
        return False

