-- Hongdae Eats: update 2 (includes update 1, safe to run even if you already ran update 1)
-- - removes the "2-portion minimum?" question
-- - adds photos
-- - adds user accounts (username + country)
-- - reviews must be approved by you before they show
-- Supabase → SQL Editor → New query → paste all of this → Run

----------------------------------------------------------------- update 1
alter table public.reviews drop column if exists two;
alter table public.reviews add column if not exists photos text[] not null default '{}'
  check (cardinality(photos) <= 5);

insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('review-photos', 'review-photos', true, 5242880, array['image/jpeg','image/png','image/webp'])
on conflict (id) do update
  set public = true, file_size_limit = 5242880, allowed_mime_types = array['image/jpeg','image/png','image/webp'];

----------------------------------------------------------------- profiles
create table if not exists public.profiles (
  id         uuid primary key references auth.users(id) on delete cascade,
  username   text not null unique check (username ~ '^[A-Za-z0-9_.]{3,20}$'),
  country    text not null check (char_length(country) between 2 and 40),
  created_at timestamptz not null default now()
);
alter table public.profiles enable row level security;

drop policy if exists "profiles are public" on public.profiles;
create policy "profiles are public" on public.profiles
  for select to anon, authenticated using (true);

drop policy if exists "create own profile" on public.profiles;
create policy "create own profile" on public.profiles
  for insert to authenticated with check (id = auth.uid());

drop policy if exists "update own profile" on public.profiles;
create policy "update own profile" on public.profiles
  for update to authenticated using (id = auth.uid()) with check (id = auth.uid());

grant select on public.profiles to anon, authenticated;
grant insert, update on public.profiles to authenticated;

----------------------------------------------------------------- reviews: owner + approval
alter table public.reviews add column if not exists user_id uuid references public.profiles(id) on delete set null;
alter table public.reviews add column if not exists approved boolean not null default false;
alter table public.reviews alter column author_name drop not null;

-- Everyone sees approved reviews; you also see your own reviews that are waiting
drop policy if exists "read visible reviews" on public.reviews;
create policy "read visible reviews" on public.reviews
  for select to anon, authenticated
  using (hidden = false and (approved = true or user_id = auth.uid()));

-- Only signed-in users can post, only as themselves, never pre-approved
drop policy if exists "add reviews" on public.reviews;
create policy "add reviews" on public.reviews
  for insert to authenticated
  with check (user_id = auth.uid() and approved = false and is_team = false and hidden = false);

revoke insert on public.reviews from anon;
grant select on public.reviews to anon, authenticated;
grant insert on public.reviews to authenticated;

----------------------------------------------------------------- photos: signed-in users only
drop policy if exists "upload review photos" on storage.objects;
create policy "upload review photos" on storage.objects
  for insert to authenticated
  with check (bucket_id = 'review-photos');
