# Feature-specific implementation checks

## Text and entities
- Distinguish Bot API HTML/MarkdownV2 parsing from raw message entities and website HTML/CSS.
- Compute offsets and lengths in UTF-16 code units where specified; do not use Python character counts or UTF-8 byte lengths as substitutes.
- Test emoji before and inside the styled span, escaping, nesting, links, spoilers and code blocks that the actual request uses.
- Check captions separately from message text and preserve their current restrictions.

## Emoji and stickers
- Distinguish Unicode emoji, custom emoji in text, emoji statuses, reactions, message effects, stickers and sticker sets.
- Verify identifier types, current entitlement/actor restrictions and fallback rendering.
- Inspect the actual asset dimensions, duration, frame rate, file size, encoding and transparency as applicable. Static, animated and video assets have different requirements.
- “Animate this emoji” may request asset creation; “send this custom emoji” requires supported Telegram representation and identifiers. Resolve from context.

## Voice and video notes
- For Bot API inspect `sendVoice`, `sendAudio`, `sendVideo`, `sendVideoNote` and their documented differences.
- A круг/кружок normally means a video note: verify that the request and returned message use that type. Do not claim an ordinary square video has achieved it.
- Probe and, when needed, convert local media; check actual codec/container, aspect ratio, duration and size against the selected method's current requirements.
- Voice, audio and file attachments may display differently even when they share underlying audio data.
- Upload success and client playback/rendering are distinct checks.

## Mini Apps
- Verify the launch mechanism, supported client/version, theme, viewport and safe-area behavior relevant to the feature.
- Validate initData on the server according to the official algorithm and the chosen verification mode; do not trust initDataUnsafe for authentication.
- Check freshness/replay handling, user/session binding and server-side permissions.
- Do not assume Mini Apps inherit every bot or user-account capability.

## Payments, Stars and business
- Determine the product, payment mechanism, payer/recipient, account type and applicable current Telegram requirements before selecting methods.
- Follow the documented invoice, checkout, successful-payment and refund flows applicable to the task.
- Verify business connection rights and current method support. A business connection is not unrestricted user access.

## Client APIs and updates
- Verify bot versus user authorization for each chosen method.
- Keep peer identifiers and access hashes distinct from Bot API chat identifiers.
- Use the library's documented session/update synchronization and flood-wait handling; avoid blind retries of non-idempotent operations.
- For platform-specific rendering, inspect the matching official client at a recorded revision and verify behavior in that client where possible.
