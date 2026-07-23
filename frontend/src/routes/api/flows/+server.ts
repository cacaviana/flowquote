import { json, error } from '@sveltejs/kit';
import { env } from '$env/dynamic/private';
import { authHeaders } from '$lib/server/auth-proxy';
import type { RequestHandler } from './$types';

const BACKEND_URL = env.BACKEND_URL || 'http://localhost:8001';

export const GET: RequestHandler = async ({ url, request }) => {
  const flowType = url.searchParams.get('flow_type');
  const backendUrl = flowType
    ? `${BACKEND_URL}/api/flows?flow_type=${encodeURIComponent(flowType)}`
    : `${BACKEND_URL}/api/flows`;
  const res = await fetch(backendUrl, { headers: authHeaders(request) });
  if (!res.ok) throw error(res.status, 'Erro ao buscar flows');
  const data = await res.json();
  return json(data.flows ?? data);
};

export const POST: RequestHandler = async ({ request }) => {
  const body = await request.json();
  const res = await fetch(`${BACKEND_URL}/api/flows`, {
    method: 'POST',
    headers: authHeaders(request, { 'Content-Type': 'application/json' }),
    body: JSON.stringify(body)
  });
  if (!res.ok) throw error(res.status, 'Erro ao criar flow');
  return json(await res.json(), { status: 201 });
};
