# QSR automation framework

Python + Pytest + Appium (Android tablets) + Playwright (web POS). Layout: **pages** (POM), **flows** (business orchestration), **actions** (low-level UI), **drivers** (sessions).

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
```

**Appium Server + UiAutomator2 (not in `requirements.txt`):** Python installs the **client** only. Install **Node.js**, then globally install Appium and the Android driver on the machine where you run `appium`:

```bash
npm i -g appium
appium driver install uiautomator2
appium driver list --installed
```

## Configuration

1. Edit `config/devices.yaml` — set each **UDID** from `adb devices` (see [Android Studio emulators](#android-studio-emulators) below).
2. Edit `config/capabilities.yaml` — set real `appium:appPackage`, `appium:appActivity`, and optional `appium:app` APK paths.
3. Edit `config/env.yaml` — POS **base_url**, Appium **server_url**.

Optional: add `config/local.yaml` (gitignored) to override `env.yaml` without editing committed files.

### Android app permissions (from configuration)

Permissions are controlled in **`config/capabilities.yaml`**, not in `env.yaml`.

- **`emulator_common`** / **`device_common`** already set **`appium:autoGrantPermissions: true`**, which tells Appium to grant declared permissions when possible.
- If a dialog still appears (for example notifications on Android 13+), add explicit grants under the same block (or under a specific `apps.<role>` entry):

```yaml
appium:grantPermissions:
  - android.permission.POST_NOTIFICATIONS
```

List permission names from your app’s manifest or from:  
`adb shell dumpsys package your.package | findstr permission`

### Android Studio emulators

Use **AVDs** (Android Virtual Devices) the same way as physical devices: Appium attaches to the emulator **serial** shown by ADB.

1. Install **Android Studio** and the **SDK** (platform tools include `adb`).
2. Open **Device Manager** → create or start one AVD per role you need (for example gunner, bombardier, wingman, pilot), or run fewer AVDs and map multiple roles only after you understand parallel limits.
3. With each emulator booted, run **`adb devices`** — emulators appear as `emulator-5554`, `emulator-5556`, etc. (first booted is usually `5554`, next `5556`, …).
4. Copy those serials into `config/devices.yaml` as each role’s `udid`.
5. Keep **`kind: emulator`** on those entries so `emulator_common` caps from `capabilities.yaml` apply (e.g. auto-grant permissions, disable window animation). For real hardware, use `kind: device` or remove `kind` and add a `device_common` block later if you need it.

Ensure `adb` is on your `PATH` (typical Windows SDK path: `%LOCALAPPDATA%\Android\Sdk\platform-tools`). Start **Appium 2** (`appium`) before tests; use the same `appium:server_url` as in `config/env.yaml`.

Quick check from the repo root: `powershell -File scripts/check_android_devices.ps1`

### IP-based device configuration (ADB over Wi-Fi)

You can run tablets by IP instead of USB. The framework already supports this because `udid` can be any serial returned by `adb devices`.

1. Connect tablet and laptop to the same network.
2. Enable Developer options and USB debugging on the tablet.
3. Pair/connect ADB over Wi-Fi (Android 11+ pairing flow, or `adb tcpip 5555` for older flow).
4. Confirm `adb devices` shows a serial like `192.168.x.x:5555`.
5. Put that exact serial in `config/devices.yaml` and set `kind: device`.

Example:

```yaml
devices:
  pilot:
    udid: "192.168.1.47:5555"
    role: pilot
    kind: device
```

Helper script:

```bash
powershell -File scripts/connect_android_wifi.ps1 -DeviceIp 192.168.1.47 -Port 5555
```

**Wireless UDID auto-heal (IPv4:port drift):** If `adb devices` shows the tablet on a **new port** (e.g. `10.0.0.183:46623`) but `config/devices.yaml` still has an old `10.0.0.183:34461`, the framework runs `adb devices` and, when there is exactly **one** online `device` for that IP, uses the new serial automatically (enabled by default).

- Disable: set `HEAL_WIRELESS_UDID=0` or pass **`pytest --no-wireless-udid-heal`**.
- Persist the resolved value to gitignored **`config/local.yaml`** (so the next run starts with the right port): set `HEAL_WIRELESS_UDID_PERSIST=1` or pass **`pytest --persist-healed-udid`**.

If **more than one** tablet is online with the same IP prefix, auto-heal does not switch UDIDs (avoids picking the wrong device).

## Run tests

```bash
pytest
```

Each run also writes a **self-contained HTML report** to **`reports/html/report.html`** (configured in `pytest.ini`). Requires **`pip install -r requirements.txt`** so **pytest-html** is installed. To skip HTML for one run: `pytest -p no:html`.

Smoke tests load YAML only. Tests marked `e2e` or `integration` run a one-time **preflight** (device + Appium + app check) before the first matching test, unless you pass `--skip-preflight`. Run them explicitly, for example:

```bash
pytest -m e2e
```

### Channel and order profile (E2E)

- **`--channel web`** — submit via Playwright POS (`web.base_url`); default.
- **`--channel api`** — POST JSON from `data/orders.json` to **`api.orders_submit_url`** in `config/env.yaml`.
- **`--channel tablet`** — **no Playwright**, no HTTP submit; only runs **Appium / KDS validation** using `data/orders.json`. Use when the order is already on the tablets (manual/API elsewhere) or you only exercise tablet UI checks.

Pick the order payload by key in **`data/orders.json`**:

```bash
pytest tests\test_order_end_to_end.py -m e2e --channel web --order sample_order
pytest tests\test_order_end_to_end.py -m e2e --channel api --order api_full_ticket
pytest tests\test_order_end_to_end.py -m e2e --channel tablet --order sample_order --preflight-roles pilot
```

You can also set **`TEST_CHANNEL`** and **`TEST_ORDER_PROFILE`** env vars instead of flags.

Configure **`api.orders_submit_url`** before using `--channel api` (empty URL raises a clear error).

### Functional tests (Pilot station app)

Pilot tablet flows live in **`tests/test_pilot_functional.py`** (marker **`functional`**).

1. Pilot station locators are implemented in **`pages/mobile/pilot_page.py`**.
2. The functional test validates timer/order fields/customer/wings and taps **Drop Sides**.
3. Run:

```bash
pytest -m functional --preflight-roles pilot
```

Functional tests include:
- Pilot station timer bar + order sections visibility
- customer name + wings visibility + tap **Drop Sides**

#### Add a new Pilot test (copy/paste)

Use this as the simplest pattern for new SDETs:

```python
import pytest
from pages.mobile.pilot_page import PilotPage


@pytest.mark.functional
@pytest.mark.integration
def test_pilot_station_smoke(device_manager) -> None:
    page = PilotPage(device_manager.get("pilot"))
    page.run_station_smoke_checks(customer_name="sravani kompall", tap_drop_sides=True)
```

`run_station_smoke_checks()` is only a wrapper. It still runs all required steps:
- `assert_timer_bar_displayed()`
- `assert_order_number_block_displayed()`
- `assert_order_type_block_displayed()`
- `assert_customer_name_displayed("...")`
- `assert_wings_displayed()`
- `tap_drop_sides()` (when `tap_drop_sides=True`)

For most new tests, only change:
- `customer_name`
- `tap_drop_sides` (`True` / `False`)

If you prefer explicit style, use this equivalent form:

```python
import pytest
from pages.mobile.pilot_page import PilotPage


@pytest.mark.functional
@pytest.mark.integration
def test_pilot_station_explicit(device_manager) -> None:
    page = PilotPage(device_manager.get("pilot"))
    page.assert_timer_bar_displayed()
    page.assert_order_number_block_displayed()
    page.assert_order_type_block_displayed()
    page.assert_customer_name_displayed("sravani kompall")
    page.assert_wings_displayed()
    page.tap_drop_sides()
```

### Automatic device video recording

You can record tablet execution per test and store MP4 artifacts in **`reports/videos/`**.

```bash
pytest -m functional --preflight-roles pilot --record-device-video --video-role pilot
```

- `--record-device-video` enables recording hook.
- `--video-role` selects which role/device udid to record from `config/devices.yaml` (default: `pilot`).
- Files are saved as one MP4 per test (best-effort pull from `/sdcard`).
- Android `screenrecord` may have device-imposed duration limits (often ~180s).

### Device/app preflight before E2E

For tests marked `integration`/`e2e`, the framework runs a one-time preflight before the first test:

- verifies each configured role can start an Appium session,
- verifies the role exists in both `config/devices.yaml` and `config/capabilities.yaml`,
- verifies `appium:appPackage` is installed/reachable on that device when provided.

Optional flags:

```bash
pytest -m e2e --preflight-roles pilot,gunner
pytest -m e2e --skip-preflight
```

### KDS validation (Gunner / Bombardier / Wingman / Pilot)

Line items in **`data/orders.json`** should include **`tags`** (see **`data/kitchen_station_rules.yaml`**) so the framework knows which tablets must show which lines. After submit, **`KitchenStationValidation`** checks:

- **Gunner** — only lines tagged for Gunner (sides, corn, boneless, tenders).
- **Bombardier** — only lines tagged for Bombardier (classic, classic_boneless, tenders_classic).
- **Wingman** — flavors / spices lines.
- **Pilot** — **full order** (all lines, including dips and drinks).

Assertions use **`display_name`** (or `sku`) as visible text; adjust **`assert_line_texts_visible`** in **`pages/base_page.py`** if your UI uses resource ids instead of text.

- **Order number:** set **`order_number`** (or `order_id` / `ticket_number`) on the order object in **`data/orders.json`**. When **`kitchen.verify_order_number`** is true (default), each tablet under test must show that string before line assertions.
- **Quantity:** each line is matched using **`kitchen.line_text_format`** in **`config/env.yaml`** (default `"{qty}x {name}"`). Override any line with **`kds_line_text`** on the item to match the UI exactly.

Optional **`kitchen.sync_wait_s`** in **`config/env.yaml`** waits before reading tablets after submit.

## Command reference

Quick copy/paste commands used with this framework (PowerShell on Windows). Paths assume repo root.

### Run tests — recipes and parameter reference

Run these from the **repo root** after activating the venv (next subsection).

#### 1. Smoke tests (no Appium / no device)

```powershell
cd c:\Users\prash\MyProjects\gitrepos\kds_automation
pytest tests\test_smoke.py
```

| Part | Meaning |
|------|--------|
| `pytest` | Pytest test runner (`pytest.ini` adds `-q` and discovers under `tests/`). |
| `tests\test_smoke.py` | Only config/data/helper checks; fast local validation. |

**Result:** **Pass** = YAML order data and kitchen utilities look consistent. **Fail** = bad or incomplete `config/*.yaml`, `data/orders.json`, or changed helpers. This does **not** prove tablets or Appium work.

#### 2. Functional tests (pilot app — needs Appium + device)

```powershell
pytest -m functional --preflight-roles pilot
```

| Part | Meaning |
|------|--------|
| `-m functional` | Runs tests marked `@pytest.mark.functional` (see `tests/test_pilot_functional.py`). |
| `--preflight-roles pilot` | One-time preflight checks **only** the **pilot** role (UDID + app). Omit to preflight **all** roles listed in `config/devices.yaml`. |

Run a **single** test:

```powershell
pytest tests\test_pilot_functional.py::test_pilot_station_elements_and_drop_sides --preflight-roles pilot
```

| Part | Meaning |
|------|--------|
| `::test_pilot_station_elements_and_drop_sides` | That one test function only. |

#### 3. E2E order flow (`tests/test_order_end_to_end.py`)

```powershell
pytest tests\test_order_end_to_end.py -m e2e --channel tablet --order sample_order --preflight-roles pilot
```

| Part | Meaning |
|------|--------|
| `-m e2e` | Only tests marked `@pytest.mark.e2e`. |
| `--channel web` \| `api` \| `tablet` | **web** = Playwright POS; **api** = HTTP POST from `data/orders.json`; **tablet** = no web/API submit, only KDS validation on tablets. |
| `--order sample_order` | Key in **`data/orders.json`**. Defaults can come from env **`TEST_CHANNEL`** / **`TEST_ORDER_PROFILE`**. |
| `--preflight-roles pilot` | Limit preflight to these roles (comma-separated). |

#### 4. Skip preflight

```powershell
pytest -m functional --skip-preflight
```

| Part | Meaning |
|------|--------|
| `--skip-preflight` | Skips the one-time Appium “session + app installed” check (faster; fails later if env is wrong). |

#### 5. Device screen recording (MP4 under `reports\videos`)

```powershell
pytest -m functional --preflight-roles pilot --record-device-video --video-role pilot
```

| Part | Meaning |
|------|--------|
| `--record-device-video` | Runs `adb screenrecord` per matching test (see `tests/conftest.py`). |
| `--video-role pilot` | Uses **pilot**’s `udid` from `config/devices.yaml`. |

#### 6. HTML report (pytest-html)

```powershell
pytest -m functional --preflight-roles pilot --html=reports\html\report.html --self-contained-html
```

| Part | Meaning |
|------|--------|
| `--html=...` | Output path for the HTML report. |
| `--self-contained-html` | Single file with assets inlined (easy to open or share). |

#### 7. Common pytest flags (any command)

| Flag | Meaning |
|------|--------|
| `-q` | Quiet (already applied via `pytest.ini` **addopts** unless overridden). |
| `-v` | Verbose — print each test name. |
| `-k pilot_station` | Run tests whose names contain `pilot_station`. |
| `--collect-only` | List tests that would run; do not execute. |

**Before functional/E2E:** start **Appium** (`appium`), connect devices (`adb connect …`), and align `config/devices.yaml` + `config/capabilities.yaml`.

### Python, venv, and dependencies

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
pip install requests
python -m pytest -q
```

### Playwright (web POS channel)

```powershell
playwright install chromium
```

### Appium server and UiAutomator2 driver

```powershell
npm i -g appium
appium driver install uiautomator2
appium driver list --installed
appium
appium --allow-cors
```

### Verify Appium is listening

```powershell
curl.exe http://127.0.0.1:4723/status
```

### ADB and devices

```powershell
adb devices -l
adb kill-server
adb start-server
adb pair 10.0.0.183:<pair_port>
adb connect 10.0.0.183:<connect_port>
adb -s <udid> shell cmd package resolve-activity --brief com.loyverse.sale
where adb
adb version
adb shell dumpsys package com.your.package | findstr permission
```

### Repo helper scripts

```powershell
powershell -File scripts\check_android_devices.ps1
powershell -File scripts\connect_android_wifi.ps1 -DeviceIp 10.0.0.183 -Port 5555
```

### Pytest — smoke, E2E, functional, preflight

```powershell
pytest
pytest -q
pytest tests\test_smoke.py -q
pytest tests\test_order_end_to_end.py -m e2e --collect-only -q
pytest -m e2e --preflight-roles pilot
pytest -m functional --preflight-roles pilot
pytest tests\test_pilot_functional.py::test_pilot_station_elements_and_drop_sides --preflight-roles pilot
pytest -m functional -k pilot_station --preflight-roles pilot
pytest -m e2e --preflight-roles pilot,gunner
pytest -m e2e --skip-preflight
```

### Pytest — channels, order profile, video, Allure

```powershell
pytest tests\test_order_end_to_end.py -m e2e --channel web --order sample_order
pytest tests\test_order_end_to_end.py -m e2e --channel api --order api_full_ticket
pytest tests\test_order_end_to_end.py -m e2e --channel tablet --order sample_order --preflight-roles pilot
pytest -m functional --preflight-roles pilot --record-device-video --video-role pilot
pytest --alluredir=reports\allure-results
```

### Allure report (requires Allure CLI installed)

```powershell
allure serve reports\allure-results
```

### HTML execution report (pytest-html)

After `pip install -r requirements.txt`, **every** `pytest` run (via `pytest.ini`) writes **`reports/html/report.html`** (`--self-contained-html`).

- Open: `start reports\html\report.html` (PowerShell) or from Explorer.
- Disable for one run: `pytest -p no:html`.
- Custom path (optional): `pytest --html=reports\html\functional_report.html --self-contained-html` (alongside other flags).

## Layout

- `config/` — devices, env, Appium capabilities (common + per-app).
- `drivers/` — Appium factory, Playwright factory, `DeviceManager` (one session per role).
- `pages/` — POM: `web/`, `mobile/` (gunner, bombardier, wingman, pilot).
- `flows/` — cross-surface flows.
- `actions/` — reusable mobile/web helpers.
- `tests/` — Pytest + `conftest.py` fixtures.

Replace placeholder **accessibility id** roots in `pages/mobile/*_page.py` with your real selectors.

## Next Steps for Actual Apps

Use this rollout order to move from scaffold to real production apps.

1. **Map real devices/emulators per role**
   - Set real `udid` values in `config/devices.yaml` for `gunner`, `bombardier`, `wingman`, `pilot`.
   - If you are onboarding gradually, run with `--preflight-roles` for a subset first.

2. **Set real Appium capabilities**
   - Update `config/capabilities.yaml` with real `appium:appPackage` and `appium:appActivity` per role.
   - If needed, add `appium:app` APK path per role.

3. **Implement real selectors in page objects**
   - Replace placeholders in `pages/mobile/*_page.py` with stable ids (`accessibility id` / resource-id).
   - Keep XPath usage minimal and targeted.

4. **Implement order submission for your channels**
   - `web`: complete `PosPage.place_order_from_data()` in `pages/web/pos_page.py`.
   - `api`: set `api.orders_submit_url` in `config/env.yaml` and align payload/headers in `services/order_api.py`.

5. **Align test data with what tablets actually display**
   - Update `data/orders.json` with real item names and tags.
   - Keep `order_number` and `qty`.
   - Tune `kitchen.line_text_format` in `config/env.yaml` to match UI text rendering.

6. **Run a small pilot first, then scale**
   - Start with one app/role (for example `pilot`) and one order profile.
   - Expand to `gunner`, then `bombardier`, then `wingman`.

### First real-run command

```bash
pytest tests\test_order_end_to_end.py -m e2e --channel web --order multi_station_order --preflight-roles pilot,gunner
```
