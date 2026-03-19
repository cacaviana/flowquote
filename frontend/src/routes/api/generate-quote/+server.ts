import { json, error } from '@sveltejs/kit';
import { env } from '$env/dynamic/private';
import type { RequestHandler } from './$types';

const BACKEND_URL = env.BACKEND_URL || 'http://localhost:8001';

export const POST: RequestHandler = async ({ request }) => {
  const body = await request.json();

  try {
    const res = await fetch(`${BACKEND_URL}/api/submissions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });

    if (!res.ok) {
      const errBody = await res.text();
      console.error('Backend error:', res.status, errBody);
      throw error(res.status, `Erreur backend: ${errBody}`);
    }

    const result = await res.json();
    return json(result);
  } catch (e: any) {
    if (e.status) throw e;
    console.error('Backend connection error:', e.message);
    throw error(502, 'Impossible de se connecter au serveur de devis. Verifiez que le backend est demarre.');
  }
};
