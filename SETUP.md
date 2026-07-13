# Turning on live shared voting

The site works immediately in **preview mode** (votes save to the visitor's own
browser). To make voting **shared and live across everyone**, connect a free
Supabase database. ~5 minutes, one-time.

## 1. Create a Supabase project
- Go to https://supabase.com → sign in → **New project** (free tier is fine).
- Wait for it to finish provisioning.

## 2. Create the table + counts view
In the Supabase dashboard: **SQL Editor → New query**, paste this, and click **Run**.

```sql
-- Votes table
create table gem_votes (
  id uuid primary key default gen_random_uuid(),
  game text not null,
  choice text not null check (choice in ('gem','meh')),
  voter text,
  created_at timestamptz default now()
);

-- Lock the raw table down, but allow anonymous visitors to INSERT a vote
alter table gem_votes enable row level security;
grant insert on gem_votes to anon;

create policy "anon can cast a vote"
  on gem_votes for insert to anon
  with check (choice in ('gem','meh'));

-- Public aggregate view (exposes only counts, never individual rows)
create view gem_vote_counts
  with (security_invoker = off) as
  select game,
         count(*) filter (where choice = 'gem') as gems,
         count(*) filter (where choice = 'meh') as mehs
  from gem_votes
  group by game;

grant select on gem_vote_counts to anon;
```

## 3. Paste your keys into the site
- In Supabase: **Project Settings → API**.
- Copy the **Project URL** and the **anon / public** key.
- Open `index.html`, find the CONFIG block near the bottom, and fill in:

```js
const SUPABASE_URL = "https://YOURPROJECT.supabase.co";
const SUPABASE_ANON_KEY = "eyJ...your-anon-key...";
```

The anon key is **safe to commit** to a public repo — it only allows the two
actions the SQL policy permits (insert a vote, read the aggregate counts).

## 4. Commit + push
That's it. On the next load the yellow "preview mode" banner disappears and every
visitor sees the same shared tallies.

## Notes
- **One vote per game per browser** is enforced client-side (localStorage). It's a
  light guardrail, not fraud-proof — fine for a fun community poll.
- To reset or moderate votes, use the Supabase **Table Editor** on `gem_votes`.
- To see totals any time: `select * from gem_vote_counts order by gems desc;`
