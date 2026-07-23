import { json, error } from '@sveltejs/kit';
import { env } from '$env/dynamic/private';
import { authHeaders } from '$lib/server/auth-proxy';
import type { RequestHandler } from './$types';

const BACKEND_URL = env.BACKEND_URL || 'http://localhost:8001';

export const GET: RequestHandler = async ({ params, request }) => {
  const res = await fetch(`${BACKEND_URL}/api/submissions/${params.id}`, {
    headers: authHeaders(request)
  });
  if (!res.ok) throw error(res.status, 'Submission nao encontrada');
  return json(await res.json());
};
