import { json, error } from '@sveltejs/kit';
import { env } from '$env/dynamic/private';
import { authHeaders } from '$lib/server/auth-proxy';
import type { RequestHandler } from './$types';

const BACKEND_URL = env.BACKEND_URL || 'http://localhost:8001';

export const GET: RequestHandler = async ({ request }) => {
  const res = await fetch(`${BACKEND_URL}/api/submissions`, {
    headers: authHeaders(request)
  });
  if (!res.ok) throw error(res.status, 'Erro ao buscar submissions');
  return json(await res.json());
};

// POST e PUBLICO — formulario do cliente final; o backend resolve o tenant pelo flow.
export const POST: RequestHandler = async ({ request }) => {
  const body = await request.json();
  const res = await fetch(`${BACKEND_URL}/api/submissions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  });
  if (!res.ok) throw error(res.status, 'Erro ao criar submission');
  return json(await res.json(), { status: 201 });
};
