# Mini Apps, web authentication and external integrations

Read only the relevant surface. Website sign-in, Mini App launch authentication, a Telegram account session, login URL authorization, verification-code delivery and Passport are separate protocols. Determine the user's actual surface before choosing one.

## Mini App lifecycle and bridge

Identify the launch mechanism: keyboard, inline/menu button, main Mini App, direct link, inline mode or another documented entrypoint. Available data and send/return behavior depend on launch context. Inspect the supported bridge version and client capabilities before using newer methods. Keep the existing application and adapt the appropriate integration instead of producing only a browser mockup.

Use current theme, viewport, keyboard, safe-area and fullscreen semantics relevant to the design. Handle events and cleanup across navigation rather than sizing the layout once from desktop browser dimensions. Request contact, location, write access or other capabilities through the documented user flow; unsupported/denied permissions need usable UI behavior. Test at least the actual client/platform implicated by the request.

Source: [Mini App specifications and releases](https://core.telegram.org/bots/webapps).

## Launch authentication

Send raw `initData` to the backend and validate it with the official algorithm for the chosen trust model. Bot-token HMAC verification and third-party public-key signature verification have different data construction; do not mix them. The third-party mode does not require disclosure of the bot token. `initDataUnsafe`, decoded user fields and URL parameters are not independently authenticated.

Bind validated data to the intended bot/environment and application session. Check authentication age with a justified expiry policy and protect authenticated mutations from replay/session confusion. Preserve the exact serialized fields through verification, then parse the verified data. Test tampering, stale payloads and production/test-environment mismatch using the actual backend path.

Source: [validating Mini App data](https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app) and [third-party validation](https://core.telegram.org/bots/webapps#validating-data-for-third-party-use).

## Website and native-mobile Telegram Login

Read the current [Telegram Login](https://core.telegram.org/bots/telegram-login) documentation. It describes a Login library, native SDKs and OIDC Authorization Code Flow with PKCE. Do not build a new integration solely from a remembered legacy iframe/HMAC example. Conversely, preserve the project's existing legacy flow unless migration is requested or necessary; use [the archived widget](https://core.telegram.org/widgets/login-legacy) for its own verification specification.

For OIDC, use the existing suitable authentication library with current discovery/endpoints, registered allowed URLs and server-side code exchange. Validate the ID token's signature, issuer, audience, lifetime and flow-bound nonce where used; protect redirect initiation with state and the chosen PKCE flow. Request only scopes required by the task and verify grants rather than inferring a phone number or permission to send messages from any successful sign-in. Avoid turning OIDC claims into a Telegram account/MTProto session.

For [seamless URL authorization](https://core.telegram.org/api/url-authorization) or a Bot API login URL, implement its documented URL/domain and data checks. These are not Mini App `initData`.

## Deep links and sharing

Choose a link family matching the intent: bot start/startgroup, Mini App launch/startapp, invite/join, message/thread, username/profile, share, invoice or a client-specific `tg://` route. Follow [deep-link rules](https://core.telegram.org/api/links) and [bot start parameters](https://core.telegram.org/bots/features#deep-linking). Encode and validate parameters, preserve the destination and test the expected client/web fallback. A link itself does not authenticate its user or authorize a paid/actionable operation; use short-lived server-side state when linking identities.

## Other integrations

- [Gateway](https://core.telegram.org/gateway): verification-code delivery and verification/delivery-status lifecycle, not arbitrary bot announcements. Read current status, retry and request-identity semantics for the intended flow.
- [Passport](https://core.telegram.org/passport): identity-document request/decryption/validation flow, not ordinary website login. Implement only the requested data types and handle relevant element errors.
- [Web widgets](https://core.telegram.org/widgets): sharing/post embedding has its own behavior; embedding a post does not establish access to private chat data.
- [Instant View](https://instantview.telegram.org/docs): article templates and rules, distinct from an app interface. Verify the actual article samples.

Authentication acceptance means the backend rejects invalid data and establishes the correct app session. A rendered login button or successfully decoded JSON is insufficient.
