# Deploy contract — Sabby Roadtrip site

Frank → MediaServer hand-off. Everything you need to host the container at
`https://roadtrip.tomjohnell.com`.

## Image

| Field | Value |
| --- | --- |
| Registry | `ghcr.io` |
| Image | `ghcr.io/tldev/roadtrip` |
| Rolling tag | `:latest` |
| Pinned tags | `:sha-<short>` per commit (rollback target) |
| Visibility | Public (no pull token needed) |
| Architectures | `linux/amd64` |
| Build trigger | GitHub Actions on push to `master` |

## Runtime contract

| Setting | Value |
| --- | --- |
| Internal port | `8080` |
| Healthcheck | `GET /healthz` → `{"status":"ok","version":"<sha>","ts":"..."}` |
| Healthcheck interval | 30 s, 5 s timeout, 10 s start period |
| User | non-root (`app`) |
| Persistent volume | `/data` (SQLite lives here in slice 2; safe to create empty in slice 1) |
| Logs | stdout / stderr |

### Environment variables

| Var | Required | Slice | Notes |
| --- | --- | --- | --- |
| `PORT` | no | 1 | Defaults to 8080. |
| `GIT_SHA` | no | 1 | Baked at build time; surfaced in `/healthz`. |
| `TRIP_DATE_OVERRIDE` | no | 1 | `YYYY-MM-DD`; pin "today" for demos / testing. |
| `ADMIN_TOKEN` | yes (slice 2) | 2 | Long random string. Anyone with this can push location pings. Rotate via redeploy. |
| `COOKIE_SECRET` | yes (slice 2) | 2 | 32+ bytes; signs the admin cookie. Rotate via redeploy. |
| `HCAPTCHA_SITEKEY` | yes (slice 2) | 2 | Public key, exposed to browser. |
| `HCAPTCHA_SECRET` | yes (slice 2) | 2 | Server-side hCaptcha secret. |

### Cookie policy (slice 2)

`SameSite=Lax`, `HttpOnly`, `Secure`, `Path=/`, ~30-day `Max-Age`. Set
behind TLS only. Reverse proxy must forward `X-Forwarded-Proto` for the
app to recognise the connection as secure.

## docker-compose snippet (drop into MediaServer)

```yaml
services:
  sabby-roadtrip:
    image: ghcr.io/tldev/roadtrip:latest
    container_name: sabby-roadtrip
    restart: unless-stopped
    pull_policy: always
    ports:
      - "127.0.0.1:8081:8080"   # MediaServer reverse proxy fronts this
    volumes:
      - sabby-roadtrip-data:/data
    environment:
      # Slice 1 needs none. Slice 2 wires these in.
      # ADMIN_TOKEN: "<set in MediaServer secrets>"
      # COOKIE_SECRET: "<set in MediaServer secrets>"
      # HCAPTCHA_SITEKEY: "<set in MediaServer secrets>"
      # HCAPTCHA_SECRET: "<set in MediaServer secrets>"
    healthcheck:
      test: ["CMD", "wget", "-qO-", "http://127.0.0.1:8080/healthz"]
      interval: 30s
      timeout: 5s
      start_period: 10s
      retries: 3
    labels:
      com.centurylinklabs.watchtower.enable: "true"

volumes:
  sabby-roadtrip-data:
```

Reverse proxy: terminate TLS for `roadtrip.tomjohnell.com`, forward
to `127.0.0.1:8081`, set `X-Forwarded-Proto: https`. No rewrites needed.

## Auto-update

Watchtower polling `:latest` every 5 minutes is the chosen mechanism. The
compose label above opts the container in. If MediaServer's Watchtower runs
in *label-mode*, that's the entire wiring — no further config.

```yaml
watchtower:
  image: containrrr/watchtower
  command: --label-enable --interval 300 --cleanup
  volumes:
    - /var/run/docker.sock:/var/run/docker.sock
```

## iOS Shortcuts ping recipe (slice 2)

For Tom & Kay to push location from the lockscreen without opening the site.

1. Shortcuts → New Shortcut → "Ping Sabby"
2. Action: **Get Current Location**
3. Action: **Get Contents of URL**
   * URL: `https://roadtrip.tomjohnell.com/api/location`
   * Method: `POST`
   * Headers:
     * `Authorization`: `Bearer <ADMIN_TOKEN>`
     * `Content-Type`: `application/json`
   * Request Body (JSON):
     ```json
     {
       "lat": <Latitude of Current Location>,
       "lng": <Longitude of Current Location>,
       "label": "On the road"
     }
     ```
4. Add to Lock Screen / Home Screen as a one-tap action.

The slice-2 `POST /api/location` accepts both bearer-token and signed-cookie
auth — the bearer path is for the iOS Shortcut, the cookie path is for the
admin web button.

## Rollback

```sh
docker pull ghcr.io/tldev/roadtrip:sha-<short>
docker tag ghcr.io/tldev/roadtrip:sha-<short> ghcr.io/tldev/roadtrip:latest
docker compose up -d sabby-roadtrip
```

Or skip the retag and edit the compose `image:` line to the pinned `sha-…` tag and `up -d`.

## Smoke-test checklist (post-deploy)

- [ ] `https://roadtrip.tomjohnell.com/healthz` returns 200 with current `version`
- [ ] `https://roadtrip.tomjohnell.com/` loads, "Today / Tomorrow / Full Trip" tabs render
- [ ] Map view draws all stops + polylines
- [ ] Watchtower picks up a new `:latest` push within ~5 min (verify with one trivial commit)
