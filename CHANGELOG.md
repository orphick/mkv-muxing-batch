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

[Unreleased]: https://github.com/orphick/mkv-muxing-batch/compare/2.7.4...HEAD
[2.7.4]: https://github.com/orphick/mkv-muxing-batch/releases/tag/2.7.4
