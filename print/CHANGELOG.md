## 0.1.0
- Initial release. Stateless HTTP service that renders + prints to an IP-connected 80mm ESC/POS thermal printer (Xprinter XP-80T compatible).
- Endpoints: `GET /api/health`, `POST /api/print/shopping-list`, `POST /api/print/recipe`.
- Forces `CP858` codepage for correct å/ä/ö rendering; partial cut with 6-line feed.
- Sibling-accessible on port `8100` for HA-stock / HA-recipes / HA service-call integrations.
