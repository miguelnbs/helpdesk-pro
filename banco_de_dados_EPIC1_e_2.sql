-- ============================================================================
-- HelpDesk Pro — Script do Banco de Dados — EPIC 1 e EPIC 2
-- Banco: Supabase (PostgreSQL)
-- Aluno: Miguel Nóbrega Scheidegger
--
-- Este script pode ser executado do zero OU sobre o banco já existente:
-- ele só cria o que falta e recria as políticas de segurança (RLS).
-- Rodar inteiro no Supabase → SQL Editor.
-- ============================================================================


-- ============================================================================
-- 1. TABELAS
-- ============================================================================

-- 1.1 Perfis de usuário (EPIC 1) — vinculados ao Supabase Auth
CREATE TABLE IF NOT EXISTS public.profiles (
  id          UUID        NOT NULL,
  full_name   TEXT        NOT NULL,
  role        TEXT        NOT NULL DEFAULT 'user',      -- 'user' ou 'admin'
  sector      TEXT,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT profiles_pkey PRIMARY KEY (id)
);

-- Ao excluir o usuário no Auth, o perfil é removido junto
ALTER TABLE public.profiles DROP CONSTRAINT IF EXISTS profiles_id_fkey;
ALTER TABLE public.profiles
  ADD CONSTRAINT profiles_id_fkey
  FOREIGN KEY (id) REFERENCES auth.users(id) ON DELETE CASCADE;

ALTER TABLE public.profiles DROP CONSTRAINT IF EXISTS profiles_role_check;
ALTER TABLE public.profiles
  ADD CONSTRAINT profiles_role_check CHECK (role IN ('user', 'admin'));

-- 1.2 Chamados (EPIC 2)
CREATE TABLE IF NOT EXISTS public.tickets (
  id           UUID        NOT NULL DEFAULT gen_random_uuid(),
  title        TEXT        NOT NULL,
  description  TEXT        NOT NULL,
  category     TEXT        NOT NULL,
  priority     TEXT        NOT NULL DEFAULT 'low',      -- low, medium, high, critical
  status       TEXT        NOT NULL DEFAULT 'open',     -- open, in_progress, waiting, resolved, cancelled
  created_by   UUID        NOT NULL REFERENCES public.profiles(id),
  assigned_to  UUID        REFERENCES public.profiles(id),
  created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  resolved_at  TIMESTAMPTZ,
  CONSTRAINT tickets_pkey PRIMARY KEY (id)
);

ALTER TABLE public.tickets DROP CONSTRAINT IF EXISTS tickets_status_check;
ALTER TABLE public.tickets
  ADD CONSTRAINT tickets_status_check
  CHECK (status IN ('open', 'in_progress', 'waiting', 'resolved', 'cancelled'));

ALTER TABLE public.tickets DROP CONSTRAINT IF EXISTS tickets_priority_check;
ALTER TABLE public.tickets
  ADD CONSTRAINT tickets_priority_check
  CHECK (priority IN ('low', 'medium', 'high', 'critical'));

-- 1.3 Histórico de atualizações do chamado (EPIC 2)
-- ON DELETE CASCADE: ao excluir o chamado, o histórico é excluído junto
CREATE TABLE IF NOT EXISTS public.ticket_updates (
  id          UUID        NOT NULL DEFAULT gen_random_uuid(),
  ticket_id   UUID        NOT NULL REFERENCES public.tickets(id) ON DELETE CASCADE,
  author_id   UUID        NOT NULL REFERENCES public.profiles(id),
  message     TEXT        NOT NULL,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT ticket_updates_pkey PRIMARY KEY (id)
);


-- ============================================================================
-- 2. TRIGGER — CRIAÇÃO AUTOMÁTICA DE PERFIL (EPIC 1)
-- Cria o registro em profiles sempre que alguém se cadastra no Supabase Auth
-- ============================================================================

CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
  INSERT INTO public.profiles (id, full_name, role)
  VALUES (
    NEW.id,
    COALESCE(NEW.raw_user_meta_data->>'full_name', 'Usuário'),
    'user'
  );
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();


-- ============================================================================
-- 3. FUNÇÕES AUXILIARES DE PERMISSÃO
-- SECURITY DEFINER evita recursão infinita quando uma política da tabela
-- profiles precisa consultar a própria tabela profiles.
-- ============================================================================

CREATE OR REPLACE FUNCTION public.is_admin()
RETURNS BOOLEAN
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
  SELECT EXISTS (
    SELECT 1 FROM public.profiles WHERE id = auth.uid() AND role = 'admin'
  );
$$;

CREATE OR REPLACE FUNCTION public.my_role()
RETURNS TEXT
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
  SELECT role FROM public.profiles WHERE id = auth.uid();
$$;


-- ============================================================================
-- 4. RLS — ROW LEVEL SECURITY (EPIC 1 e EPIC 2)
-- ============================================================================

ALTER TABLE public.profiles       ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.tickets        ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ticket_updates ENABLE ROW LEVEL SECURITY;

-- Remove políticas antigas (nomes usados nas versões anteriores do projeto)
DROP POLICY IF EXISTS "Usuários autenticados podem ler perfis"             ON public.profiles;
DROP POLICY IF EXISTS "Usuário pode atualizar próprio perfil"              ON public.profiles;
DROP POLICY IF EXISTS "Service pode ler todos os profiles"                 ON public.profiles;
DROP POLICY IF EXISTS "autenticados_podem_ler_perfis"                      ON public.profiles;
DROP POLICY IF EXISTS "usuario_atualiza_proprio_perfil"                    ON public.profiles;
DROP POLICY IF EXISTS "leitura_publica_profiles"                           ON public.profiles;

DROP POLICY IF EXISTS "Usuário pode criar chamado"                         ON public.tickets;
DROP POLICY IF EXISTS "Usuário pode ver seus chamados"                     ON public.tickets;
DROP POLICY IF EXISTS "Admin pode ver todos os chamados"                   ON public.tickets;
DROP POLICY IF EXISTS "Admin pode atualizar chamados"                      ON public.tickets;
DROP POLICY IF EXISTS "Admin pode excluir chamados"                        ON public.tickets;
DROP POLICY IF EXISTS "Service pode ler todos os tickets"                  ON public.tickets;

DROP POLICY IF EXISTS "Usuário pode criar atualização"                     ON public.ticket_updates;
DROP POLICY IF EXISTS "Usuário pode ver atualizações dos seus chamados"    ON public.ticket_updates;
DROP POLICY IF EXISTS "Admin pode ver todas as atualizações"               ON public.ticket_updates;
DROP POLICY IF EXISTS "Service pode ler todos os updates"                  ON public.ticket_updates;

-- Remove também as políticas desta versão (permite rodar o script mais de uma vez)
DROP POLICY IF EXISTS "Autenticados leem perfis"                           ON public.profiles;
DROP POLICY IF EXISTS "Usuario atualiza proprio perfil sem mudar a role"   ON public.profiles;
DROP POLICY IF EXISTS "Admin atualiza perfis"                              ON public.profiles;
DROP POLICY IF EXISTS "Leitura publica de perfis (dashboard)"              ON public.profiles;

DROP POLICY IF EXISTS "Usuario cria chamado proprio"                       ON public.tickets;
DROP POLICY IF EXISTS "Usuario ve seus chamados"                           ON public.tickets;
DROP POLICY IF EXISTS "Admin ve todos os chamados"                         ON public.tickets;
DROP POLICY IF EXISTS "Admin atualiza chamados"                            ON public.tickets;
DROP POLICY IF EXISTS "Admin exclui chamados"                              ON public.tickets;
DROP POLICY IF EXISTS "Leitura publica de chamados (dashboard)"            ON public.tickets;

DROP POLICY IF EXISTS "Usuario responde em chamado proprio"                ON public.ticket_updates;
DROP POLICY IF EXISTS "Usuario ve historico dos seus chamados"             ON public.ticket_updates;
DROP POLICY IF EXISTS "Admin ve todo o historico"                          ON public.ticket_updates;
DROP POLICY IF EXISTS "Leitura publica do historico (dashboard)"           ON public.ticket_updates;

-- ---- profiles -------------------------------------------------------------

CREATE POLICY "Autenticados leem perfis"
  ON public.profiles FOR SELECT TO authenticated
  USING (true);

-- O usuário edita o próprio perfil, mas NÃO pode mudar a própria role
CREATE POLICY "Usuario atualiza proprio perfil sem mudar a role"
  ON public.profiles FOR UPDATE TO authenticated
  USING (auth.uid() = id)
  WITH CHECK (auth.uid() = id AND role = public.my_role());

-- O administrador pode atualizar qualquer perfil (ex.: promover a admin)
CREATE POLICY "Admin atualiza perfis"
  ON public.profiles FOR UPDATE TO authenticated
  USING (public.is_admin())
  WITH CHECK (public.is_admin());

-- Leitura pública: usada pelo dashboard Streamlit (chave anon)
CREATE POLICY "Leitura publica de perfis (dashboard)"
  ON public.profiles FOR SELECT TO anon
  USING (true);

-- ---- tickets --------------------------------------------------------------

CREATE POLICY "Usuario cria chamado proprio"
  ON public.tickets FOR INSERT TO authenticated
  WITH CHECK (auth.uid() = created_by);

CREATE POLICY "Usuario ve seus chamados"
  ON public.tickets FOR SELECT TO authenticated
  USING (auth.uid() = created_by);

CREATE POLICY "Admin ve todos os chamados"
  ON public.tickets FOR SELECT TO authenticated
  USING (public.is_admin());

CREATE POLICY "Admin atualiza chamados"
  ON public.tickets FOR UPDATE TO authenticated
  USING (public.is_admin())
  WITH CHECK (public.is_admin());

CREATE POLICY "Admin exclui chamados"
  ON public.tickets FOR DELETE TO authenticated
  USING (public.is_admin());

CREATE POLICY "Leitura publica de chamados (dashboard)"
  ON public.tickets FOR SELECT TO anon
  USING (true);

-- ---- ticket_updates -------------------------------------------------------

-- Só responde em chamado próprio (ou em qualquer chamado, se admin)
CREATE POLICY "Usuario responde em chamado proprio"
  ON public.ticket_updates FOR INSERT TO authenticated
  WITH CHECK (
    auth.uid() = author_id
    AND (
      public.is_admin()
      OR EXISTS (
        SELECT 1 FROM public.tickets t
        WHERE t.id = ticket_id AND t.created_by = auth.uid()
      )
    )
  );

CREATE POLICY "Usuario ve historico dos seus chamados"
  ON public.ticket_updates FOR SELECT TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM public.tickets t
      WHERE t.id = ticket_id AND t.created_by = auth.uid()
    )
  );

CREATE POLICY "Admin ve todo o historico"
  ON public.ticket_updates FOR SELECT TO authenticated
  USING (public.is_admin());

CREATE POLICY "Leitura publica do historico (dashboard)"
  ON public.ticket_updates FOR SELECT TO anon
  USING (true);


-- ============================================================================
-- 5. PROMOVER UM USUÁRIO A ADMINISTRADOR (executar manualmente)
-- ============================================================================

-- UPDATE public.profiles
-- SET role = 'admin'
-- WHERE id = (SELECT id FROM auth.users WHERE email = 'seu@email.com');


-- ============================================================================
-- 6. CONSULTAS ÚTEIS PARA CONFERÊNCIA
-- ============================================================================

-- Usuários e perfis
-- SELECT u.email, p.full_name, p.role, p.sector, p.created_at
-- FROM auth.users u JOIN public.profiles p ON p.id = u.id ORDER BY p.created_at DESC;

-- Políticas ativas
-- SELECT tablename, policyname, cmd, roles FROM pg_policies
-- WHERE schemaname = 'public' ORDER BY tablename, cmd;
