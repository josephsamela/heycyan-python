import asyncio
import heycyan

async def main():
    callback_done = asyncio.Event()
    glass1 = await heycyan.device('A937F620-1BA2-583F-51F1-D53418614922')
    await callback_done.wait()

if __name__ == '__main__':
    asyncio.run(main())
