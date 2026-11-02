-- Hongdae Eats: reviews table
-- Supabase → SQL Editor → New query → paste all of this → Run

create table if not exists public.reviews (
  id            uuid primary key default gen_random_uuid(),
  created_at    timestamptz not null default now(),
  restaurant_id text not null check (char_length(restaurant_id) between 5 and 40),
  rating        smallint not null check (rating between 1 and 5),
  tourist       text not null check (tourist in ('yes','no','unsure')),
  solo          text not null check (solo    in ('yes','no','unsure')),
  halal         text not null check (halal   in ('yes','no','unsure')),
  veg           text not null check (veg     in ('yes','no','unsure')),
  english       text not null check (english in ('yes','no','unsure')),
  cards         text not null check (cards   in ('yes','no','unsure')),
  two           text not null check (two     in ('yes','no','unsure')),
  body          text check (char_length(body) <= 2000),
  author_name   text not null check (char_length(author_name) between 1 and 40),
  country       text check (char_length(country) <= 40),
  is_team       boolean not null default false,  -- set to true by hand in Table Editor for your own reviews
  hidden        boolean not null default false   -- set to true by hand to hide a reported review
);

create index if not exists reviews_restaurant_idx on public.reviews (restaurant_id);

alter table public.reviews enable row level security;

-- Anyone can read reviews that are not hidden
drop policy if exists "read visible reviews" on public.reviews;
create policy "read visible reviews" on public.reviews
  for select to anon, authenticated
  using (hidden = false);

-- Anyone can add a review, but cannot mark it as Team or hidden
drop policy if exists "add reviews" on public.reviews;
create policy "add reviews" on public.reviews
  for insert to anon, authenticated
  with check (is_team = false and hidden = false);

-- No update / delete policies: only you (from the dashboard) can edit or delete.

grant select, insert on public.reviews to anon, authenticated;
