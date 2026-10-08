# How this site is secured

Site: https://sharavjiwrajka.me (also https://www.sharavjiwrajka.me)

## 1. The certificate

My site uses a free certificate from Let's Encrypt, requested with Certbot on the VM. The issuer shown on the certificate is Let's Encrypt, intermediate "YE2". One certificate covers both names:

- `sharavjiwrajka.me`
- `www.sharavjiwrajka.me`

It was issued on October 8, 2026 and expires on January 6, 2027, which is 90 days. A certificate is the site's proof of identity. It tells a browser that whoever answers at this name controls the domain, and it gives the browser the key it needs to encrypt the connection.

To get it, Let's Encrypt asked my server to serve a secret file at the domain over port 80. My server did, so Let's Encrypt knew I control the name. This only worked after I set both Cloudflare records to DNS only.

## 2. Renewal

Let's Encrypt certificates only last 90 days, so renewal has to be automatic. Certbot installed a systemd timer called `certbot.timer`. It runs twice a day and renews any certificate with 30 days or less left, so mine should renew around early December without me doing anything.

I tested it with `sudo certbot renew --dry-run`, and it ended with "all simulated renewals succeeded". I also checked the timer with `systemctl list-timers | grep certbot`:

```
Fri 2026-10-09 04:14:39 UTC       9h Thu 2026-10-08 12:55:24 UTC      6h ago certbot.timer                  certbot.service
```

It last ran 6 hours before I checked and is scheduled to run again at 04:14 UTC the next day.

## 3. Open ports and who can reach them

The Azure network security group (the firewall in front of the VM) has these inbound rules:

| Port | Who can reach it | Why it is open |
| --- | --- | --- |
| 22 (SSH) | Only my own computer's one public address, written as a /32 | So I can log in to manage the server |
| 80 (HTTP) | Anyone | Only to redirect visitors to HTTPS and to let Certbot prove I own the domain |
| 443 (HTTPS) | Anyone | The real website |

Everything else is closed, including port 8000 where the app listens. The app only listens on `127.0.0.1`, so even if someone opened 8000 in the firewall by mistake, the app would still refuse outside connections. That is the two locks idea: a firewall rule and the app's own bind address.

**Who can reach SSH:** only one computer, mine, and even then only with my private key. There is no password login. Anyone else's packets to port 22 are dropped by the firewall before they reach the server.

While setting up this exercise I found a real mistake in that rule. Its **source port** was set to `300` instead of `*`. A computer connecting by SSH picks a random source port, so the rule never matched and the firewall silently dropped even my own connection. It looked like my SSH command was hanging. I fixed it by changing the source port to `*` while keeping the source address locked to my single IP. The lesson is that restricting who can connect (the source address) is the security control. Restricting the source port does nothing useful, and a wrong value just locks you out.

## 4. Where encryption starts and ends

The connection is encrypted from the visitor's browser to Nginx on my VM. Nginx handles the HTTPS and holds the certificate.

From Nginx to my app, the traffic is plain HTTP on `127.0.0.1:8000`. That last hop is not encrypted. It stays inside the VM and never goes on a network, so nobody outside the machine can read it. Only someone already logged in to the VM could, and if they can do that, they could read the app's files anyway. Nginx tells the app the original request was HTTPS by sending an `X-Forwarded-Proto` header, and the app runs with `--proxy-headers` so it trusts that and builds correct links.

Cloudflare is only my DNS provider (DNS only, grey cloud). It is not in the path of the traffic, so it never sees or decrypts the connection.

The HTTP-to-HTTPS redirect is in place too. This is what both names return on HTTP:

```
HTTP/1.1 301 Moved Permanently
Location: https://sharavjiwrajka.me/
```

and the same with `www` for the second name.

## 5. How to check it in Chrome

1. Open https://sharavjiwrajka.me.
2. Click the small icon at the left end of the address bar.
3. Click "Connection is secure", then "Certificate is valid".
4. The certificate window shows the name it was issued to, that it was issued by Let's Encrypt, and the valid-from and valid-to dates.

When I did this, Chrome said the connection is secure and showed the certificate was issued by Let's Encrypt. The page also loaded fully styled with no warning.

One mistake I caught earlier: my DNS records were set to Proxied (orange cloud), which put Cloudflare in front of my server. With that on, visitors would have been shown Cloudflare's certificate, not mine, and this write-up would have been wrong. I turned both records to DNS only, then requested the certificate.

## 6. Evidence

Command run on the VM, with its real output:

```
$ echo | openssl s_client -connect sharavjiwrajka.me:443 -servername sharavjiwrajka.me 2>/dev/null | openssl x509 -noout -subject -issuer -dates -ext subjectAltName
subject=CN = sharavjiwrajka.me
issuer=C = US, O = Let's Encrypt, CN = YE2
notBefore=Oct  8 18:03:10 2026 GMT
notAfter=Jan  6 18:03:09 2027 GMT
X509v3 Subject Alternative Name: 
    DNS:sharavjiwrajka.me, DNS:www.sharavjiwrajka.me
```
