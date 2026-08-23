"""Projeye ozel Python keyword kutuphanesi.

NEDEN VAR?
    Robot Framework, is akisini tarif etmekte mukemmeldir ama HESAP YAPMAKTA
    zayiftir. "$29.99 metnini sayiya cevir, KDV'yi hesapla, listenin sirali
    olup olmadigini kontrol et" gibi isler Robot sozdiziminde okunaksiz olur.
    Bu tur mantik Python'a tasinir ve Robot'a KEYWORD olarak sunulur.

    Robot Framework'un asil gucu de budur: dogal dile yakin katman ile
    programlama katmanini temiz bir sinirla ayirir. Test yazan kisi
    `Verify Checkout Totals Are Correct` yazar; altta ne oldugunu bilmesi
    gerekmez.

KARSILASTIRMA NOTU:
    Selenium/Playwright projelerinde ayni mantik `utils/parsers.py` icindedir
    ve dogrudan cagrilir. Buradaki fark, bu fonksiyonlarin Robot'un
    keyword adlandirma kurallarina (bosluklu, buyuk harfli) donusmesidir:
        parse_price()              ->  Parse Price
        verify_sorted_ascending()  ->  Verify Sorted Ascending
"""
from __future__ import annotations

import re
from typing import Any, Sequence

from robot.api import logger
from robot.api.deco import keyword, library

_PRICE_PATTERN = re.compile(r"-?\d+(?:[.,]\d+)?")


@library(scope="GLOBAL", version="1.0.0", auto_keywords=False)
class SauceDemoLibrary:
    """SauceDemo'ya ozel hesaplama ve dogrulama keyword'leri."""

    ROBOT_LIBRARY_SCOPE = "GLOBAL"
    ROBOT_LIBRARY_VERSION = "1.0.0"

    # ------------------------------------------------------------------ #
    # Metin -> veri donusumleri
    # ------------------------------------------------------------------ #
    @keyword("Parse Price")
    def parse_price(self, text: str) -> float:
        """'Item total: $129.94' metninden 129.94 sayisini cikarir.

        Ornek:
        | ${amount} = | Parse Price | Item total: $129.94 |
        """
        match = _PRICE_PATTERN.search(str(text).replace(",", "."))
        if not match:
            raise ValueError(f"Metinden fiyat cikarilamadi: '{text}'")
        return round(float(match.group()), 2)

    @keyword("Parse Prices")
    def parse_prices(self, texts: Sequence[str]) -> list[float]:
        """Fiyat metinlerinden olusan listeyi sayi listesine cevirir."""
        return [self.parse_price(t) for t in texts]

    @keyword("Product Slug")
    def product_slug(self, name: str) -> str:
        """'Sauce Labs Backpack' -> 'sauce-labs-backpack'

        SauceDemo'nun data-test degerlerini uretir; boylece her urun icin
        ayri locator tanimlamak gerekmez.
        """
        return name.strip().lower().replace(" ", "-")

    @keyword("Add To Cart Locator")
    def add_to_cart_locator(self, product_name: str) -> str:
        return f"css:[data-test='add-to-cart-{self.product_slug(product_name)}']"

    @keyword("Remove From Cart Locator")
    def remove_from_cart_locator(self, product_name: str) -> str:
        return f"css:[data-test='remove-{self.product_slug(product_name)}']"

    # ------------------------------------------------------------------ #
    # Siralama dogrulamalari
    # ------------------------------------------------------------------ #
    @keyword("Verify List Is Sorted Ascending")
    def verify_list_is_sorted_ascending(self, values: Sequence[Any], label: str = "Liste") -> None:
        ordered = sorted(values)
        if list(values) != ordered:
            raise AssertionError(
                f"{label} artan sirali degil.\n  Gercek : {list(values)}\n  Beklenen: {ordered}"
            )
        logger.info(f"{label} artan sirali: {list(values)}")

    @keyword("Verify List Is Sorted Descending")
    def verify_list_is_sorted_descending(self, values: Sequence[Any], label: str = "Liste") -> None:
        ordered = sorted(values, reverse=True)
        if list(values) != ordered:
            raise AssertionError(
                f"{label} azalan sirali degil.\n  Gercek : {list(values)}\n  Beklenen: {ordered}"
            )
        logger.info(f"{label} azalan sirali: {list(values)}")

    # ------------------------------------------------------------------ #
    # Is kurali dogrulamalari
    # ------------------------------------------------------------------ #
    @keyword("Verify Checkout Totals")
    def verify_checkout_totals(
        self,
        subtotal_text: str,
        tax_text: str,
        total_text: str,
        expected_subtotal: float | None = None,
        tax_rate: float = 0.08,
        tolerance: float = 0.01,
    ) -> dict:
        """Checkout ozetindeki tum tutarlari tek keyword'de dogrular.

        Kontroller:
          1. Ara toplam beklenen degere esit mi? (opsiyonel)
          2. KDV = ara toplam x oran mi?
          3. Genel toplam = ara toplam + KDV mi?

        Ornek:
        | Verify Checkout Totals | ${sub} | ${tax} | ${total} |
        | ...                    | expected_subtotal=39.98   | tax_rate=0.08 |
        """
        subtotal = self.parse_price(subtotal_text)
        tax = self.parse_price(tax_text)
        total = self.parse_price(total_text)
        errors: list[str] = []

        if expected_subtotal is not None:
            expected_subtotal = float(expected_subtotal)
            if abs(subtotal - expected_subtotal) > tolerance:
                errors.append(
                    f"Ara toplam hatali: beklenen {expected_subtotal:.2f}, gercek {subtotal:.2f}"
                )

        expected_tax = round(subtotal * float(tax_rate), 2)
        if abs(tax - expected_tax) > tolerance:
            errors.append(
                f"KDV hatali: {subtotal:.2f} x {tax_rate} = {expected_tax:.2f} olmali, "
                f"ekranda {tax:.2f}"
            )

        expected_total = round(subtotal + tax, 2)
        if abs(total - expected_total) > tolerance:
            errors.append(
                f"Genel toplam hatali: {subtotal:.2f} + {tax:.2f} = {expected_total:.2f} olmali, "
                f"ekranda {total:.2f}"
            )

        if errors:
            raise AssertionError("Tutar dogrulamasi basarisiz:\n  - " + "\n  - ".join(errors))

        logger.info(
            f"Tutarlar dogru | Ara toplam: {subtotal:.2f} | "
            f"KDV: {tax:.2f} | Toplam: {total:.2f}"
        )
        return {"subtotal": subtotal, "tax": tax, "total": total}

    @keyword("Sum Product Prices")
    def sum_product_prices(self, products: dict, names: Sequence[str]) -> float:
        """Referans fiyat tablosundan secili urunlerin toplamini hesaplar."""
        total = 0.0
        missing = []
        for name in names:
            if name not in products:
                missing.append(name)
                continue
            total += float(products[name])
        if missing:
            raise ValueError(f"Referans veride bulunmayan urunler: {missing}")
        return round(total, 2)

    @keyword("Verify Sets Are Equal")
    def verify_sets_are_equal(
        self, actual: Sequence[str], expected: Sequence[str], label: str = "Kume"
    ) -> None:
        """Iki listeyi SIRADAN BAGIMSIZ karsilastirir ve farki raporlar."""
        actual_set, expected_set = set(actual), set(expected)
        if actual_set == expected_set:
            logger.info(f"{label} eslesiyor ({len(actual_set)} oge)")
            return
        raise AssertionError(
            f"{label} eslesmiyor.\n"
            f"  Fazla olanlar : {sorted(actual_set - expected_set)}\n"
            f"  Eksik olanlar : {sorted(expected_set - actual_set)}"
        )

    # ------------------------------------------------------------------ #
    # Raporlama yardimcilari
    # ------------------------------------------------------------------ #
    @keyword("Log Test Data Table")
    def log_test_data_table(self, title: str, rows: dict) -> None:
        """Robot log.html icine HTML tablo basar.

        Robot'un `logger.info(..., html=True)` destegi, raporun okunakliligini
        artirmak icin kullanilabilecek guclu ama az bilinen bir ozelliktir.
        """
        cells = "".join(
            f"<tr><td style='padding:4px 12px'><b>{k}</b></td>"
            f"<td style='padding:4px 12px'>{v}</td></tr>"
            for k, v in rows.items()
        )
        logger.info(
            f"<h4>{title}</h4><table border='1' style='border-collapse:collapse'>"
            f"{cells}</table>",
            html=True,
        )

    @keyword("Count Broken Images In Page Source")
    def count_broken_images(self, image_sources: Sequence[str]) -> int:
        """Ayni src'ye sahip gorselleri sayar (problem_user senaryosu)."""
        return len(image_sources) - len(set(image_sources))
