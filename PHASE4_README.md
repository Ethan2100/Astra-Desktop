# ASTRA Phase 4 — First Tools

Phase 4 begins with real, bounded tools rather than model-generated claims.

## Included in this increment
- Live DuckDuckGo HTML search through Python's standard library (no API key).
- Search results include the actual destination URLs returned by the search provider.
- Direct launch of a small allowlist of Windows applications.
- Opening explicitly supplied HTTP(S) URLs in the default browser.
- Recognized commands are routed to tools before Ollama, so a small local model does not need to invent tool calls.

## Commands
- `search the web for Re:Zero season 5 official announcement`
- `google latest Python release`
- `look up online Crunchyroll Kenya Re:Zero`
- `open Notepad`
- `open Calculator`
- `open File Explorer`
- `open https://example.com`

## Important limitations
- Search results are leads, not verified facts. Open the source pages and compare publication dates before drawing conclusions.
- This increment does not yet give the model unrestricted shell, file deletion, mouse or keyboard access.
- The next increment adds screen inspection and carefully scoped desktop interaction, with confirmations for consequential actions.
- Search depends on DuckDuckGo's public HTML endpoint and may fail if the provider blocks automated requests or changes its page markup.

## Privacy
No search API key is stored. Search queries are sent to DuckDuckGo. Ollama chat remains local unless a later feature explicitly uses an online service.
