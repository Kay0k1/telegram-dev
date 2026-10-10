# Messaging, media and file implementation checks

Read only the relevant section. For exact current fields/limits, open the linked official source and the selected method/type. Client appearance and upload acceptance are different verification levels.

## Text and entities
- Distinguish Bot API HTML/MarkdownV2 parsing from raw message entities and website HTML/CSS.
- Compute offsets and lengths in UTF-16 code units where specified; do not use Python character counts or UTF-8 byte lengths as substitutes.
- Test emoji before and inside the styled span, escaping, nesting, links, spoilers and code blocks that the actual request uses.
- Check captions separately from message text and preserve their current restrictions.
- Distinguish regular text/entities from the newer rich-message structures and their allowed markup. Inspect the live specification before deciding a table, structured block or embedded interaction requires a Mini App. Do not paste arbitrary browser HTML/CSS into an API that supports only a documented subset.

Sources: [message entities](https://core.telegram.org/api/entities), [regular formatting](https://core.telegram.org/bots/api#formatting-options), [rich bot messages](https://core.telegram.org/bots/features#rich-messages).

## Emoji and stickers
- Distinguish Unicode emoji, custom emoji in text, emoji statuses, reactions, message effects, stickers and sticker sets.
- Verify identifier types, current entitlement/actor restrictions and fallback rendering.
- Inspect the actual asset dimensions, duration, frame rate, file size, encoding and transparency as applicable. Static, animated and video assets have different requirements.
- “Animate this emoji” may request asset creation; “send this custom emoji” requires supported Telegram representation and identifiers. Resolve from context.
- A sticker's semantic type (regular, mask, custom emoji) and its storage format (static, animated, video) are separate. Preserve the requested set type and editing operation; creating a local asset alone does not publish a usable Telegram set.

Sources: [sticker asset requirements](https://core.telegram.org/stickers), [client sticker operations](https://core.telegram.org/api/stickers), [custom emoji](https://core.telegram.org/api/custom-emoji). Button-specific checks are in [buttons and custom emoji](buttons-and-custom-emoji.md).

## Voice and video notes
- For Bot API inspect `sendVoice`, `sendAudio`, `sendVideo`, `sendVideoNote` and their documented differences.
- A круг/кружок normally means a video note: verify that the request and returned message use that type. Do not claim an ordinary square video has achieved it.
- Probe and, when needed, convert local media; check actual codec/container, aspect ratio, duration and size against the selected method's current requirements.
- Voice, audio and file attachments may display differently even when they share underlying audio data.
- Upload success and client playback/rendering are distinct checks.

Sources: [sendVoice](https://core.telegram.org/bots/api#sendvoice), [sendAudio](https://core.telegram.org/bots/api#sendaudio), [sendVideo](https://core.telegram.org/bots/api#sendvideo), [sendVideoNote](https://core.telegram.org/bots/api#sendvideonote).

## File transfer and albums

- Resolve whether the task needs a new upload, a reusable file identity, URL fetch, download, copy or forward. These have different behavior for captions, media type, attribution and protected content.
- Bot API `file_id` and `file_unique_id` serve different purposes; verify the current reuse scope and restrictions. Do not pass an identity intended for comparison as a downloadable/sendable file reference.
- Choose the documented cloud or local Bot API server behavior when upload/download limits matter. Do not claim a cloud-limit failure is a universal Telegram media limit, or deploy a new server without need.
- For raw Telegram API transfers, inspect part size/alignment, DC/CDN behavior, integrity, resumption and actual file-reference expiry. Refresh the source message/reference through the documented path rather than endlessly retrying an expired reference.
- Preserve album grouping and order, media compatibility, captions and expected per-message results. Sending several independent files is not proof of an album.
- Preserve credentials while downloading: Bot API file URLs may contain the token; avoid placing them in public logs or product HTML. A downloaded filename/extension does not verify the bytes or codec.

Sources: [Bot API file objects](https://core.telegram.org/bots/api#file), [local Bot API server](https://core.telegram.org/bots/api#using-a-local-bot-api-server), [MTProto files](https://core.telegram.org/api/files), [file references](https://core.telegram.org/api/file_reference).

## Other message types

For polls/quizzes, dice, locations/live locations, contacts, effects, reactions, checklists or paid media, inspect the matching message type and actor-specific method. Preserve its lifecycle: editing a live location, observing a vote, updating a checklist and buying locked media are not generic text sends. Check the exact update visibility and destination restrictions for the requested outcome.

Sources: [current Bot API](https://core.telegram.org/bots/api), [Telegram API family index](https://core.telegram.org/api). For administration and conversation destinations use [groups and channels](groups-and-channels.md); commerce lifecycles use [business and commerce](business-and-commerce.md).
