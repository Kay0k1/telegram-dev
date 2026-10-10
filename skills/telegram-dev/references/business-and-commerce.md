# Business, commerce, gifts and stories

Read the relevant section only. Identify the acting bot/user/business account, destination, payer/recipient and requested monetary or visibility outcome. Verify current numeric limits, rights and eligibility immediately before implementation.

## Business connections

Resolve the active connection and its granted rights. Separate the connection identifier, business owner and managed conversation; do not use the owner's private chat as a substitute destination. Thread the required business context through supported method calls and incoming message/edit/deletion handlers. Handle disablement and changed rights without silently reverting to ordinary bot messages.

Check each requested action independently: messaging/read/delete, profile edits, gift/Stars access and stories use distinct permissions. A connected bot is not an unrestricted user-account session; a business account feature described in raw MTProto may not be exposed by the same Bot API method. For auto replies, inspect documented eligibility windows and managed recipients instead of hardcoding a remembered rule.

Sources: [business account features](https://core.telegram.org/api/business), [connected business bots](https://core.telegram.org/api/bots/connected-business-bots), [connection object](https://core.telegram.org/bots/api#businessconnection), [rights object](https://core.telegram.org/bots/api#businessbotrights).

## Payments for goods and services

Classify digital versus physical goods/services before choosing a payment mechanism. The current digital-goods flow inside Telegram uses Stars (`XTR`); physical goods/services have a separate provider flow. Verify the current requirements for the actual product and delivery surface instead of copying invoice parameters between them.

Model invoice creation, checkout validation and payment completion as distinct states. A pre-checkout approval or client popup result does not establish a completed paid order. Deliver from the authoritative successful-payment event, validate order/amount/currency/payer against server-side state, and deduplicate fulfillment. Retain the Telegram charge identity needed for reconciliation/refunds, separate from a provider's identifier. Handle a delayed or repeated event and avoid accepting another payment for a single-use order unless the product permits it. Use the documented checkout deadline, test environment and current customer-support/refund requirements.

Sources: [digital goods](https://core.telegram.org/bots/payments-stars), [physical goods](https://core.telegram.org/bots/payments), [payment types and methods](https://core.telegram.org/bots/api#payments).

## Other Stars and monetization flows

An invoice payment, subscription, paid-media unlock, paid message, suggested-post settlement and business-to-bot transfer are different transactions. Select the matching flow; do not implement all as `sendInvoice`. For subscriptions, distinguish recurring bot services from channel membership and model expiry, cancellation and renewal. For paid media, verify allowed content and recipient/creator support. For suggested posts, inspect proposal, acceptance, publication and settlement/refund lifecycle. Represent amounts using the precision specified by each API, including fractional units where exposed; display balances and transaction direction correctly.

Sources: [Stars](https://core.telegram.org/api/stars), [subscriptions](https://core.telegram.org/api/subscriptions), [paid media](https://core.telegram.org/api/paid-media), [suggested posts](https://core.telegram.org/api/suggested-posts). Discover paid messages, revenue, affiliate programs and giveaways from [the live index](https://core.telegram.org/api).

## Gifts and collectibles

Resolve whether the user wants to purchase/send a catalog gift, manage an already-owned gift, convert it, upgrade it into a collectible, transfer it, display it, resell it or participate in an auction. These require different identifiers and entitlement/balance checks. Read the exact object and operation; a catalog `gift_id` is not interchangeable with an owned/unique gift identifier. Separate regular gifts, collectible gifts, Premium gifts and giveaway prizes. Confirm the authorized account and recipient before irreversible spending or ownership changes. After an ambiguous timeout, reconcile ownership or transaction history before retrying.

Sources: [gifts and their lifecycle](https://core.telegram.org/api/gifts), [Bot API gift/business methods](https://core.telegram.org/bots/api), current gift-auction article linked by [the API index](https://core.telegram.org/api).

## Stories

Determine whether a user, channel or managed business account publishes the story, and select the matching API. The Bot API has business-story operations; do not claim stories always require a user session. Check current rights, eligibility, media type, active period, archive/profile behavior, caption entities, areas and privacy. A normal chat video upload does not create a story. Editing/reposting/deleting may have narrower ownership rules than viewing or posting.

Sources: [Telegram stories](https://core.telegram.org/api/stories), [Bot API postStory](https://core.telegram.org/bots/api#poststory), [business rights](https://core.telegram.org/bots/api#businessbotrights).

Useful acceptance checks include duplicate-payment fulfillment, revoked business rights, correct owned-gift identity, actual story response and expected privacy/destination. Mocked calls establish request construction only; state when no live acceptance or settlement was verified.
