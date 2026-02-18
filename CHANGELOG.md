# Changelog

All notable changes to this project are documented here.

## v1.1-secure - 2026-02-18

### Security & Hardening
- Implemented P0/P1 hardening: global CSRF, login rate limiting, secure headers/cookies.
- Added DB performance/security indexes via migration.
- Added verification report and automated checks.
- Implemented P2 hardening pass:
  - Password complexity policy enforcement.
  - Stronger input validators across key forms.
  - Targeted exception handling improvements.

### Performance
- Fixed N+1 query pattern in vehicle listing.
- Added pagination improvements for major lists.

### Quality & Testing
- Added security + rate-limit tests.
- Added password policy tests.
- Verified with pytest and compile checks.

## Commit Highlights
- `1f83eb1` P2 hardening pass: password policy, stronger validators, targeted exception handling, tests
- `c56be3f` Implement P0/P1: CSRF+rate limit, N+1 fixes, indexes, tests, verification report
- `8089a23` Vehicle bookings module + dashboard upcoming bookings
- `f91cc22` Dashboard: upcoming scheduled trips (next 7 days)
- `1b89fcc` Dashboard: vehicles inside/outside mill counts
- `c48f0ce` Dashboard drill-down filters + list page filters
- `0ed0cf7` Dashboard: daily focus (trips by time_out)
- `df17c8f` Trips report: lock best-practice column order (CSV+PDF)
- `e61c789` Reports: landscape PDFs + add trip odo/time columns
- `ec62bc6` Trip closure expenses + documents/incidents modules
