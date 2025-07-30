from telethon import TelegramClient

API_ID = 26078542
API_HASH = "6b40d98a20b17a7903cc3b479f88ae69"

async def get_chat_ids():
    client = TelegramClient("temp_session", API_ID, API_HASH)
    await client.start()
    
    print("Твои диалоги:")
    async for dialog in client.iter_dialogs():
        print(f"{dialog.name}: {dialog.id}")
    
    await client.disconnect()

if __name__ == "__main__":
    import asyncio
    asyncio.run(get_chat_ids())
