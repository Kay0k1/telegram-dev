# Official source and API map

| Intent | Start here | Important distinction |
|---|---|---|
| Bot messages, commands, updates, keyboards, files, payments | https://core.telegram.org/bots/api | HTTPS Bot API; inspect actor, chat and business connection restrictions per method. |
| Embedded web interface | https://core.telegram.org/bots/webapps | JS bridge plus application backend and often Bot API. Check launch context, platform and supported version. |
| User-account operations, custom clients, detailed platform features | https://core.telegram.org/api | Telegram API over MTProto; authorization type still governs permissions. |
| Client implementation with local state/networking handled by a library | https://core.telegram.org/tdlib | TDLib's own types and methods differ from Bot API and raw TL schema. |
| Protocol and transport | https://core.telegram.org/mtproto | Distinguish protocol mechanics from application API methods. |
| Types, constructors, methods | https://core.telegram.org/schema | TL schema; follow links to related methods and constructors. |
| Message formatting | https://core.telegram.org/api/entities and Bot API “Formatting options” | API-specific parsing, entities, UTF-16 offsets; website HTML is a different surface. |
| Stickers and custom emoji | https://core.telegram.org/stickers ; https://core.telegram.org/api/stickers ; https://core.telegram.org/api/custom-emoji | Asset requirements, set operations, display permissions and message entities are separate concerns. |
| Files, voice messages, video notes | https://core.telegram.org/bots/api ; https://core.telegram.org/api/files | Check intended message type, media preparation and chosen API together. |
| Deep links | https://core.telegram.org/api/links | Link purpose and launch context matter. |
| Verification-code delivery | https://core.telegram.org/gateway | Distinct service; not arbitrary bot messaging. |
| Website widgets and login | https://core.telegram.org/widgets | Follow the particular current integration's authentication specification. |
| Passport | https://core.telegram.org/passport | Separate identity-document integration. |
| Instant View | https://instantview.telegram.org/docs | Article templates; not Mini Apps. |
| Themes | https://core.telegram.org/api/themes | Client themes; distinct from Mini App theme parameters. |

Use the main API index to discover further families: channels, topics, stories, reactions, calls, secret chats, business, Stars, gifts, Premium, search, privacy, admin permissions and updates. This table is a routing aid, not a claim that these are the only Telegram features.

## Release sources

- Bot API: https://core.telegram.org/bots/api-changelog and recent changes at https://core.telegram.org/bots/api
- Mini Apps: release sections at https://core.telegram.org/bots/webapps
- Telegram API layers: https://core.telegram.org/api/layers
- TDLib: https://github.com/tdlib/td/blob/master/CHANGELOG.md
- Product announcements and archive links: https://telegram.org/blog
- Official product evolution timeline: https://telegram.org/evolution
- Official client repository links: https://telegram.org/apps

Keep API version, TL layer, TDLib version, client version, SDK version and publication date separate. Do not compare their numeric versions as one sequence. Record URL, section, applicable version/layer when stated, and retrieval date. An old changelog stays historical even when fetched today.

The bundled index includes linked public documentation and selected official repository files. It does not mirror all client source repositories or reconstruct every past documentation revision. When client behavior requires source-code investigation, start from the official apps page, pin the repository revision, and mark the result as a code observation.
