import { json, error } from '@sveltejs/kit';
import { env } from '$env/dynamic/private';
import type { RequestHandler } from './$types';

const BACKEND_URL = env.BACKEND_URL || 'http://localhost:8001';

export const GET: RequestHandler = async ({ url }) => {
  const flowType = url.searchParams.get('flow_type');
  const backendUrl = flowType
    ? `${BACKEND_URL}/api/flows?flow_type=${encodeURIComponent(flowType)}`
    : `${BACKEND_URL}/api/flows`;
  const res = await fetch(backendUrl);
  if (!res.ok) throw error(res.status, 'Erro ao buscar flows');
  const data = await res.json();
  return json(data.flows ?? data);
};

export const POST: RequestHandler = async ({ request }) => {
  const body = await request.json();
  const res = await fetch(`${BACKEND_URL}/api/flows`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  });
  if (!res.ok) throw error(res.status, 'Erro ao criar flow');
  return json(await res.json(), { status: 201 });
};
