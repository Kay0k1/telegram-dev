# Bot operations and evolving bot capabilities

Read this for setup, event delivery, callbacks, inline results, bot modes and reliable operations. Source links are entrypoints; read current method sections for exact parameters and limits.

## Diagnose the existing integration

Inspect the installed SDK, configuration, update routing and deployment before changing the stack. For missed events, distinguish delivery failure, subscription filtering, privacy mode, missing rights, wrong bot identity and an exception inside the handler. Use authorized diagnostic state and sanitized logs. A successful `getMe` identifies the bot; it does not prove its webhook or chat permissions work.

Choose webhook or long polling according to the deployment. They cannot receive updates simultaneously for the same bot. Inspect existing webhook state before changing it. Preserve queued updates during routine recovery unless discarding them is part of the requested operation. Durable handling should avoid acknowledging an event that would be lost if the process crashes. Exercise duplicate and out-of-order delivery against business state; decide ordering at the conversation/operation level, not by blocking every chat globally.

Check `allowed_updates` against the actual event type. Default subscriptions do not include every event. Privacy mode and membership affect which messages reach the bot; a permission granted in a UI does not guarantee delivery of a subscribed update.

Sources: [update delivery](https://core.telegram.org/bots/api#getting-updates), [webhooks](https://core.telegram.org/bots/webhooks), [bot FAQ](https://core.telegram.org/bots/faq), [privacy mode](https://core.telegram.org/bots/features#privacy-mode).

## Interaction state and identifiers

- A reply keyboard sends a message or invokes its documented request action. An inline callback creates a callback query. A URL button opens a link. Preserve the user's desired action when adding styling or an icon.
- Acknowledge callbacks using the documented method; business processing and UI acknowledgement are different concerns. Resolve ordinary chat/message identifiers versus `inline_message_id` from the received object before editing.
- Treat callback payloads and deep-link parameters as input. Bind state-changing actions to the authenticated actor and current server-side state; a visible command scope or hidden button is not an access-control check.
- For inline results, verify result type, pagination and caching behavior. User-specific data must not be reused as a shared cached result. Receiving a selected result or obtaining an identifier does not establish access to its destination chat.
- Preserve identifier precision in storage and JSON boundaries. Keep a bot/chat/message tuple where identity is scoped that way; avoid globally keying state solely by `message_id`.

Sources: [keyboards and scopes](https://core.telegram.org/bots/features), [callback query](https://core.telegram.org/bots/api#callbackquery), [inline mode](https://core.telegram.org/bots/inline).

## New modes and rich bot experiences

For managed bots, guest bots, bot-to-bot communication, streaming drafts, stop-generation events, ephemeral replies, rich messages or private chat topics, read the live feature guide and corresponding methods/types. Check required BotFather mode, actor, destination, capability flags and deployed SDK serialization. Do not repeat historical claims such as “bots can never see other bots” without checking the current enabled mode.

A streaming draft is a transient preview; verify how the final result becomes a persistent message. Propagate a user cancellation to the actual background work. For a personalized group response, preserve its documented recipient visibility instead of posting private data as an ordinary group message. Rich message structures and their allowed markup are distinct from regular text/entities and a Mini App web page.

Sources: [current bot features](https://core.telegram.org/bots/features), [current Bot API types and methods](https://core.telegram.org/bots/api), [changes](https://core.telegram.org/bots/api-changelog).

## Failure handling and verification

Use response errors and documented retry information to classify throttling, revoked access, invalid payloads and transient transport failures. Honor the appropriate wait with bounded retries. A timeout after a send is ambiguous: do not duplicate a payment, gift or other costly action by retrying without reconciliation. Handle migration to a new chat identifier when applicable.

For a production incident, reproduce the concrete trigger and fix the existing path. Relevant checks include duplicate delivery, handler restart, callback from an expired UI, SDK preservation of a new field, and a target bot receiving the intended event. Request-construction tests do not prove Telegram delivery.

Sources: [Bot API response parameters](https://core.telegram.org/bots/api#responseparameters), [FAQ rate limits](https://core.telegram.org/bots/faq#my-bot-is-hitting-limits-how-do-i-avoid-this), [test environment](https://core.telegram.org/bots/features#testing-your-bot).
