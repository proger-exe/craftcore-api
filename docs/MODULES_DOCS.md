# Стандарт создания модулей.
- Основа декларирования и доменной структуры проекта

## Типы модулей:
- База данных (модели)
- Функциональный воркер (API / тгбот / дсбот / плагины)
- Служба (shared, иные дополнительные модули для воркеров)

## Категории модулей:
- Экономика (economics)
- Социальный (social)
- Режимный (safety / admins)
- Информационо-агитационный (mailing)
- Интеграция / связь (relation)


## Как создавать

Строго соблюдается иерархия:

1. Тип модуля
2. Категория 
3. Название

## Пример:

```python 
# /models/economics/__init__.py
"""
Module of economic system
Objects: 
- Shops (deps: /app/routers/shops.py, /bot/module/shops, /dis_bot/module/shops)
- Wallet (deps: /app/routers/wallet.py, /bot/module/wallet, /dis_bot/module/wallet) 

from .shops import *
from .wallet import *
```

## ПРАВИЛА
- `__init__.py` обязан быть задокументирован на каждом уровне, чтобы соблюдать level-spacing и не пихать лишние объекты / модули.
- `ONLY CATEGORY` - никаких объектов, которые лишь частично связаны с категорией. В случае создания managers для работы взаимосвязей категорий использовать категорию `relation`
- `asterisk method` - чтобы упростить импорты в дальнейшем сразу импортировать все с помощью `from .module import *`
- `PEP-8 full method` - полностью соблюдать PEP-8 стандарты.
- `Docs everything` - полностью документировать функции

---

## Текущие модули API (ссылки)

Полный перечень эндпоинтов и схем см. в [docs/API.md](API.md).

**Admin:** identity (поиск по нику/Telegram), players/search (поиск игроков), analytics (досье игрока, server-snapshot, player sessions), settings (настройки бота), votes (создание голосований), wallet (freeze/unfreeze), referrals/stats, nickchange (requests, approve, reject), announcements, notifications, safety (bans, mutes, warns), statistics.

**User:** profile, analytics, telegram link, clans, shops, transactions (в т.ч. balance с полем frozen, transfer), quests (системные и player-created marketplace: create, player-created, details, applications, submit/review, abandon, cancel, delete), votes (list, get, cast, stats), rankings (balance, online-time), referrals (code, join, stats), nickchange (request, history), mailing (announcements, notifications), market, party, social (friends), qol (scenarios, npcs, crafts).
