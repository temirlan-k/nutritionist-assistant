# src/core/counters.py

from pymongo import ReturnDocument


async def get_next_sequence(db, name: str) -> int:
    """
    Получает следующее значение счётчика из коллекции counters.
    Параметры:
      - db: экземпляр базы данных (AsyncIOMotorDatabase)
      - name: имя счётчика (например, "dayplan_index")
    """
    ret = await db.counters.find_one_and_update(
        {"_id": name},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
    return ret["seq"]
