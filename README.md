# CraftCore API

Backend for a Minecraft server's meta-game: players, economy and transfers, shops with inventory, market, clans, parties, quests, referrals, voting, mailing, moderation (arrests, safety), localization and quality-of-life settings. FastAPI + Tortoise ORM on PostgreSQL. Consumers are a Telegram bot, a Discord bot and the in-game plugin [CraftSocial](https://github.com/proger-exe/craftsocial).

Around 18k lines of Python, 15 routers, startup migrations, structured logging. Deployed with a Gitea Actions pipeline to a systemd service (see `deploy/`).

## Auth model

- Every request carries `X-Player-ID`: whose behalf the call is made on.
- The system account (`777000`, used for admin operations) additionally requires `Authorization: Bearer <service JWT>`. Trusted services obtain the JWT from `POST /integrations/auth/token` with `client_id` / `client_secret` configured in `SERVICE_CREDENTIALS`.

## Run

```bash
pip install -r requirements.txt
cp .env.example .env         # DB_*, JWT_SECRET, SERVICE_CREDENTIALS
uvicorn main:app --reload    # Swagger UI at /, ReDoc at /redoc, schema at /openapi.json
```

Schema is created on first start; later changes go through `core/models/startup_migrations.py` (see `docs/DATABASE_MIGRATIONS.md`).

## Layout

```
main.py                 app factory, error handlers, request log, CORS
settings.py             .env via SimpleConfig
api/routers/            admin, integrations, user (economics, localization, mailing, players, qol, safety, social)
api/schemas/            pydantic request/response models
core/models/            Tortoise models + startup migrations
core/managers/          domain logic: economics, shops, market, clans, party, quests, mailing, safety, voting, ...
core/shared/            errors, logger, helpers
docs/                   API.md (full endpoint reference), MODELS.md, SHOPS.md, TRANSFERS.md, ARRESTS.md, LOCALIZATION.md
scripts/                one-off maintenance scripts
deploy/                 deploy.sh + systemd unit
```

There is no test suite in this repo; the API is exercised by the bot and plugin integration.

## License

MIT
