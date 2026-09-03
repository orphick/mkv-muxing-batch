# Changelog

All notable changes to the maintained `orphick/mkv-muxing-batch` fork are
documented here.

Project provenance marker: `ORPHICK-MRM-20260903-2C42BF7`

## [Unreleased]

### Documentation

- Added explicit copyright and provenance information for the substantial
  maintenance, interface redesign, reliability, testing, and Windows release
  work authored by Mohammadreza Mahdavi (`@orphick`) in 2026.
- Embedded a stable provenance marker in source, diagnostic, and packaged
  application metadata so downstream copies can be identified without
  affecting application behavior or user data.

## [2.7.5] - 2026-09-03

### Fixed

- Fixed a native Windows GDI handle leak caused by recreating the taskbar
  overlay icon on every mux progress update. Long queues could exhaust the
  process GUI-resource limit, leaving muxing active while Qt could no longer
  repaint or interact with the window.
- Reused unchanged taskbar overlay icons, released replaced and cleared native
  icon handles, and coalesced duplicate taskbar progress values.
- Fixed Qt5 checkbox-state handling that could raise an exception when changing
  the source subtitle, audio, or existing-track options.

### Verification

- Verified 10,000 taskbar updates kept the real Windows GDI count at 16 after
  the overlay was cleared, instead of growing with every update.
- Passed all 43 tests under Qt6 and Qt5; the Qt5 run retained two expected
  MKVToolNix integration skips in the development environment.

## [2.7.4] - 2026-09-02

### Added

- Added persistent diagnostic logging for startup, Qt messages, mux and CRC job
  transitions, uncaught exceptions, and native crashes.
- Added an independent GUI watchdog that records Python thread dumps when the
  interface stops responding for ten seconds and records later recovery.
- Added runtime details for the application, Python, Windows, and Qt binding to
  each diagnostic session.

### Verification

- Verified the packaged Qt5/PySide2 application opened a responsive window.
- Verified the diagnostic logger and GUI watchdog in the packaged application.
- Verified the portable archive contains the Qt5/PySide2 runtime and bundled
  MKVToolNix tools without Qt6/PySide6.

[Unreleased]: https://github.com/orphick/mkv-muxing-batch/compare/2.7.5...HEAD
[2.7.5]: https://github.com/orphick/mkv-muxing-batch/releases/tag/2.7.5
[2.7.4]: https://github.com/orphick/mkv-muxing-batch/releases/tag/2.7.4
