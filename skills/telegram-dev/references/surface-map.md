# Official source and API map

| Intent | Start here | Important distinction |
|---|---|---|
| Bot messages, commands, updates, keyboards, files, payments | https://core.telegram.org/bots/api and https://core.telegram.org/bots/features | HTTPS Bot API; inspect actor, chat and business connection restrictions per method. |
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
| Website/mobile sign-in | https://core.telegram.org/bots/telegram-login | Current Telegram Login library/native SDKs/OIDC; distinguish archived widget authentication. |
| Legacy login widget and URL authorization | https://core.telegram.org/widgets/login-legacy and https://core.telegram.org/api/url-authorization | Existing widget and login URL flows use their own verification rules; do not apply Mini App authentication. |
| Website sharing and post widgets | https://core.telegram.org/widgets | Embedding/sharing is distinct from authentication and Bot API messaging. |
| Passport | https://core.telegram.org/passport | Separate identity-document integration. |
| Instant View | https://instantview.telegram.org/docs | Article templates; not Mini Apps. |
| Themes | https://core.telegram.org/api/themes | Client themes; distinct from Mini App theme parameters. |

## Feature-family entrypoints

The links below route to documentation rather than duplicate method catalogs. Some features have Bot API, TDLib and raw Telegram API variants with different permissions; inspect the selected method instead of transferring rules between them.

| Family | Official sources | Read with |
|---|---|---|
| Business account features and connected bots | https://core.telegram.org/api/business ; https://core.telegram.org/api/bots/connected-business-bots | `business-and-commerce.md` |
| Digital/physical payments and Stars | https://core.telegram.org/bots/payments-stars ; https://core.telegram.org/bots/payments ; https://core.telegram.org/api/stars | `business-and-commerce.md` |
| Subscriptions, paid media, paid messages and suggested posts | https://core.telegram.org/api/subscriptions ; https://core.telegram.org/api/paid-media ; https://core.telegram.org/api/suggested-posts ; follow current index for paid messages | `business-and-commerce.md` |
| Gifts, collectible upgrades/transfers/auctions, boosts and giveaways | https://core.telegram.org/api/gifts ; follow current index for auctions/boosts/giveaways | `business-and-commerce.md` |
| Stories and story privacy/areas | https://core.telegram.org/api/stories ; current Bot API story methods | `business-and-commerce.md` |
| Groups/channels, rights, topics and direct messages | https://core.telegram.org/api/channel ; https://core.telegram.org/api/rights ; https://core.telegram.org/api/forum ; https://core.telegram.org/api/monoforum | `groups-and-channels.md` |
| Auth, 2FA, QR and passkeys | https://core.telegram.org/api/auth ; https://core.telegram.org/api/passkeys ; follow auth links for the chosen mechanism | `client-development.md` |
| Client updates, peer state and errors | https://core.telegram.org/api/updates ; https://core.telegram.org/api/errors ; https://core.telegram.org/tdlib/getting-started | `client-development.md` |
| One-to-one/group calls and secret chats | https://core.telegram.org/api/calls ; https://core.telegram.org/api/group-calls ; https://core.telegram.org/api/end-to-end ; https://core.telegram.org/mtproto/security_guidelines | `client-development.md` |
| MTProto upload/download and expired references | https://core.telegram.org/api/files ; https://core.telegram.org/api/file_reference | `feature-checks.md` |

For search, folders, drafts, Saved Messages, contacts, blocklist, privacy, scheduled messages, translation/transcription, polls/checklists, reactions/effects/statuses, themes/wallpapers, statistics, ads, verification, Premium/collectibles and takeout, start at https://core.telegram.org/api and select the matching article. Follow its schema links for exact types and availability. For evolving bot features such as managed bots, guest queries, bot-to-bot communication, AI assistants, rich messages, private topics and ephemeral responses, start with https://core.telegram.org/bots/features and the live Bot API. Never infer these are unsupported from a skill's static topic list.

## Release sources

- Bot API: https://core.telegram.org/bots/api-changelog and recent changes at https://core.telegram.org/bots/api
- Mini Apps: release sections at https://core.telegram.org/bots/webapps
- Telegram API layers: https://core.telegram.org/api/layers
- TDLib: https://github.com/tdlib/td/blob/master/CHANGELOG.md
- Product announcements and archive links: https://telegram.org/blog
- Official product evolution timeline: https://telegram.org/evolution
- Official client repository links: https://telegram.org/apps

Keep API version, TL layer, TDLib version, client version, SDK version and publication date separate. Do not compare their numeric versions as one sequence. Record URL, section, applicable version/layer when stated, and retrieval date. An old changelog stays historical even when fetched today.

The runtime indexes fetched public documentation and selected official repository files. Coverage depends on the installation's actual corpus status; the skill files alone are not a downloaded documentation mirror. The index does not mirror all client source repositories or reconstruct every past documentation revision. When client behavior requires source-code investigation, start from the official apps page, pin the repository revision, and mark the result as a code observation.
