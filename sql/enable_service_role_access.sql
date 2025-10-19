-- Enable service_role access to bot tables
-- Ces policies permettent au service_role de bypasser RLS

-- =============================================
-- TYPING EVENTS
-- =============================================
ALTER TABLE public.typing_events ENABLE ROW LEVEL SECURITY;

-- Policy pour service_role (SELECT)
CREATE POLICY "service_role_select_typing_events" 
ON public.typing_events 
FOR SELECT 
TO service_role 
USING (true);

-- Policy pour service_role (INSERT/UPDATE)
CREATE POLICY "service_role_upsert_typing_events" 
ON public.typing_events 
FOR ALL 
TO service_role 
USING (true) 
WITH CHECK (true);

-- =============================================
-- MESSAGES
-- =============================================
ALTER TABLE public.messages ENABLE ROW LEVEL SECURITY;

-- Policy pour service_role (SELECT)
CREATE POLICY "service_role_select_messages" 
ON public.messages 
FOR SELECT 
TO service_role 
USING (true);

-- Policy pour service_role (INSERT)
CREATE POLICY "service_role_insert_messages" 
ON public.messages 
FOR INSERT 
TO service_role 
WITH CHECK (true);

-- =============================================
-- BOT MEMORY
-- =============================================
ALTER TABLE public.bot_memory ENABLE ROW LEVEL SECURITY;

-- Policy pour service_role (ALL)
CREATE POLICY "service_role_all_bot_memory" 
ON public.bot_memory 
FOR ALL 
TO service_role 
USING (true) 
WITH CHECK (true);

-- =============================================
-- BOT PROFILES
-- =============================================
ALTER TABLE public.bot_profiles ENABLE ROW LEVEL SECURITY;

-- Policy pour service_role (SELECT)
CREATE POLICY "service_role_select_bot_profiles" 
ON public.bot_profiles 
FOR SELECT 
TO service_role 
USING (true);

-- =============================================
-- PROFILES
-- =============================================
-- Policy pour service_role (SELECT pour JOIN)
CREATE POLICY "service_role_select_profiles" 
ON public.profiles 
FOR SELECT 
TO service_role 
USING (true);
