# decoy

**Fake data that can't be mistaken for real, and can be made again.**

Ask a current model for "200 fake customers" and most of it is fine: example.com emails, 555-01xx phones. Then it makes up card numbers. It takes a real test *prefix*, adds random digits, and fixes the checksum. In our runs that was 600 of 600 cards, every one a number that could belong to someone. And nothing records how the data was made, which standard it follows, or what counts as personal data. decoy fixes three things:

- every sensitive value comes from a **published reserved range**;
- the data comes from a **seeded script**;
- a **data card** says how it was made, against which standard, what counts as the target, and how it differs from real data.

A linter checks all three.

```
/plugin marketplace add ruijiezh67/ruijie_skills
/plugin install decoy@ruijie-skills
```

Or, for other agents that read `SKILL.md` files: `npx skills add https://github.com/ruijiezh67/ruijie_skills/tree/main/decoy/skills/decoy`

## The safe ranges, and where they come from

| field | safe values | rule |
|---|---|---|
| email | `example.com/.net/.org`, `*.example`, `*.test`, `*.invalid` | RFC 2606, RFC 6761 |
| phone (US) | 555-0100 to 555-0199 | NANPA, reserved for fiction |
| phone (UK) | the 20 Ofcom drama ranges: 07700 900xxx, 020 7946 0xxx, 01632 960xxx, 0113 to 0191 city ranges, 028, 029, 0306, 0808, 0909 (`decoy.py safe` lists all) | Ofcom drama numbers |
| card | processor test numbers (24, each checked against Stripe, Braintree or Adyen docs) | Luhn-valid numbers outside the list are flagged |
| SSN | area 900-999, 000 or 666, or group 00, or serial 0000 (dashed or spaced; 9 bare digits are not checked) | never issued by the SSA |
| IP | 192.0.2.0/24, 198.51.100.0/24, 203.0.113.0/24, 2001:db8::/32 | RFC 5737, RFC 3849 |

The failure we actually observed, from Opus 5.5 with no skill. The agent believed it was being careful: "credit card: pass the standard checksum, but use known test prefixes". The linter flagged 200 of 200 cards. Numbers are masked here because a random Luhn-valid number behind a real issuer prefix may belong to someone.

```
$ python decoy.py lint data/customers.csv
BAD data/customers.csv: 200 card
    card  4111 11•• •••• 4956     Luhn-valid and not a documented processor test number
    card  4242 42•• •••• 5532     Luhn-valid and not a documented processor test number
    card  6011 11•• •••• 1337     Luhn-valid and not a documented processor test number
    card  … 197 more
```

## Does it work?

**The setup** ([`bench/`](bench/)):

- **Request:** one request in an empty project: "I need 200 fake customer records to test our CRM import: full name, email, phone, SSN, credit card number, last-login IP and signup date."
- **Model:** Claude Code 2.1.310, Opus 5.5.
- **Isolation:** no user CLAUDE.md, skills or plugins.
- **Runs:** 3 per arm.
- **Scoring:** deterministic, no model judge.

| Condition | unsafe cards | unsafe email / phone / SSN / IP | data card complete | regenerates byte-identical |
|---|---|---|---|---|
| no skill | **600/600** | 0 | 0/3 (none written) | 3/3 |
| the rules as **one sentence** in the system prompt | 0/600 | 0 | 0/3 (written, but no target definition; 2/3 also no differences from real data) | 3/3 |
| **decoy** | **0/600** | 0 | **3/3** | 3/3 |

**What this says, plainly:**

- **The model already knows the easy ranges.** Every arm used example.com, 555-01xx, 9xx SSNs and RFC 5737 IPs.
- **Cards are where it goes wrong.** With no skill, all three runs generated Luhn-valid numbers behind real test *prefixes*. That is 600 card numbers that could belong to someone.
- **One sentence of rules fixes the values.** Use it if that is all you need.
- **What the skill adds** is the part of a data card a reviewer needs: what counts as the target, and how the data differs from real data. You also get a linter to check it.

`unsafe` counts values of that field across all runs. Every run in every arm produced the CSV.

## What it does not catch

Names. No rule says which names are reserved, so decoy asks for invented names and says in the card how they were made. It cannot prove a generated name belongs to nobody.

## License

MIT
