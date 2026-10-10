# Telegram client and protocol development

Read this for account sessions, TDLib/MTProto, client-side state, calls, secret chats and export. A Telegram API account client, an MTProto-authorized bot and a Bot API service have different capabilities even when a library supports all three.

## Choose the integration level

Use the existing suitable library. TDLib manages networking, encryption and local state through its own API; inspect the installed build's generated schema and documentation rather than translating Bot API method names literally. Raw Telegram API clients use the application's credentials, authorization state and supported TL layer. MTProto is the protocol below that application API. Protocol implementation is appropriate only when the request actually requires it.

Pin source/build revisions when investigating a client discrepancy. A method existing in the latest schema does not prove the project's TDLib build or target client supports it. For distribution of a third-party client, read the applicable [API terms](https://core.telegram.org/api/terms) and [client documentation](https://core.telegram.org/api), including required behavior relevant to that client.

Sources: [TDLib](https://core.telegram.org/tdlib), [getting started](https://core.telegram.org/tdlib/getting-started), [TL schema](https://core.telegram.org/schema), [MTProto](https://core.telegram.org/mtproto), [official clients](https://telegram.org/apps).

## Authorization and account state

Follow the actual library's authorization state machine and current [user-authentication flow](https://core.telegram.org/api/auth). Codes, 2FA, QR login and [passkeys](https://core.telegram.org/api/passkeys) have different states and expiry semantics. Website OIDC/Mini App data does not authorize an MTProto account session. Do not expose credentials or session storage in generated logs; request account access only for the live account work actually authorized.

Handle expiry, revocation, sign-out and account mismatch explicitly. Preserve the distinction between authenticating a user, registering an application and granting a bot a business connection. Use the dedicated [2FA](https://core.telegram.org/api/srp) or [QR-login](https://core.telegram.org/api/qr-login) source when that mode applies.

## Peers, updates and synchronization

Resolve the input peer using the chosen client's peer database and documented identifier/access-hash rules. A Bot API chat ID alone is not a complete raw `InputPeer`. Partial/min constructors may require contextual resolution; do not treat missing fields as a complete replacement for cached state.

For a raw client, follow sequence-state, gap and difference rules for the relevant update stream. For TDLib, consume its update objects and persistence behavior instead of maintaining a second incompatible MTProto state machine. Check pagination semantics for each collection rather than assuming a common offset. On errors, handle DC migrations, revoked authentication, flood waits and expired file references using the documented recovery path; do not spin retries or duplicate non-idempotent actions.

Sources: [updates](https://core.telegram.org/api/updates), [peer database](https://core.telegram.org/api/peers), [min constructors](https://core.telegram.org/api/min), [pagination](https://core.telegram.org/api/offsets), [errors](https://core.telegram.org/api/errors), [file references](https://core.telegram.org/api/file_reference).

## Calls and secret chats

Separate voice/video messages, one-to-one calls, group calls, live streaming and secret-chat messaging. Sending audio or joining a chat does not establish a media call. Read the current [call](https://core.telegram.org/api/calls) or [group-call](https://core.telegram.org/api/group-calls) flow, the chosen library's actual support, signaling, media transport/engine and permission/lifecycle requirements. Test with the intended participants and client platforms when authorized; a successful signaling call alone does not prove bidirectional audio/video.

For [secret chats](https://core.telegram.org/api/end-to-end), use the documented E2E state/layer/sequence/rekey lifecycle and a suitable existing implementation. Do not call ordinary cloud-chat encryption “end to end”. Custom cryptographic work must follow [security guidelines](https://core.telegram.org/mtproto/security_guidelines) and the relevant linked protocol specifications, not invented schemes. State the client's actual secret-chat/call limitations rather than assuming a transport library implements them.

## Other client features and export

Account privacy, contacts/blocklist, folders/drafts, Saved Messages, scheduled messages, search, read state, reactions, themes, translation, transcription and notifications use distinct API families. Discover their current source from [the API index](https://core.telegram.org/api); inspect permissions and client configuration rather than hardcoding undocumented limits. For export, distinguish ordinary paginated history retrieval from [takeout](https://core.telegram.org/api/takeout), its lifecycle and data access. Preserve the requested account/scope and applicable content restrictions.

Useful verification includes restart/update-gap recovery, partial peer objects, migrated chats, pagination without skips, actual auth-state transitions and the requested client-visible feature. Mocks and one library method returning successfully cannot establish full client interoperability.
