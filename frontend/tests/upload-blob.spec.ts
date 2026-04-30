import { test, expect } from '@playwright/test';
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';

test.describe('POST /api/upload — Azure Blob', () => {
  const fixturePath = path.join(os.tmpdir(), 'test-pixel.jpg');

  test.beforeAll(() => {
    // 1x1 red JPEG (tiny valid image)
    const b64 =
      '/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAAEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/2wBDAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwA/8AH/AP/Z';
    fs.writeFileSync(fixturePath, Buffer.from(b64, 'base64'));
  });

  test('uploads JPEG and returns public Azure Blob URL', async ({ request }) => {
    const buf = fs.readFileSync(fixturePath);

    const res = await request.post('/api/upload', {
      multipart: {
        file: { name: 'pixel.jpg', mimeType: 'image/jpeg', buffer: buf },
        tenant_id: 'tenant_1',
        flow_id: 'pw-test',
        node_id: 'pw-node'
      }
    });

    expect(res.status()).toBe(201);
    const body = await res.json();
    expect(body.url).toMatch(/^https:\/\/[a-z0-9]+\.blob\.core\.windows\.net\/flowquote-uploads\//);
    expect(body.blobName).toContain('tenant_1/pw-test/pw-node-');
    expect(body.size).toBe(buf.byteLength);
    expect(body.type).toBe('image/jpeg');

    // Fetch the uploaded blob — must be publicly accessible
    const fetched = await request.get(body.url);
    expect(fetched.status()).toBe(200);
    expect(fetched.headers()['content-type']).toBe('image/jpeg');
    expect((await fetched.body()).byteLength).toBe(buf.byteLength);
  });

  test('rejects file too large (>5 MB)', async ({ request }) => {
    const big = Buffer.alloc(6 * 1024 * 1024, 0xff); // 6 MB
    const res = await request.post('/api/upload', {
      multipart: {
        file: { name: 'big.jpg', mimeType: 'image/jpeg', buffer: big }
      }
    });
    expect(res.status()).toBe(413);
  });

  test('rejects unsupported mime type', async ({ request }) => {
    const res = await request.post('/api/upload', {
      multipart: {
        file: { name: 'evil.exe', mimeType: 'application/octet-stream', buffer: Buffer.from('x') }
      }
    });
    expect(res.status()).toBe(415);
  });
});
