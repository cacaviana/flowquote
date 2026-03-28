import { json, error } from '@sveltejs/kit';
import { env } from '$env/dynamic/private';
import type { RequestHandler } from './$types';

const BACKEND_URL = env.BACKEND_URL || 'http://localhost:8001';

export const GET: RequestHandler = async () => {
  const res = await fetch(`${BACKEND_URL}/api/submissions`);
  if (!res.ok) throw error(res.status, 'Erro ao buscar submissions');
  return json(await res.json());
};

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
