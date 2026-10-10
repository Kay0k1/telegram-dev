# Colored buttons and premium/custom emoji

These cases come from the user's reported failures. The examples below were checked against the official Bot API on 2026-10-10. Recheck the live specification when implementing; this date is not a release date.

## “Сделай красную кнопку”

Determine the actual surface from the project: reply keyboard, inline keyboard, Mini App content, or a native Mini App button. If the project already establishes it, do not ask the user again.

Current Bot API `KeyboardButton` and `InlineKeyboardButton` document a `style` field with `danger` (red), `success` (green), and `primary` (blue). A red inline callback button can be represented as:

```json
{"text":"Отмена","style":"danger","callback_data":"cancel"}
```

This object belongs inside the existing inline keyboard structure. Preserve its required action: URL, callback, Mini App launch or other supported type. Do not add a second mutually exclusive action field.

If the installed SDK rejects `style`, inspect its version and serialization behavior. An outdated constructor is a library compatibility problem. Choose a supported library upgrade or documented raw request path, and verify that `style` reaches Telegram. Do not silently omit the requested color, replace it with a red-circle emoji, or build a Mini App solely to work around an assumed restriction.

The documented style is not a promise of identical pixels in every client/theme, nor arbitrary RGB support for bot keyboards. Mini App HTML/CSS and its native bridge buttons have their own APIs.

Sources:
- https://core.telegram.org/bots/api#keyboardbutton
- https://core.telegram.org/bots/api#inlinekeyboardbutton
- https://core.telegram.org/bots/webapps
- https://core.telegram.org/bots/api-changelog

## “Добавь premium emoji”

Resolve where the custom emoji should appear. Text, button icon, reaction, status and sticker are different representations.

- Message text: inspect `MessageEntity` with type `custom_emoji`, or the documented HTML `tg-emoji` markup. Use a real custom emoji identifier and a valid fallback emoji. With explicit entities, verify UTF-16 span offsets.
- Keyboard icon: inspect `icon_custom_emoji_id` on the specific button type. Do not put HTML into a plain button label and expect it to render as an emoji entity.
- Rich-message button: inspect `RichMessageButton` and its supported `RichText` representation separately; regular keyboard-label rules do not define rich-message markup.
- Reaction, profile status or other use: inspect that surface's dedicated methods and eligibility rules; do not transfer text-message permissions automatically.

At the verification date, Bot API documents custom emoji eligibility for bots that purchased additional usernames on Fragment, or for messages directly sent to private/group/supergroup chats when the bot owner has Telegram Premium. Read the current exact conditions for the actual field and destination. Do not reduce this to “bots cannot use Premium emoji”, “Premium always suffices”, or a guessed purchase requirement. Channels, inline results and other contexts must be checked separately.

Do not invent identifiers or substitute a Unicode emoji/sticker without explaining that it changes the requested outcome. Obtain the identifier from authorized existing data or the relevant documented API. A numeric-looking value is not proof that it identifies a usable custom emoji.

Sources:
- https://core.telegram.org/bots/api#formatting-options
- https://core.telegram.org/bots/api#messageentity
- https://core.telegram.org/bots/api#inlinekeyboardbutton
- https://core.telegram.org/bots/api#getcustomemojistickers
- https://core.telegram.org/api/custom-emoji

## Acceptance checks

For the colored-button case: payload contains the correct style and action, the library preserves it, Telegram accepts it, and the target client shows the intended style when live verification is available.

For emoji: correct surface/identifier, documented actor and destination eligibility, correct entities or icon field, and the requested result rather than a fallback substitution. Report offline-only verification as such.
