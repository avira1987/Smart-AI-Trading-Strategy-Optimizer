from django.core.management.base import BaseCommand
from typing import List
from api.mt5_client import fetch_mt5_candles
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Quick MT5 fetch test for XAUUSD / XAUUSD_I candles'

    def add_arguments(self, parser):
        parser.add_argument('--symbol', type=str, default='', help='Symbol to test (e.g., XAUUSD_I)')
        parser.add_argument('--timeframe', type=str, default='M1', help='Timeframe (M1, M5, M15, M30, H1)')
        parser.add_argument('--count', type=int, default=200, help='Number of candles to fetch')

    def handle(self, *args, **options):
        preferred_symbol = options['symbol'].strip()
        timeframe = options['timeframe'].upper()
        count = int(options['count'])

        candidates: List[str] = []
        if preferred_symbol:
            candidates = [preferred_symbol]
        else:
            # Try common gold symbols
            candidates = ['XAUUSD_I', 'XAUUSD', 'XAUUSD.', 'XAUUSD.m']

        self.stdout.write(self.style.WARNING(f"Testing MT5 with timeframe={timeframe} count={count}"))
        for sym in candidates:
            self.stdout.write(self.style.WARNING(f"Trying symbol: {sym}"))
            logger.info(f"[TEST_MT5] start symbol={sym} tf={timeframe} count={count}")
            df, err = fetch_mt5_candles(sym, timeframe=timeframe, count=count)
            if err:
                logger.warning(f"[TEST_MT5] error symbol={sym}: {err}")
                self.stdout.write(self.style.ERROR(f"  Error: {err}"))
                continue
            if df.empty:
                logger.warning(f"[TEST_MT5] empty df symbol={sym}")
                self.stdout.write(self.style.ERROR("  No data returned"))
                continue
            logger.info(f"[TEST_MT5] success symbol={sym} rows={len(df)}")
            self.stdout.write(self.style.SUCCESS(f"  OK: received {len(df)} candles for {sym}"))
            # Print last 5 rows concise
            tail = df.tail(5)
            for idx, row in tail.iterrows():
                self.stdout.write(f"    {idx} | O:{row['open']} H:{row['high']} L:{row['low']} C:{row['close']} V:{row.get('volume', 0)}")
            # Stop after first success
            break
        else:
            self.stdout.write(self.style.ERROR("All candidates failed."))


