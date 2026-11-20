-- Seoul Eats update 6: online menu links (QR menus). Safe to run more than once.
create table if not exists public.menu_links (
  id            bigint generated always as identity primary key,
  restaurant_id text not null,
  url           text not null check (url ~* '^https?://' and char_length(url) <= 500),
  user_id       uuid references public.profiles(id) on delete set null default auth.uid(),
  approved      boolean not null default false,
  created_at    timestamptz not null default now()
);
create index if not exists menu_links_r on public.menu_links(restaurant_id);
alter table public.menu_links enable row level security;
drop policy if exists "read menu links" on public.menu_links;
create policy "read menu links" on public.menu_links for select to anon, authenticated using (approved or user_id = auth.uid());
drop policy if exists "add menu links" on public.menu_links;
create policy "add menu links" on public.menu_links for insert to authenticated with check (user_id = auth.uid() and approved = false);
grant select on public.menu_links to anon, authenticated;
grant insert on public.menu_links to authenticated;
