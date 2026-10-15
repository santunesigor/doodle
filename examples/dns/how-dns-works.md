# How does my browser find a website?

## In three sentences

1. Computers find each other by **numbers** (IP addresses), but people type **names** like `www.example.com`.
2. DNS is the internet's phone book: a **chain of servers** that turns the name into a number, one piece at a time.
3. Answers can be **cached** until their TTL expires, so a repeat lookup may avoid some or all of those questions.

The names and addresses below illustrate an IPv4 address lookup; they are not a live DNS result.
The full lookup assumes the relevant caches are empty and omits the browser's interaction with the operating system.

---

## Pieces you need to know

| Piece | What it is |
|---|---|
| **IP address** | The number of a computer on the internet, like `203.0.113.10`. |
| **Resolver** | The server that does the asking for you, usually your internet provider's or a public one like `1.1.1.1`. |
| **Root server** | Knows who is in charge of each ending (`.com`, `.org`, `.br`…). |
| **TLD server** | The server for one ending, like `.com`. It knows who is in charge of `example.com`. |
| **Authoritative server** | The server that holds the real answer for `example.com`. |
| **TTL** | "Time to live": how many seconds an answer may be kept in a cache. |

---

## Step 1: a name is a path in a tree, read from right to left

<!-- doodle
tree: DNS is a tree, read from right to left
> www.example.com  =  "com", then "example", then "www"
. (root) | the top of the tree | info
  com | a top-level domain (TLD)
    example.com | holds the real answer | ok
      www.example.com | 203.0.113.10 | ok
  org | another TLD
  br | another TLD
-->
![DNS is a tree, read from right to left](img/how-dns-works-dns-is-a-tree-read-from-right-to-left.svg)

- No single server needs the whole tree. Each zone holds its own records and can **delegate part of the tree** to other servers.
- That is why the lookup is a series of questions, not a single one.

---

## Step 2: the resolver asks, level by level, for you

<!-- doodle
sequence: One full lookup
Browser | info
Browser -> Resolver: where is www.example.com?
Resolver -> Root server: who handles .com?
Root server ~> Resolver: ask the .com servers
Resolver -> .com server: who handles example.com?
.com server ~> Resolver: ask example.com's servers
Resolver -> example.com server: where is www.example.com?
example.com server ~> Resolver: 203.0.113.10 | ok
Resolver ~> Browser: 203.0.113.10 | ok
-->
![One full lookup](img/how-dns-works-one-full-lookup.svg)

- Your browser asks **one** question. The resolver does all the walking.
- The root and `.com` servers return **referrals**: "ask these servers next". The authoritative server returns the address.

---

## Step 3: most of the time, a cache answers first

<!-- doodle
stack: Who answers, from closest to farthest
@arrow
Browser cache | already asked a moment ago? | ok
Operating system cache | shared by every app | ok
Home router | many routers keep a small cache
Resolver | has a big shared cache, walks the tree only if needed | info
-->
![Who answers, from closest to farthest](img/how-dns-works-who-answers-from-closest-to-farthest.svg)

- The lookup goes down the stack only until **someone already knows** the answer.
- Reusing a cached answer saves DNS lookup time on a later visit.

---

## Step 4: why a changed address takes time to show up

<!-- doodle
cycle: The cache cycle
Full lookup | walks the tree (slow) | info
Answer cached | kept for TTL seconds | ok
Instant answers | everyone near reuses it | ok
TTL expires | the answer is thrown away | warn
-->
![The cache cycle](img/how-dns-works-the-cache-cycle.svg)

- When a site moves to a new IP, **old answers live on until their TTL runs out**.
- That delay is what people call "DNS propagation". Lowering the TTL before a move makes it shorter.

---

## Why it matters

- **"The site works for me but not for you"** is often a DNS cache with an old answer.
- **"Server not found"** means the name could not be turned into a number. The site itself may be fine.

## References

- [RFC 1034: domain hierarchy, referrals, resolvers, and caching](https://www.rfc-editor.org/rfc/rfc1034.html).
