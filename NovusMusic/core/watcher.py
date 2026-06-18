# --------------------------------------------------------------------------------
#  NovusMusic © 2026
#  Developed by Bad Munda 
#
#  Unauthorized copying, editing, re-uploading or removing credits
#  from this source code is strictly prohibited.
# --------------------------------------------------------------------------------

import asyncio


async def watchdog() -> None:
    """No-op — watchdog disabled to keep bot running 24/7."""
    while True:
        await asyncio.sleep(3600)  # sleep forever, do nothing
