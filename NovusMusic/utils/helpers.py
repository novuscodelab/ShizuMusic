# --------------------------------------------------------------------------------
#  NovusMusic © 2026
#  Developed by Bad Munda 
#
#  Unauthorized copying, editing, re-uploading or removing credits
#  from this source code is strictly prohibited.
# --------------------------------------------------------------------------------

import os


def delete_file(path: str) -> None:
    """Silently delete a file if it exists."""
    try:
        if path and os.path.exists(path):
            os.remove(path)
    except Exception:
        pass
