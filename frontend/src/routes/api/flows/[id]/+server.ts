import { json, error } from '@sveltejs/kit';
import { env } from '$env/dynamic/private';
import type { RequestHandler } from './$types';

const BACKEND_URL = env.BACKEND_URL || 'http://localhost:8001';

export const GET: RequestHandler = async ({ params }) => {
  const res = await fetch(`${BACKEND_URL}/api/flows/${params.id}`);
  if (!res.ok) throw error(res.status, 'Flow nao encontrado');
  return json(await res.json());
};

export const PUT: RequestHandler = async ({ params, request }) => {
  const body = await request.json();
  const res = await fetch(`${BACKEND_URL}/api/flows/${params.id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  });
  if (!res.ok) throw error(res.status, 'Erro ao atualizar flow');
  return json(await res.json());
};

export const DELETE: RequestHandler = async ({ params }) => {
  const res = await fetch(`${BACKEND_URL}/api/flows/${params.id}`, {
    method: 'DELETE'
  });
  if (!res.ok) throw error(res.status, 'Erro ao deletar flow');
  return json({ ok: true });
};
