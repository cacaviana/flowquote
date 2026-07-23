/** Repassa o header Authorization do cliente para o backend FastAPI. */
export function authHeaders(
	request: Request,
	extra: Record<string, string> = {}
): Record<string, string> {
	const auth = request.headers.get('authorization');
	return auth ? { ...extra, Authorization: auth } : extra;
}
