# Groups, channels, moderation and conversation routing

Read this for administrative actions, membership, forums, comments and channel direct messages. First resolve the actual chat type and acting identity from project state. A basic group, supergroup, broadcast channel, forum and channel direct-message conversation do not share every operation or event model.

## Permissions and moderation

Map the requested action to its exact required right, the bot/user's effective rights, the target member's role and the method's chat-type restrictions. An administrator label alone is insufficient. Restricting permissions, banning, unbanning, removing a member, deleting a message and preventing future joins have different outcomes; preserve the requested one. Evaluate defaults versus per-member overrides and expiry semantics using the selected API.

For automatic moderation, use the event's actor fields rather than assuming `from` always identifies an ordinary user: channel posts, anonymous administrators and messages sent on behalf of chats need different handling. Build a targeted check from the user's actual moderation rule; do not infer authorization from a command appearing in a menu. Report missing rights before retrying. Destructive bulk changes should preserve the authorized selection and stopping condition.

Sources: [chat types](https://core.telegram.org/api/channel), [rights](https://core.telegram.org/api/rights), [Bot API administrative methods](https://core.telegram.org/bots/api), [bot visibility](https://core.telegram.org/bots/faq#what-messages-will-my-bot-get).

## Invites, joins and membership

Distinguish a public username, invite link, join request and paid subscription invite. Verify who owns/manages the relevant link, approval rights, expiry, limits and update subscriptions. Revoking one link is not equivalent to disabling every route into a chat. Reconcile a membership change with live state when a delayed event would otherwise trigger an incorrect action.

Sources: [invite links and join requests](https://core.telegram.org/api/invites), [subscription flows](https://core.telegram.org/api/subscriptions), [Bot API join-request objects](https://core.telegram.org/bots/api#chatjoinrequest).

## Topics, comments and direct messages

Forum topics can belong to a group or to a bot's enabled private-chat topic mode. Check the current mode and capabilities rather than assuming topics require a supergroup. Preserve the topic identity in sends and replies; choosing only the outer chat can send the answer into the wrong conversation. Topic create/edit/close/reopen/hide/delete operations have separate permission and lifecycle rules, including special handling for the General topic.

Before enabling private bot topics, check the current [Bot Developer Terms](https://telegram.org/tos/bot-developers#6-2-6-enabling-topics-in-private-chats) for activation conditions and any effect on Stars purchases. Surface an actual documented cost when it changes the user's decision. Check each method's private-chat support independently rather than extending a supergroup-only operation to the new mode.

A channel post, its discussion-group comment thread and a channel direct-message topic are separate destinations. Resolve the appropriate outer peer, root/thread/topic and reply target. Channel direct messages are not ordinary forum topics just because both expose a topic-like identifier. Test a reply when the original replied-to message is absent/deleted if routing fallback matters to the task.

Sources: [forum and bot topics](https://core.telegram.org/api/forum), [discussion groups](https://core.telegram.org/api/discussion), [message threads](https://core.telegram.org/api/threads), [channel direct messages](https://core.telegram.org/api/monoforum).

## Other community features

For polls/quizzes, reactions, pins, checklists, scheduled posts, statistics, boosts, giveaways, antispam, protected content or channel monetization, follow the matching current API-index article and exact actor-specific method. Keep anonymous vote totals separate from identifiable votes; check which poll/reaction events the bot is entitled and subscribed to receive. A public post being readable does not imply every statistic or member is accessible. Protected media/content restrictions still apply to export or repost requests.

Source: [feature-family index](https://core.telegram.org/api). Payment and suggested-post flows also use [business and commerce](business-and-commerce.md).

Acceptance evidence should cover the intended destination and effective permission state: success in the requested topic, the target restriction/deletion result, or the relevant subscribed event. Avoid interpreting a successful API request as proof of every member's client view.
