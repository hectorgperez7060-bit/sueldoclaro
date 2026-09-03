-- La sesion se cortaba a los 15 minutos y el usuario perdia lo que estaba
-- cargando. Los refresh tokens vivian en la memoria del proceso, y en Vercel
-- cada instancia tiene su propia memoria: el /auth/refresh caia en otra
-- instancia, no encontraba el jti y devolvia 401. Ahora se guardan en la base,
-- que es la unica memoria compartida entre instancias.
BEGIN;

CREATE TABLE IF NOT EXISTS public.refresh_token (
  jti         varchar(64) PRIMARY KEY,
  usuario_id  uuid NOT NULL REFERENCES public.usuario(id) ON DELETE CASCADE,
  expira_en   timestamptz NOT NULL,
  created_at  timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_refresh_token_usuario_id
  ON public.refresh_token(usuario_id);
CREATE INDEX IF NOT EXISTS ix_refresh_token_expira_en
  ON public.refresh_token(expira_en);

DO $$ BEGIN
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'sueldoclaro') THEN
    GRANT SELECT, INSERT, UPDATE, DELETE ON public.refresh_token TO sueldoclaro;
  END IF;
END $$;

COMMIT;
