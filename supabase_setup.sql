-- 이음이 Supabase 테이블 수정본
-- 오류 원인:
-- 기존 eumi_users.id가 text인데, family_links에서 uuid 외래키로 연결하려 해서 타입 충돌 발생.
-- 해결:
-- id / user_id 계열을 text 기준으로 통일하고, family_links는 안전하게 재생성합니다.

create extension if not exists "pgcrypto";

-- 1) 사용자 테이블
create table if not exists public.eumi_users (
    id text primary key default gen_random_uuid()::text,
    phone text not null unique,
    name text not null,
    password_hash text not null,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

alter table public.eumi_users add column if not exists id text;
alter table public.eumi_users add column if not exists phone text;
alter table public.eumi_users add column if not exists name text;
alter table public.eumi_users add column if not exists password_hash text;
alter table public.eumi_users add column if not exists created_at timestamptz not null default now();
alter table public.eumi_users add column if not exists updated_at timestamptz not null default now();

-- 이전 버전에 role 컬럼이 not null로 만들어졌을 수 있으므로 새 코드와 충돌하지 않게 정리
alter table public.eumi_users add column if not exists role text default 'user';
alter table public.eumi_users alter column role set default 'user';
alter table public.eumi_users alter column role drop not null;

-- id가 자동 생성되도록 보강
alter table public.eumi_users alter column id set default gen_random_uuid()::text;

-- phone unique 보강
do $$
begin
    if not exists (
        select 1
        from pg_constraint
        where conname = 'eumi_users_phone_key'
          and conrelid = 'public.eumi_users'::regclass
    ) then
        alter table public.eumi_users add constraint eumi_users_phone_key unique (phone);
    end if;
end $$;

-- 2) 가족 연결 테이블
-- 기존 family_links가 uuid 컬럼으로 잘못 만들어졌을 수 있으므로 연결정보 테이블만 재생성합니다.
-- 테스트 단계에서는 가족 연결만 다시 하면 됩니다. eumi_users와 usage_logs는 지우지 않습니다.
drop table if exists public.family_links;

create table public.family_links (
    id text primary key default gen_random_uuid()::text,

    -- caregiver: 기록을 볼 수 있는 사람
    caregiver_user_id text,

    -- caree: 도움받는 사람 / 기록 주인
    caree_user_id text,

    -- 미가입 사용자를 위해 전화번호도 보관
    caregiver_phone text,
    caree_phone text,

    -- caregiver 화면에서 caree를 어떻게 부를지. 예: 엄마, 아빠, 장모님
    relation_label text,

    -- caree 화면에서 caregiver를 어떻게 부를지. 예: 아들, 딸
    reverse_relation_label text,

    requested_by_user_id text,

    -- pending_signup: 상대가 아직 가입 전
    -- pending: 상대 승인 대기
    -- active: 연결 완료
    -- rejected: 거절
    status text not null default 'pending'
        check (status in ('pending_signup', 'pending', 'active', 'rejected')),

    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

-- 3) 사용 기록 테이블
create table if not exists public.usage_logs (
    id text primary key default gen_random_uuid()::text,
    user_id text,
    question text,
    answer text,
    has_image boolean default false,

    -- 자동 분류 폴더
    category text default '기타',
    place_name text default '미분류',
    task_name text default '확인하기',
    short_title text default '화면 질문',
    folder_key text default '기타__미분류',

    created_at timestamptz not null default now()
);

alter table public.usage_logs add column if not exists user_id text;
alter table public.usage_logs add column if not exists question text;
alter table public.usage_logs add column if not exists answer text;
alter table public.usage_logs add column if not exists has_image boolean default false;
alter table public.usage_logs add column if not exists category text default '기타';
alter table public.usage_logs add column if not exists place_name text default '미분류';
alter table public.usage_logs add column if not exists task_name text default '확인하기';
alter table public.usage_logs add column if not exists short_title text default '화면 질문';
alter table public.usage_logs add column if not exists folder_key text default '기타__미분류';
alter table public.usage_logs add column if not exists created_at timestamptz not null default now();

-- 기존 usage_logs.user_id가 uuid 등 다른 타입이면 text로 변환
do $$
declare
    col_type text;
begin
    select data_type into col_type
    from information_schema.columns
    where table_schema = 'public'
      and table_name = 'usage_logs'
      and column_name = 'user_id';

    if col_type is not null and col_type <> 'text' then
        execute 'alter table public.usage_logs alter column user_id type text using user_id::text';
    end if;
end $$;

-- 4) 인덱스
create index if not exists idx_eumi_users_phone on public.eumi_users(phone);
create index if not exists idx_family_links_caregiver on public.family_links(caregiver_user_id);
create index if not exists idx_family_links_caree on public.family_links(caree_user_id);
create index if not exists idx_family_links_caregiver_phone on public.family_links(caregiver_phone);
create index if not exists idx_family_links_caree_phone on public.family_links(caree_phone);
create index if not exists idx_family_links_status on public.family_links(status);
create index if not exists idx_usage_logs_user_id on public.usage_logs(user_id);
create index if not exists idx_usage_logs_folder_key on public.usage_logs(folder_key);
