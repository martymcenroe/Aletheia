# Implementation Report — Issue #628

**Title:** chore: replace Discworld asides with mainstream literary references
**Date:** 2026-05-23
**Status:** Complete (pending review + merge)
**Branch:** `628-mainstream-literary-asides`

## Summary

Replaced **all five** Discworld asides on the site with mainstream-recognizable literary references per user feedback during #625 review. Original issue scope was two (`demos.html`, `safety.html`); grep found three additional pre-existing references (`architecture.html`, `observability.html`, `operations.html`). All five preserve the epigrammatic-aside form factor while broadening accessibility.

Selection criteria: each replacement maps directly to the page's thesis, and the literary tradition is in current mainstream cultural circulation (recent films, TV adaptations, or classical-education staples). Trickster gods favored per user style guidance (Ulysses, Hermes, Odin all qualify).

## Files Modified

| File | Page Thesis | Original (Discworld) | Replacement |
|------|-------------|----------------------|-------------|
| `docs/demos.html` | Attacks hidden in legitimate content | Lancre witch quote | Ulysses / Trojan Horse |
| `docs/safety.html` | LLM classifies, code enforces | Librarian of UU zero-tolerance | Dune Butlerian Jihad |
| `docs/architecture.html` | Naked Python orchestrator, file-before-act | UU Library cataloguing + "Ook" | Foundation's Encyclopedia Galactica |
| `docs/observability.html` | Trace metadata without reading content | Clacks towers / GNU Terry Pratchett | Hermes carrying messages between gods |
| `docs/operations.html` | Light-touch governance / minimal intervention | Lord Vetinari / Ankh-Morpork | Odin from Hlidskjalf / Nine Worlds |

## Replacements

### `docs/demos.html`

**Before:**
> A man walking through a market in long-ago Lancre asked how to recognize a witch. "Don't worry," said the answer, "she'll be the one selling you something.

**After:**
> When Ulysses gave Troy a horse, the Trojans wheeled it inside the walls because the horse was a gift, and gifts get wheeled inside walls. The lesson is not "beware of Greeks bearing gifts." The lesson is that an attack can arrive in the shape of whichever object you have stopped paying attention to.

Why this works for the page: the demos page is about prompt-injection attacks embedded in legitimate-looking content (news article, technical spec, academic paper, social post, encyclopedia entry). The Trojan Horse is exactly that — an attack hidden inside a benign-looking object. Trickster-god framing per user style preference (Ulysses / Odysseus).

### `docs/safety.html`

**Before:**
> The Librarian of Unseen University has a simple policy regarding the mistreatment of books: zero tolerance, applied instantly, with no appeals process. The books don't decide their own protection — the Librarian does. Our guardrails follow the same philosophy.

**After:**
> The Butlerian Jihad ended ten thousand years before House Atreides reached Arrakis, and it ended with a single commandment: thou shalt not make a machine in the likeness of a human mind. The machines did not propose this rule. It was made by humans, applied to machines, and enforced by humans. Aletheia's guardrails follow the same shape.

Why this works: the page's core principle is "The LLM classifies; code enforces. Policy decisions are never delegated to the model." The Butlerian Jihad is exactly that — humans deciding the rules that govern machines, then enforcing them. Dune is mainstream via the Villeneuve films.

### `docs/architecture.html`

**Before:**
> Much like the Unseen University Library, where every book must pass through several layers of cataloguing before reaching the shelves — and the Librarian knows exactly where each one belongs — every request is filed, classified, and stored with precision. Ook.

**After:**
> The Encyclopedia Galactica was Hari Seldon's first move: catalogue everything, then watch what falls out of the patterns. The Plan needed the encyclopedia to be filed correctly more than it needed any particular entry to be read. Every request Aletheia handles is filed before it is acted on.

Why this works: the page is about Aletheia's request-classification pipeline. Foundation's Encyclopedia Galactica is the archetypal cataloguing-as-strategy artifact in science fiction. Mainstream via the Apple TV+ adaptation.

### `docs/observability.html`

**Before:**
> Like the Clacks towers of the Grand Trunk, every message carries overhead bytes recording its journey — how long each tower held it, which ones dropped it, the cost of the semaphore time — but the message itself is never read by the operators. GNU Terry Pratchett.

**After:**
> Hermes carried messages between the gods and the dead. His winged sandals were not the load-bearing element of his work. The load-bearing element was that he always remembered who sent each message, to whom, and at what hour. Tracing is older than computers; it used to wear winged sandals.

Why this works: the page's principle is "log metadata about every request, never log the content." Hermes is the messenger god who carries content but is remembered for who-when-from-to provenance. Greek myth is classical-education mainstream and Hermes is a recognized trickster figure.

### `docs/operations.html`

**Before:**
> Lord Vetinari governs Ankh-Morpork not through force but through careful observation and the occasional, precise intervention. The city runs itself; he merely ensures nothing runs away with it. The same principle applies here.

**After:**
> Odin governed the Nine Worlds not by ruling them but by watching from Hlidskjalf, the high seat from which he could see everything that happened. He sent ravens to ask questions. He sent Valkyries to settle wars. He intervened only when a thread was about to unravel. The same principle applies here.

Why this works: the page is about light-touch infrastructure operations — let the system run, observe carefully, intervene precisely. Odin's high-seat-and-ravens method is the same archetype. Norse mythology is broadly recognized via the MCU's Thor films and Neil Gaiman's work; Odin is explicitly on the user's "welcome trickster gods" list.

## Files Intentionally NOT Changed

- `.discworld-aside` CSS class name kept as-is. The class continues to provide the styling (italic, indented, smaller font). Renaming would require updating the styles.css selector and any other references, which is out of scope for a content-only fix. Can be addressed in a future cleanup if it becomes a maintenance issue.

## Verification

- Grep confirms no other Discworld references on the site (`grep -i "discworld\|lancre\|ankh\|unseen university\|librarian of\|pratchett"` returns only these two paragraphs).
- Both pages render with the new asides in the `.discworld-aside` styling block.

## Related

- #625 — original demo content (Lancre quote was introduced there)
- safety.html Librarian quote was pre-existing; modified here per the same user feedback
