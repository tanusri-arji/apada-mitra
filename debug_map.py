import asyncio
from playwright.async_api import async_playwright

async def test():
    async with async_playwright() as p:
        b = await p.chromium.launch(channel='chrome', headless=True)
        page = await b.new_page()
        page.on('console', lambda msg: print('PAGE LOG:', msg.text))
        page.on('pageerror', lambda err: print('PAGE ERROR:', err))
        page.on('response', lambda res: print('RESP:', res.url, res.status))
        await page.goto('http://localhost:5173', wait_until='domcontentloaded')
        print("Waiting for .custom-village-icon to appear...")
        await page.wait_for_selector(".custom-village-icon", timeout=20000)
        v_count = await page.evaluate('document.querySelectorAll(".custom-village-icon").length')
        m_count = await page.evaluate('document.querySelectorAll(".leaflet-marker-icon").length')
        print(f"SUCCESS! custom-village-icon: {v_count}, leaflet-marker-icon: {m_count}")
        await b.close()

if __name__ == '__main__':
    asyncio.run(test())
