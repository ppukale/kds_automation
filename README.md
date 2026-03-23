# QSR automation framework

Python + Pytest + Appium (Android tablets) + Playwright (web POS). Layout: **pages** (POM), **flows** (business orchestration), **actions** (low-level UI), **drivers** (sessions).

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
```

## Configuration

1. Edit `config/devices.yaml` — set each **UDID** from `adb devices` (see [Android Studio emulators](#android-studio-emulators) below).
2. Edit `config/capabilities.yaml` — set real `appium:appPackage`, `appium:appActivity`, and optional `appium:app` APK paths.
3. Edit `config/env.yaml` — POS **base_url**, Appium **server_url**.

Optional: add `config/local.yaml` (gitignored) to override `env.yaml` without editing committed files.

### Android Studio emulators

Use **AVDs** (Android Virtual Devices) the same way as physical devices: Appium attaches to the emulator **serial** shown by ADB.

1. Install **Android Studio** and the **SDK** (platform tools include `adb`).
2. Open **Device Manager** → create or start one AVD per role you need (e.g. five AVDs for gunner, bombardier, wingman, pilot, expo), or run fewer AVDs and map multiple roles only after you understand parallel limits.
3. With each emulator booted, run **`adb devices`** — emulators appear as `emulator-5554`, `emulator-5556`, etc. (first booted is usually `5554`, next `5556`, …).
4. Copy those serials into `config/devices.yaml` as each role’s `udid`.
5. Keep **`kind: emulator`** on those entries so `emulator_common` caps from `capabilities.yaml` apply (e.g. auto-grant permissions, disable window animation). For real hardware, use `kind: device` or remove `kind` and add a `device_common` block later if you need it.

Ensure `adb` is on your `PATH` (typical Windows SDK path: `%LOCALAPPDATA%\Android\Sdk\platform-tools`). Start **Appium 2** (`appium`) before tests; use the same `appium:server_url` as in `config/env.yaml`.

Quick check from the repo root: `powershell -File scripts/check_android_devices.ps1`

## Run tests

```bash
pytest
```

Smoke tests load YAML only. End-to-end tests are skipped unless:

```bash
set RUN_E2E=1
pytest -m e2e
```

### Channel and order profile (E2E)

- **`--channel web`** — submit via Playwright POS (`web.base_url`); default.
- **`--channel api`** — POST JSON from `data/orders.json` to **`api.orders_submit_url`** in `config/env.yaml`.

Pick the order payload by key in **`data/orders.json`**:

```bash
set RUN_E2E=1
pytest tests\test_order_end_to_end.py -m e2e --channel web --order sample_order
pytest tests\test_order_end_to_end.py -m e2e --channel api --order api_full_ticket
```

You can also set **`TEST_CHANNEL`** and **`TEST_ORDER_PROFILE`** env vars instead of flags.

Configure **`api.orders_submit_url`** before using `--channel api` (empty URL raises a clear error).

### Device/app preflight before E2E

For tests marked `integration`/`e2e`, the framework runs a one-time preflight (when `RUN_E2E=1`) before the first test:

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

## Layout

- `config/` — devices, env, Appium capabilities (common + per-app).
- `drivers/` — Appium factory, Playwright factory, `DeviceManager` (one session per role).
- `pages/` — POM: `web/`, `mobile/` (gunner, bombardier, wingman, pilot, expo).
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
set RUN_E2E=1
pytest tests\test_order_end_to_end.py -m e2e --channel web --order multi_station_order --preflight-roles pilot,gunner
```
