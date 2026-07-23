import { json } from '@sveltejs/kit';
import { env } from '$env/dynamic/private';
import { authHeaders } from '$lib/server/auth-proxy';
import type { RequestHandler } from './$types';

const BACKEND_URL = env.BACKEND_URL || 'http://localhost:8001';

export const GET: RequestHandler = async ({ request }) => {
  const res = await fetch(`${BACKEND_URL}/api/settings/ai`, {
    headers: authHeaders(request)
  });
  const data = await res.json();
  return json(data, { status: res.status });
};

export const PUT: RequestHandler = async ({ request }) => {
  const body = await request.json();
  const res = await fetch(`${BACKEND_URL}/api/settings/ai`, {
    method: 'PUT',
    headers: authHeaders(request, { 'Content-Type': 'application/json' }),
    body: JSON.stringify(body)
  });
  const data = await res.json();
  return json(data, { status: res.status });
};
