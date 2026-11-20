-- Seoul Eats update 5: menu photos + menu items (also includes update 3+4). Safe to run more than once.
-- Supabase -> SQL Editor -> New query -> paste ALL -> Run

alter table public.profiles add column if not exists verified   boolean not null default false;
alter table public.profiles add column if not exists avatar_url text;
revoke update on public.profiles from authenticated;
grant update (username, country, avatar_url) on public.profiles to authenticated;

create table if not exists public.menu_photos (
  id            bigint generated always as identity primary key,
  restaurant_id text not null,
  url           text not null,
  user_id       uuid references public.profiles(id) on delete set null default auth.uid(),
  approved      boolean not null default false,
  created_at    timestamptz not null default now()
);
create table if not exists public.menu_items (
  id            bigint generated always as identity primary key,
  restaurant_id text not null,
  name_ko       text not null check (char_length(name_ko) between 1 and 60),
  price         integer check (price between 0 and 10000000),
  user_id       uuid references public.profiles(id) on delete set null default auth.uid(),
  approved      boolean not null default false,
  created_at    timestamptz not null default now()
);
create index if not exists menu_photos_r on public.menu_photos(restaurant_id);
create index if not exists menu_items_r  on public.menu_items(restaurant_id);

alter table public.menu_photos enable row level security;
alter table public.menu_items  enable row level security;

drop policy if exists "read menu photos" on public.menu_photos;
create policy "read menu photos" on public.menu_photos for select to anon, authenticated using (approved or user_id = auth.uid());
drop policy if exists "add menu photos" on public.menu_photos;
create policy "add menu photos" on public.menu_photos for insert to authenticated with check (user_id = auth.uid() and approved = false);

drop policy if exists "read menu items" on public.menu_items;
create policy "read menu items" on public.menu_items for select to anon, authenticated using (approved or user_id = auth.uid());
drop policy if exists "add menu items" on public.menu_items;
create policy "add menu items" on public.menu_items for insert to authenticated with check (user_id = auth.uid() and approved = false);

grant select on public.menu_photos, public.menu_items to anon, authenticated;
grant insert on public.menu_photos, public.menu_items to authenticated;
