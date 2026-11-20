-- Update 3: verified (blue tick) reviewers
-- Supabase -> SQL Editor -> New query -> paste -> Run
alter table public.profiles add column if not exists verified boolean not null default false;

-- Users may edit only username/country, never "verified"
revoke update on public.profiles from authenticated;
grant update (username, country) on public.profiles to authenticated;

-- To give a friend the blue tick (run in SQL Editor):
-- update public.profiles set verified = true where username = 'friend_username';
