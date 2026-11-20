-- Update 3+4: blue tick + profile photos. Safe to run more than once.
-- Supabase -> SQL Editor -> New query -> paste all -> Run
alter table public.profiles add column if not exists verified   boolean not null default false;
alter table public.profiles add column if not exists avatar_url text;

-- Users can edit their own username, country and photo, never "verified"
revoke update on public.profiles from authenticated;
grant update (username, country, avatar_url) on public.profiles to authenticated;

-- Give someone the blue tick:
-- update public.profiles set verified = true where username = 'their_username';
