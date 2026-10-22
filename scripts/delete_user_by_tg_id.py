"""
Скрипт полного удаления пользователя из базы данных по Telegram ID.
Удаляет пользователя и все связанные данные.
"""

import asyncio
import sys

from core.models import init, close
from core.managers.players.players import get_player_by_tg_id, delete_player
from core.models.players.players import Player
from core.models.social.clans import Clan
from core.models.economics.shops import Shop
from core.models.social.party import Party
from core.models.safety.analytics import PlaytimeRewardQueue


def _usage() -> str:
    return (
        "Usage:\n"
        "  python delete_user_by_tg_id.py <tg_id> [--force]\n\n"
        "  Полностью удаляет пользователя с указанным Telegram ID из базы данных.\n"
        "  Удаляет все связанные данные: профиль, аналитику, баны, друзей,\n"
        "  магазины, кланы, партии, квесты, транзакции и т.д.\n\n"
        "  tg_id — числовой Telegram ID пользователя.\n"
        "  --force — удалить без подтверждения (опционально).\n\n"
        "Example:\n"
        "  python delete_user_by_tg_id.py 123456789\n"
        "  python delete_user_by_tg_id.py 123456789 --force\n"
    )


async def _get_related_data_count(player: Player) -> dict:
    """Подсчитывает количество связанных записей для отображения."""
    player_id = player.id
    
    counts = {
        "clans_owned": 0,
        "shops_owned": 0,
        "parties_led": 0,
        "playtime_rewards": 0,
    }
    
    try:
        counts["clans_owned"] = await Clan.filter(owner_id=player_id).count()
        counts["shops_owned"] = await Shop.filter(owner_id=player_id).count()
        counts["parties_led"] = await Party.filter(leader_id=player_id).count()
        counts["playtime_rewards"] = await PlaytimeRewardQueue.filter(player_id=player_id).count()
    except Exception as e:
        print(f"Warning: Failed to count some related data: {e}")
    
    return counts


async def _cleanup_playtime_rewards(player_id: int) -> None:
    """Удаляет записи из очереди наград за игровое время."""
    try:
        await PlaytimeRewardQueue.filter(player_id=player_id).delete()
    except Exception as e:
        print(f"Warning: Failed to cleanup playtime rewards: {e}")


async def _run(tg_id: int, force: bool = False) -> int:
    await init()
    try:
        player = await get_player_by_tg_id(tg_id)
        if not player:
            print(f"Пользователь с Telegram ID {tg_id} не найден")
            return 2
        
        print(f"\nНайден пользователь:")
        print(f"  ID: {player.id}")
        print(f"  Telegram ID: {player.tg_id}")
        print(f"  Discord ID: {player.ds_id or 'не указан'}")
        print(f"  Никнейм: {player.nickname or 'не указан'}")
        print(f"  Роль: {player.role.value}")
        print(f"  Баланс: {player.balance}")
        print(f"  Заблокирован: {'да' if player.has_banned else 'нет'}")
        print(f"  Заблокирован бот: {'да' if player.has_locked else 'нет'}")
        
        # Подсчитываем связанные данные
        print(f"\nПодсчет связанных данных...")
        related_counts = await _get_related_data_count(player)
        
        print(f"\nБудет удалено:")
        print(f"  - Профиль игрока (PlayerProfile)")
        print(f"  - Аналитика игрока (PlayerAnalytics)")
        print(f"  - Все баны (Ban)")
        print(f"  - Все муты (Mute)")
        print(f"  - Все предупреждения (Warn)")
        print(f"  - Все друзья (Friend)")
        print(f"  - Все предметы на рынке (MarketItem)")
        print(f"  - Все квесты игрока (QuestProgress, PlayerQuest)")
        print(f"  - Все реферальные коды (Referral)")
        print(f"  - Все уведомления (Notification)")
        print(f"  - Все запросы на смену ника (NickChangeRequest)")
        print(f"  - Все сессии игрока (PlayerSession)")
        print(f"  - Кланы, где пользователь владелец: {related_counts['clans_owned']}")
        print(f"  - Магазины, где пользователь владелец: {related_counts['shops_owned']}")
        print(f"  - Партии, где пользователь лидер: {related_counts['parties_led']}")
        print(f"  - Записи в очереди наград: {related_counts['playtime_rewards']}")
        print(f"  - Транзакции (связь будет обнулена)")
        print(f"  - Логи действий админа (связь будет обнулена)")
        print(f"  - Объявления (связь автора будет обнулена)")
        print(f"  - Голосования (связь создателя будет обнулена)")
        print(f"\nПримечание: JSON поля (например, members в кланах, votes в голосованиях)")
        print(f"могут содержать ссылки на player_id, но не будут автоматически очищены.")
        
        if not force:
            print(f"\n⚠️  ВНИМАНИЕ: Это действие необратимо!")
            response = input("Продолжить удаление? (yes/no): ").strip().lower()
            if response not in ("yes", "y", "да", "д"):
                print("Удаление отменено")
                return 0
        
        # Удаляем записи из очереди наград (не FK, нужно вручную)
        if related_counts["playtime_rewards"] > 0:
            await _cleanup_playtime_rewards(player.id)
            print(f"✓ Удалено {related_counts['playtime_rewards']} записей из очереди наград")
        
        # Удаляем пользователя (CASCADE удалит все связанные записи)
        await delete_player(player)
        
        print(f"\n✓ Пользователь {tg_id} (ID: {player.id}) успешно удален из базы данных")
        return 0
    except Exception as e:
        print(f"\n❌ Ошибка при удалении пользователя: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        await close()


def main() -> int:
    if len(sys.argv) < 2:
        print(_usage())
        return 1
    
    force = "--force" in sys.argv
    
    try:
        tg_id = int(sys.argv[1])
    except ValueError:
        print("tg_id должен быть числом")
        return 1
    
    if tg_id < 1:
        print("tg_id должен быть положительным числом")
        return 1
    
    return asyncio.run(_run(tg_id=tg_id, force=force))


if __name__ == "__main__":
    sys.exit(main())
