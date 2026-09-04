import { json, error } from '@sveltejs/kit';
import { env } from '$env/dynamic/private';
import { authHeaders } from '$lib/server/auth-proxy';
import type { RequestHandler } from './$types';

const BACKEND_URL = env.BACKEND_URL || 'http://localhost:8001';

export const POST: RequestHandler = async ({ request }) => {
	const body = await request.json();
	const res = await fetch(`${BACKEND_URL}/api/flows/generate`, {
		method: 'POST',
		headers: authHeaders(request, { 'Content-Type': 'application/json' }),
		body: JSON.stringify(body)
	});
	const data = await res.json().catch(() => ({}));
	if (!res.ok) throw error(res.status, data?.detail ?? 'Erreur de génération');
	return json(data);
};
