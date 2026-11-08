# Changelog

Every rule traces to a real failure. Record the failure next to the fix.

## 0.2.1 (2026-11-08): second review of awesome-llm-apps PR #1271
- **Northern Ireland range corrected.** It is 028 9649 6000-6999. The 028 9018 0xxx block I had used is the pre-2019 range, now allocated for real use, so 0.2.0 marked real numbers as safe. The maintainer caught it.
- **Seven-digit numbers.** US numbers without an area code are read with a dash, dot or space. Seven bare digits are documented as not checked.
- **Limits documented:** two kinds of false positive, `ddd-dddd` tokens and 10 to 11 digit ids starting 0.

## 0.2.0 (2026-11-06): review of awesome-llm-apps PR #1271
Each item below is a lint gap the maintainer found.
- **The `# NON-RESERVED: <reason>` marker works.** Before, SKILL.md told the agent to mark exceptions, but lint still failed those lines. Values on a marked line are now listed for review and do not fail. A marker without a reason does not count.
- **UK phones checked against all 20 Ofcom drama ranges.** Before, only 4 were known and numbers outside the 07/020/0113/0161 prefixes were never flagged.
  - Source: Ofcom "Telephone numbers for use in TV and radio drama programmes". ofcom.org.uk blocks automated fetches, so the list was taken from its table as reproduced in Wikipedia's "Fictitious telephone number" article, which cites that page.
  - The Northern Ireland range (028 9018 0000-0999) should be confirmed against Ofcom directly.
- **New patterns.** Bare 7-digit `555-0200` and spaced SSNs (`123 45 6789`) are flagged. Bare 9-digit SSNs are documented as not checked.
- **SSN rule aligned.** README and SKILL.md now give the same rule: area 000, 666 or 9xx, or group 00, or serial 0000.
- **Luhn caveat documented.** Any Luhn-valid 13 to 19 digit id is reported as a card.
- **Tests:** 9 deterministic tests.
- **Description:** the Chinese trigger phrases were removed.

## 0.1.0 (unreleased, 2026-10-27)
- `decoy` skill: reserved values only, a seeded generator script, a data card (generator and seed, rules per field, standard, target, differences from real data), lint before handing over.
- `decoy.py`: `lint` checks emails, US/UK phones, Luhn-valid cards, SSNs and IPv4/IPv6 against published reserved ranges. `card` checks the data card. `safe` prints the ranges. Standard library only.
- Test card list: 25 numbers written from memory were each looked up in the Stripe, Braintree and Adyen docs on 2026-10-27. One (`4000000000000093`) was in none of them and was removed. 24 remain.
- `evals/test_decoy.py` (then `bench/test_decoy.py`): 6 deterministic tests.

### Findings from the first benchmark round (Opus 5.5, isolated host)
- **The model already knows most reserved ranges, but not the card rule.**
  - With no skill, every run used example.com, 555-01xx, 9xx/666 SSNs and RFC 5737 IPs.
  - One run generated 200 Luhn-valid card numbers that start with a test prefix and continue with random digits (`4111117816184956`, `4242421647525532`). Its reply called them "known test prefixes". A random number behind a real issuer prefix is a plausible real card. The skill now names this explicitly.
- **No condition without the skill wrote a data card** (0 of the runs that produced data). With the skill, all did.
- **The first regeneration check was wrong.** It re-ran the agent's scripts with no arguments, but the skill's own runs write to stdout (`python gen.py --seed N > data/customers.csv`). The check now runs the command documented in the card or the reply. Those runs had to be repeated because their work trees were already deleted.
- **Two runs produced no CSV because of the benchmark's tool allowlist, not the agent.** The agent asked for approval of a command (`cd data && python …`) that the allowlist did not cover. Such runs count as N/A, not as failures, and `cd` is now allowed.
