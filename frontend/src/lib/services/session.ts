/**
 * Sessao Petra Suite — armazenada em localStorage sob a chave `petra_session`.
 *
 * O token JWT e emitido pela identidade central (suite-api.petrasuite.ai) e
 * carrega tenant_id/products nas claims — o backend valida tudo; aqui so
 * guardamos e anexamos o Bearer nas chamadas admin.
 */

const SESSION_KEY = 'petra_session';

export interface PetraSession {
	access_token: string;
	refresh_token?: string;
	user: { id?: string; name?: string; email?: string } | null;
	tenant: { id?: string; slug?: string; is_master?: boolean } | null;
	products: string[];
}

export function getSession(): PetraSession | null {
	if (typeof localStorage === 'undefined') return null;
	const raw = localStorage.getItem(SESSION_KEY);
	if (!raw) return null;
	try {
		const parsed = JSON.parse(raw) as PetraSession;
		return parsed?.access_token ? parsed : null;
	} catch {
		return null;
	}
}

export function setSession(session: PetraSession): void {
	localStorage.setItem(SESSION_KEY, JSON.stringify(session));
}

export function clearSession(): void {
	localStorage.removeItem(SESSION_KEY);
}

export function getTenantSlug(): string {
	const s = getSession();
	return s?.tenant?.slug || '';
}

/** fetch com Authorization: Bearer quando ha sessao (chamadas admin). */
export async function authFetch(input: RequestInfo | URL, init: RequestInit = {}): Promise<Response> {
	const session = getSession();
	const headers = new Headers(init.headers);
	if (session?.access_token && !headers.has('Authorization')) {
		headers.set('Authorization', `Bearer ${session.access_token}`);
	}
	const res = await fetch(input, { ...init, headers });
	if (res.status === 401 && typeof location !== 'undefined' && location.pathname.startsWith('/admin')) {
		clearSession();
		location.href = '/login';
	}
	return res;
}
