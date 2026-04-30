import { json, error } from '@sveltejs/kit';
import { uploadImage } from '$lib/server/blob';
import type { RequestHandler } from './$types';

const MAX_BYTES = 5 * 1024 * 1024; // 5 MB
const ALLOWED = new Set(['image/jpeg', 'image/png', 'image/webp', 'image/gif']);
const EXT_BY_TYPE: Record<string, string> = {
  'image/jpeg': 'jpg',
  'image/png': 'png',
  'image/webp': 'webp',
  'image/gif': 'gif'
};

function safeSlug(s: string | null | undefined, fallback: string): string {
  if (!s) return fallback;
  return s
    .toLowerCase()
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .replace(/[^a-z0-9_-]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 60) || fallback;
}

export const POST: RequestHandler = async ({ request }) => {
  const form = await request.formData();
  const file = form.get('file');
  if (!(file instanceof File)) throw error(400, 'Missing file');

  if (file.size > MAX_BYTES) throw error(413, `File too large (max ${MAX_BYTES / 1024 / 1024} MB)`);
  if (!ALLOWED.has(file.type)) throw error(415, `Unsupported type: ${file.type}`);

  const tenant = safeSlug(form.get('tenant_id') as string | null, 'tenant_1');
  const flowId = safeSlug(form.get('flow_id') as string | null, 'misc');
  const nodeId = safeSlug(form.get('node_id') as string | null, 'misc');
  const optionId = safeSlug(form.get('option_id') as string | null, '');

  const ext = EXT_BY_TYPE[file.type];
  const ts = Date.now();
  const rand = Math.random().toString(36).slice(2, 8);
  const tail = optionId ? `${nodeId}-${optionId}` : nodeId;
  const blobName = `${tenant}/${flowId}/${tail}-${ts}-${rand}.${ext}`;

  const buf = Buffer.from(await file.arrayBuffer());
  const url = await uploadImage({ buffer: buf, contentType: file.type, blobName });

  return json({ url, blobName, size: file.size, type: file.type }, { status: 201 });
};
