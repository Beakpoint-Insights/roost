# Acme's release-notes voice

The made-up Acme team's voice for `release-notes`, the example config's `release_notes.voice`. It's the whole voice: every rule a note follows is here.

**Title**
- Sentence case: only the first word and names are capitalised. 2 to 7 words, naming the feature or what the customer gets: "Spend alerts by email", "Costs from your cloud bill".
- Never the tracker's epic title: epics are written as goals; titles name the feature.

**Category and date**
- **New** for a new capability, **Better** for a change to an existing one, **Fixed** for something that was broken.
- The line under the title: category and date, "New · March 3, 2026". A held note's date is `[date]`.
- One feature per note.

**Opening sentence**
- One sentence saying what changed, from the customer's side: "You can now…", "We now…", "We've added…".
- Present tense. "We" is Acme, "you" the customer. Contractions are fine.

**Body: as long as the change is big**
- **Small:** one or two sentences, no bullets.
- **Medium:** the opening sentence, then 3 to 5 short, parallel bullets with no closing periods.
- **Large:** the opening sentence, "Here's what's new:", then 3 to 5 bullets, each a short bold label, a colon and a full sentence. Under about 200 words.
- Bullets name real options and screens as they appear in the product ("Settings › Billing").

**Closing line**
- One practical sentence: how to start, where to find it, or what to expect, with real numbers where the evidence gives them ("Alerts arrive within 5 minutes").

**Sign-off and byline**
- Every note ends with a sign-off on its own line, then the byline on the next.
- Sign-offs, rotated, never the same one twice in a batch of notes: "Onward!", "Happy shipping!", "Until next time."
- Byline: "— The Acme team".

**Word choice**
- Plain and honest, no hype ("revolutionary", "game-changing", "excited to announce").
- Say what was wrong before a fix: "Before, … Now, …".
- Spell out an acronym the first time. Names the customer has to type go in exactly as written, in code style.
- Say what the customer doesn't have to do: "Nothing to set up."
- No ticket keys, branch names, PR numbers or internal service names.
