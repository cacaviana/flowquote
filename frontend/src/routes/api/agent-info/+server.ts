import { json } from '@sveltejs/kit';
import { env } from '$env/dynamic/private';
import { authHeaders } from '$lib/server/auth-proxy';
import type { RequestHandler } from './$types';

const BACKEND_URL = env.BACKEND_URL || 'http://localhost:8001';

export const GET: RequestHandler = async ({ request }) => {
  const res = await fetch(`${BACKEND_URL}/api/agent/info`, {
    headers: authHeaders(request)
  });
  if (!res.ok) {
    return json({ error: 'Failed to fetch agent info' }, { status: res.status });
  }
  return json(await res.json());
};
