import { json, error } from '@sveltejs/kit';
import { env } from '$env/dynamic/private';
import type { RequestHandler } from './$types';

const BACKEND_URL = env.BACKEND_URL || 'http://localhost:8001';

export const GET: RequestHandler = async ({ params }) => {
  const res = await fetch(`${BACKEND_URL}/api/flows/slug/${params.slug}`);
  if (!res.ok) throw error(res.status, 'Flow nao encontrado');
  return json(await res.json());
};
