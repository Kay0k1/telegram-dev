# TON and blockchain in Telegram

Use for wallets, payments in crypto, tokens (jettons), NFTs, smart contracts, TON Connect in Mini Apps, on-chain gifts and usernames, and any "blockchain in Telegram" request.

## Decide what the user actually needs

| Request | Usually means | Start here |
|---|---|---|
| Sell digital goods or services inside a bot or Mini App | Telegram Stars, not crypto | https://core.telegram.org/bots/payments-stars |
| Let a Mini App user connect a wallet, pay, sign | TON Connect in the Mini App frontend | https://docs.ton.org/applications/ton-connect/overview |
| Accept crypto payments and credit orders on a backend | Payment processing: watch transactions, match by comment or address, wait for finality | https://docs.ton.org/applications/payments/overview |
| Issue a token or an NFT collection | Jetton / NFT standards (TEPs) and their reference contracts | https://docs.ton.org/llms.txt → Smart contracts; https://github.com/ton-blockchain/TEPs |
| Write or audit a smart contract | Tolk (current official language); FunC/Fift are legacy | https://docs.ton.org/tolk/overview |
| Read balances, transactions, contract state from a server | Public API providers and SDKs | https://docs.ton.org/api/overview ; https://docs.ton.org/applications/sdks |
| Send coins to a Telegram user or integrate the wallet built into Telegram | Telegram's own wallet and its contract | https://docs.ton.org/llms.txt → Onboarding → Wallet apps; Smart contracts → wallets |
| AI agent that holds funds or signs transactions | Agentic wallets / AgentKit, a separate product with key custody | https://docs.ton.org/llms.txt → Onboarding → AI in TON |

The `ton` search area covers docs.ton.org, TEPs and Telegram's blockchain guidelines; `ton-releases` covers the TON node and Tolk changelogs. Fetch `https://docs.ton.org/llms.txt` first when the cache is empty: it lists every current TON page.

## Telegram rules come first

Read https://core.telegram.org/bots/blockchain-guidelines and section 7 of https://telegram.org/tos/bot-developers before designing a blockchain feature in a Mini App. Check the current text, but expect these constraints:

- Mini Apps may issue and distribute blockchain assets only on TON and may interact with wallets only through TON Connect (other protocols only for bridging into TON). Do not fork or restrict the TON Connect SDK beyond feature-based filtering.
- Digital goods and services sold inside Telegram are paid with Stars. Do not replace a Stars flow with a crypto payment because the user said "payment".
- Bots without a Mini App are outside these Mini App rules, but the rest of the Terms still apply.

Name the rule and link it when it changes the design.

## Do not trust remembered TON facts

TON product names, wallets and tooling changed recently and will change again. Read the current page before writing names, amounts or commands into code or UI text: the coin's current name and ticker, which wallet ships inside Telegram and which contract it uses, which smart-contract language and toolchain are current, address formats, and fee rules. If the docs use a name that differs from what you remember, follow the docs and tell the user.

## Implementation checks

- **Network.** Develop on testnet first; make mainnet/testnet an explicit setting. Addresses and API endpoints differ per network.
- **Amounts.** Use integer base units and the documented decimals; never floats. Jettons have their own decimals in metadata.
- **Keys.** Never ask for, log, or store a user's mnemonic or private key. Users sign in their wallet through TON Connect. Server-side wallets need explicit key management agreed with the user.
- **TON Connect.** Host a valid manifest at a public URL, handle connection restore and disconnect, and treat the returned address as unverified until the backend checks a `ton_proof` signature when it matters (login, ownership). Read the current SDK for the frontend in use (`@tonconnect/ui-react`, `@tonconnect/ui`, `@tonconnect/sdk`).
- **Payments.** A sent message is not a successful payment. Confirm the transaction on-chain, check the destination, amount and comment/payload, handle bounces and duplicates idempotently, and wait for the documented finality before crediting.
- **Contracts.** Follow the TEP for standard tokens and NFTs instead of inventing message formats; check opcodes, bounce handling and gas against the current docs and tests. Use the official toolchain for compiling and testing; do not deploy to mainnet from an agent without the user's explicit go-ahead.
- **Gifts, usernames, numbers.** Telegram collectibles that move on-chain involve both Telegram docs (Bot API / Telegram API gifts) and TON NFT standards. Check both sides.

## Report

State which network, standard and SDK version the code targets, which steps were tested offline (message building, address parsing, unit tests against an emulator) and which need a real wallet or transaction.
