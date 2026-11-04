# Portfolio Dashboard

A lightweight market dashboard for a spare monitor. It rotates through your watchlist on a big
TradingView chart, keeps a live grid of every symbol underneath, and shows your unrealized PnL %
against the average price you entered for each one.

It runs as a borderless Windows app (no browser bar), and snaps to fill whichever screen you drop it on.

## Features

- **Rotating chart.** It shows one symbol at a time and moves to the next every N seconds (default 10). The
  next chart loads in the background, so the switch is instant.
- **Live watchlist grid.** All symbols appear at once with price, day change and a sparkline (1D/1M/3M/1Y). Click a tile to show it on the
  big chart.
- **Averages and unrealised PnL.** Click "+ Click to set your average" on any tile, type your average, and the
  tile shows `Avg … Unrealised PnL +x.xx%`, updated live.
- **Desktop window.** It's borderless and fills the monitor it's on: Full, Top ½ or Bottom ½. It remembers
  the monitor and mode you used last.
- **Per-symbol timeframe.** For example, IDX stocks are locked to 1D, because that's all the free widgets provide.

## Quick start

**Option A: prebuilt exe.** Download `PortfolioDashboard.exe` (and `dashboard.html`) from
[Releases](../../releases), then run the exe.

**Option B: from source** (Windows, Python 3.10+)

```powershell
git clone https://github.com/jonathantheja99/portofolio-dashboard
cd portofolio-dashboard
pip install -r requirements.txt
pythonw dashboard.py        # or double-click run.bat
```

**Build your own exe:** run `build.bat`. The result is `dist\PortfolioDashboard.exe`.

You can also open `dashboard.html` directly in any browser. The desktop window just removes the browser UI.

## Using it

| Action | How |
| --- | --- |
| Move to another screen | Drag the symbol title (top-left) onto that screen and let go. It fills that screen. |
| Full / top half / bottom half | Use the dropdown in the header |
| Pause rotation | `Space`, or hover over the chart. Rotation also pauses while a pop-up is open. |
| Previous / next symbol | `←` / `→` |
| Set or edit an average | Click the button at the bottom of a tile. `Enter` saves, `Esc` cancels, **Clear** removes it. |
| Close / minimize | `×` / `–` in the header (or `Alt+F4`) |
| Start with Windows | `Win+R` → `shell:startup` → put a shortcut to the exe (or `run.bat`) there |

## Your watchlist

Edit the `SYMBOLS` list near the top of the `<script>` in `dashboard.html`:

```js
{ s: "IDX:BBCA", n: "PT Bank Central Asia Tbk", px: { td: "BBCA:IDX" }, tf: "D" },
```

| Field | Meaning |
| --- | --- |
| `s` | TradingView symbol with its exchange prefix, exactly as TradingView's symbol search shows it |
| `n` | Display name |
| `px` | Where the live price for the unrealised PnL % comes from (see below) |
| `tf` | Optional fixed chart timeframe for this symbol (`"D"`, `"W"`, `"60"`, …) |

If you use the exe, keep `dashboard.html` next to it. The app uses that copy, so you don't need to rebuild after editing.

## Price sources for unrealised PnL

The charts and tiles are TradingView widgets, which don't share their prices with the page. So the unrealised PnL %
uses its own feeds:

| Source (`px` key) | Covers | Key needed |
| --- | --- | --- |
| `binance` (falls back to `data-api.binance.vision`, then `coinbase`) | Crypto | No |
| `hl` (Hyperliquid) | HYPE and other Hyperliquid coins | No |
| `gold` (gold-api.com) | XAU | No |
| `td` (Twelve Data) | US stocks/ETFs, FX (USD/IDR), IDX stocks (plan-dependent) | Free key: the pop-up asks for it the first time |

The Twelve Data free tier allows 800 credits a day. The app only requests symbols you've set an average on, and
slows its refresh rate to stay under that limit.

Your averages, API key and settings are stored locally only: in the app's profile under
`%APPDATA%\PortfolioDashboard`, or in your browser's localStorage. Nothing is sent anywhere except the price
requests above.

## Notes

- Charts and quote tiles use TradingView's free embeddable widgets. Some exchanges (for example IDX) only provide daily data there.
- This is a personal tool, not financial advice.

## License

[MIT](LICENSE)
