# Zoho sender authentication check

This file exists because the project brief links a header analysis here. The analysis was done during Exercise 06 and is recorded in [ex06.md](ex06.md) section 2, so this page does not repeat it with different wording.

Summary of that evidence (from the raw header of `Test 02: new outbound`, as received by an outside Gmail mailbox, 2026-10-20):

| Check | Result | What it means |
| --- | --- | --- |
| SPF | `pass` for `sharavjiwrajka.me`, sending IP in Zoho's range | The sending server is allowed by my SPF TXT record |
| DKIM | `pass`, `header.s=zmail`, `header.i=@sharavjiwrajka.me` | The message carries a signature that verifies against the DKIM TXT record at `zmail._domainkey` |
| DMARC | `pass`, policy `p=NONE` | The passing domain matches the From domain. `p=none` only reports, it does not reject |

DNS records involved (confirmed again in Cloudflare on 2026-10-26): three Zoho MX records (10, 20, 50), SPF TXT `v=spf1 include:zohomail.com ~all`, DKIM TXT at `zmail._domainkey`, DMARC TXT at `_dmarc`, and the Zoho ownership TXT.

Not covered here: the message sent **before** the MX records existed. See ex06.md for whether that check was recorded.
