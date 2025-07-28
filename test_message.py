from datetime import datetime
import hashlib
import json

import uuid
import time

from app_v2.beings.being import Being, Soul
from app_v2.database.soul_repository import SoulRepository
from app_v2.beings.being import Message

genotype_example = {
  "attributes": {
    "content": {
      "table_name": "_text",
      "py_type": "str"
    },
    "timestamp": {
      "table_name": "_text",
      "py_type": "str"
    },
    "embedding": {
      "table_name": "_text",
      "py_type": "str"
    }
  }
}

genotype_message = {
  "attributes": {
    "source_uid": {
      "table_name": "_text",
      "py_type": "str"
    },
    "thread_uid": {
      "table_name": "_text",
      "py_type": "str"
    },
    "message": {
      "table_name": "_jsonb",
      "py_type": "dict"
    }
  }
}


values = {
    "source_uid": "123e4567-e89b-12d3-a456-426614174000",
    "thread_uid": "987e6543-e21b-32d3-a456-426614174999",
    "message": {"content": "Hello, world!", "role": "user"}
}

if __name__ == "__main__":
    # Example usage
    thread_id = str(uuid.uuid4())
    async def example_usage():
        print()
        print("==============================================")

        # soul = await Soul.create(
        #     alias="Test Soul",
        #     genotype=genotype_example
        # )
        # souls = await Soul.load_all()
        # if souls:
        #     print(f"Found {len(souls)}")
        # souls = await Soul.load_all_by_alias(soul.alias)
        # if souls:
        #     print(f"Found {len(souls)} with alias: {soul.alias}")
        # soul = await Soul.load(soul.soul_hash)
        # if soul:
        #     print(f"Loaded soul: {soul.alias} with hash: {soul.soul_hash}")

        # print(soul.genotype)
        # being = await Being.create(
        #     soul=soul,
        #     data=values
        # )
        message_soul = await Soul.create(
            alias="Message Soul",
            genotype=genotype_message
        )
        if message_soul:
            message = await Message.create(
                soul=message_soul,
                source_uid=str(uuid.uuid4()), 
                thread_uid=thread_id,
                message={"content": "Hello, world!", "role": "user"}
            )
            print(f" Created being with soul hash: {message.soul_hash}")
        # print(f"Attributes: {attributes}")

        return
        beings = await Being.load_all_by_soul_hash(soul.soul_hash)
        if beings:
            print(f"Found {len(beings)} beings for soul hash: {soul.soul_hash}")
        # test load by hash
        being = await Being.load_last_by_soul_hash(soul.soul_hash)
        if being:
            print(f"Loaded being with ulid: {being.ulid}, soul hash: {being.soul_hash}")
            being = await Being.load(being.ulid) if beings else None
            message_instance = Message()
            attributes = message_instance.get_attributes()
            print(f"Attributes: {attributes}")
            if being:
                print(f"Loaded being with ulid: {being.ulid}, soul hash: {being.soul_hash}")
        return
        beings = await being.load_all_by_soul_hash(soul.soul_hash)
        if not beings:
            print("No beings found for this soul hash.")
            being = await being.create(soul=soul, data=values)
            return

        print(f"Found {len(beings)} beings for soul ulid: {beings[0].ulid}, type: {type(beings[0])}")
        print(f"Being data: {beings[0].to_dict()}")
        being = await Being.load(beings[0].ulid)

        return

        await being.create(soul_hash=being.soul_hash, genotype=genotype_example, values=values)
        for b in being.to_dict().items():
            print(f"{b[0]}: {b[1]}")
        # message = await Message().create(
        #     source_uid=str(uuid.uuid4()), 
        #     thread_uid=thread_id,
        #     message={"content": "Hello, world!", "role": "user"}
        # )
        # print(message.uid)
        # get_message = await Message.load(message.uid)
        # print(get_message.to_dict())
        # messages = await Thread.get_thread_context(thread_id)

        # for x in messages:
        #     for k, v in x.items():
        #         print(f"{k}: {v}")
        #     if json.loads(x.get("genesis")).get('created_at') < datetime.utcnow().isoformat():
        #         print("Message is older than current time")
    import asyncio
    asyncio.run(example_usage())

    # 'bfeee0c2-de54-4f24-9dbf-02d2c937385a'