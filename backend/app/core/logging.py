"""애플리케이션 전역 로깅 설정.

uvicorn이 미리 부착한 root logger 핸들러를 덮어 `app.*` 로거의
INFO/WARNING이 stdout에 출력되도록 한다.
"""

import logging
from typing import Optional

from app.core.config import settings


def configure_logging(level: Optional[str] = None) -> None:
    """Idempotent logging setup."""
    lvl = (level or settings.LOG_LEVEL or "INFO").upper()
    logging.basicConfig(
        level=lvl,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        force=True,
    )
    logging.getLogger("app").setLevel(lvl)
