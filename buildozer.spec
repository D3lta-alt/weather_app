[app]

# ── Identity ────────────────────────────────────────────────────────────────
title = WeatherPeek
package.name = weatherpeek
package.domain = org.weatherpeek
version = 1.0

# ── Source ──────────────────────────────────────────────────────────────────
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf

# ── Entry point ──────────────────────────────────────────────────────────────
entrypoint = main.py

# ── Requirements ─────────────────────────────────────────────────────────────
# Note: kivy is pulled in automatically by buildozer; requests is added here.
requirements = python3,kivy,requests,certifi,charset-normalizer,idna,urllib3

# ── Orientation & Display ────────────────────────────────────────────────────
orientation = portrait
fullscreen = 0

# ── Android ──────────────────────────────────────────────────────────────────
android.permissions = INTERNET, ACCESS_NETWORK_STATE
android.api = 33
android.minapi = 21
android.ndk = 25b
android.accept_sdk_license = True
android.arch = arm64-v8a

# ── iOS ───────────────────────────────────────────────────────────────────────
# ios.kivy_ios_url = https://github.com/kivy/kivy-ios
# ios.kivy_ios_branch = master

# ── Log ──────────────────────────────────────────────────────────────────────
log_level = 2

# ── Buildozer internals ───────────────────────────────────────────────────────
[buildozer]
warn_on_root = 1
