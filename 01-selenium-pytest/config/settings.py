"""Yapilandirma yukleyici.

config.yaml -> ortam degiskeni -> CLI parametresi seklinde artan oncelikle
birlestirilmis, tip guvenli ayar nesneleri uretir.

KARSILASTIRMA NOTU:
    Robot Framework'te bu is `variables/` klasoru ve `--variablefile` ile,
    Playwright'ta ise `playwright.config`/fixture katmaniyla yapilir. Selenium
    tarafinda hazir bir mekanizma YOKTUR; asagidaki kod tamamen elle yazilir.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PROJECT_ROOT.parent
SHARED_DATA_DIR = REPO_ROOT / "shared"
CONFIG_FILE = PROJECT_ROOT / "config" / "config.yaml"


@dataclass(frozen=True)
class Timeouts:
    page_load: int = 30
    script: int = 20
    explicit_wait: int = 15
    slow_user_wait: int = 40
    poll_frequency: float = 0.25


@dataclass(frozen=True)
class BrowserSettings:
    name: str = "chrome"
    headless: bool = True
    window_width: int = 1920
    window_height: int = 1080
    implicit_wait: int = 0


@dataclass(frozen=True)
class ArtifactSettings:
    screenshot_on_failure: bool = True
    screenshot_dir: Path = PROJECT_ROOT / "reports" / "screenshots"
    page_source_on_failure: bool = True
    page_source_dir: Path = PROJECT_ROOT / "reports" / "page_source"
    log_dir: Path = PROJECT_ROOT / "reports" / "logs"

    def ensure_dirs(self) -> None:
        for directory in (self.screenshot_dir, self.page_source_dir, self.log_dir):
            Path(directory).mkdir(parents=True, exist_ok=True)


@dataclass(frozen=True)
class Settings:
    env: str
    base_url: str
    browser: BrowserSettings
    timeouts: Timeouts
    artifacts: ArtifactSettings
    stale_element_attempts: int = 3
    stale_element_backoff: float = 0.4
    raw: dict = field(default_factory=dict, repr=False)

    # --- Sik kullanilan turetilmis adresler -------------------------------
    @property
    def login_url(self) -> str:
        return self.base_url

    @property
    def inventory_url(self) -> str:
        return f"{self.base_url}/inventory.html"

    @property
    def cart_url(self) -> str:
        return f"{self.base_url}/cart.html"

    @property
    def checkout_step_one_url(self) -> str:
        return f"{self.base_url}/checkout-step-one.html"

    @property
    def checkout_step_two_url(self) -> str:
        return f"{self.base_url}/checkout-step-two.html"

    @property
    def checkout_complete_url(self) -> str:
        return f"{self.base_url}/checkout-complete.html"


def _read_yaml() -> dict:
    with CONFIG_FILE.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


@lru_cache(maxsize=8)
def load_settings(
    env: str | None = None,
    browser: str | None = None,
    headless: bool | None = None,
) -> Settings:
    """Ayarlari yukler. lru_cache sayesinde YAML tek kez okunur."""
    raw = _read_yaml()

    env_name = env or os.getenv("TEST_ENV") or raw.get("default_env", "prod")
    env_block = raw.get("environments", {}).get(env_name)
    if env_block is None:
        available = ", ".join(raw.get("environments", {}))
        raise ValueError(f"Bilinmeyen ortam: '{env_name}'. Tanimlilar: {available}")

    browser_block = raw.get("browser", {})
    browser_settings = BrowserSettings(
        name=(browser or os.getenv("TEST_BROWSER") or browser_block.get("name", "chrome")).lower(),
        headless=browser_block.get("headless", True) if headless is None else headless,
        window_width=browser_block.get("window_width", 1920),
        window_height=browser_block.get("window_height", 1080),
        implicit_wait=browser_block.get("implicit_wait", 0),
    )

    timeout_block = raw.get("timeouts", {})
    timeouts = Timeouts(
        page_load=timeout_block.get("page_load", 30),
        script=timeout_block.get("script", 20),
        explicit_wait=timeout_block.get("explicit_wait", 15),
        slow_user_wait=timeout_block.get("slow_user_wait", 40),
        poll_frequency=timeout_block.get("poll_frequency", 0.25),
    )

    artifact_block = raw.get("artifacts", {})
    artifacts = ArtifactSettings(
        screenshot_on_failure=artifact_block.get("screenshot_on_failure", True),
        screenshot_dir=PROJECT_ROOT / artifact_block.get("screenshot_dir", "reports/screenshots"),
        page_source_on_failure=artifact_block.get("page_source_on_failure", True),
        page_source_dir=PROJECT_ROOT / artifact_block.get("page_source_dir", "reports/page_source"),
        log_dir=PROJECT_ROOT / artifact_block.get("log_dir", "reports/logs"),
    )
    artifacts.ensure_dirs()

    retry_block = raw.get("retry", {})

    return Settings(
        env=env_name,
        base_url=env_block["base_url"].rstrip("/"),
        browser=browser_settings,
        timeouts=timeouts,
        artifacts=artifacts,
        stale_element_attempts=retry_block.get("stale_element_attempts", 3),
        stale_element_backoff=retry_block.get("stale_element_backoff", 0.4),
        raw=raw,
    )
