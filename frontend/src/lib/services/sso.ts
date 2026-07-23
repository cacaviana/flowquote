/**
 * SSO Petra Suite — cookie `petra_sso` no dominio pai `.petrasuite.ai`.
 * O JSON do cookie tem o mesmo shape da sessao localStorage `petra_session`
 * (tokens + user + tenant + products). Nao e HttpOnly de proposito (v1):
 * os apps da suite leem o cookie via JS para entrar logados sem novo login.
 */
import { setSession, type PetraSession } from '$lib/services/session';

const COOKIE_NAME = 'petra_sso';
const COOKIE_ATTRS = 'Domain=.petrasuite.ai; Path=/; Secure; SameSite=Lax';

function onPetraDomain(): boolean {
  return typeof location !== 'undefined' && location.hostname.endsWith('petrasuite.ai');
}

export function writeSsoCookie(sessionJson: string): void {
  if (!onPetraDomain()) return;
  document.cookie = `${COOKIE_NAME}=${encodeURIComponent(sessionJson)}; ${COOKIE_ATTRS}; Max-Age=28800`;
}

export function readSsoCookie(): string | null {
  if (typeof document === 'undefined') return null;
  const entry = document.cookie.split('; ').find((c) => c.startsWith(`${COOKIE_NAME}=`));
  if (!entry) return null;
  try {
    return decodeURIComponent(entry.slice(COOKIE_NAME.length + 1));
  } catch {
    return null;
  }
}

export function clearSsoCookie(): void {
  if (!onPetraDomain()) return;
  document.cookie = `${COOKIE_NAME}=; ${COOKIE_ATTRS}; Max-Age=0`;
}

/**
 * Tenta adotar a sessao do cookie petra_sso como sessao local do Quanto.
 * Retorna a sessao adotada, 'denied' se o plano nao inclui o Quanto,
 * ou null quando nao ha cookie utilizavel.
 */
export function tryAdoptSsoSession(): PetraSession | 'denied' | null {
  const raw = readSsoCookie();
  if (!raw) return null;
  try {
    const sso = JSON.parse(raw);
    if (!sso?.access_token) return null;
    const products: string[] = Array.isArray(sso.products)
      ? sso.products.map((p: any) => (typeof p === 'string' ? p : p?.slug)).filter(Boolean)
      : [];
    const isMaster = sso.tenant?.is_master === true;
    if (!products.includes('quanto') && !isMaster) return 'denied';

    const nova: PetraSession = {
      access_token: sso.access_token,
      refresh_token: sso.refresh_token,
      user: sso.user ?? null,
      tenant: sso.tenant ?? null,
      products
    };
    setSession(nova);
    return nova;
  } catch {
    return null;
  }
}
