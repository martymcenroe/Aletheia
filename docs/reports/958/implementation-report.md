# Implementation Report — Issue #958

## What changed

`workers/aletheia-api/wrangler.toml` now records the Worker's triggers:

- `api.aletheia.study/*` on zone `aletheia.study`, the route that existed before (report 349), kept until the domain lapses on 2026-11-13 at 5:03:30 PM Central.
- `aletheia-api.thrivetech.ai` as a custom domain. CloudFlare created its proxied DNS record in the `thrivetech.ai` zone.
- `workers_dev = false`, stated so a deploy never toggles it by default.

## How it was applied

`wrangler triggers deploy` in `workers/aletheia-api/`, on 2026-11-13 at about 2:57 PM Central. It applies routes and domains only; the Worker's code was not uploaded. wrangler 4.154.0, fleet account `4fe1c5e241425c85d0f2c35c69fb45b8`. Output:

```
Deployed aletheia-api triggers (1.33 sec)
  api.aletheia.study/* (zone name: aletheia.study)
  aletheia-api.thrivetech.ai (custom domain)
```

## After the lapse

Remove the `api.aletheia.study/*` entry and run `wrangler triggers deploy` again. That is part of the move tracked in #954.
