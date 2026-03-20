import { test, expect } from '@playwright/test';

/**
 * Anti-hallucination test for "Automação Comercial" flow.
 *
 * The CSV catalog contains:
 *   Camera IP 4MP, Camera IP 8MP, DVR 4/8 canais,
 *   Instalacao camera interna, Instalacao camera externa,
 *   Cabeamento por metro, Central de alarme, Sensor de movimento.
 *
 * Intentionally ABSENT from catalog:
 *   - "Camera 4K Ultra HD"     → selected by client
 *   - "Instalacao embutida teto" → selected by client
 *
 * Expected behavior:
 *   - AI must NOT substitute with a similar catalog product (hallucination).
 *   - Items absent from catalog must appear with price "A consulter" (subtotal = 0).
 *   - Items present in catalog (Central de alarme) must appear with a real price.
 */
test('automacao comercial: absent products show "A consulter", no hallucination', async ({ page }) => {
  // Navigate to the questionnaire
  await page.goto('/q/devis-automacao-comercial');
  await page.waitForSelector('text=Commencer', { timeout: 15000 });

  // ── Start form ──────────────────────────────────────────────────────────────
  await page.fill('input[type="text"]', 'Carlos Teste');
  await page.fill('input[type="email"]', 'carlos@teste.com');
  await page.click('button:has-text("Commencer")');

  // ── Q1: Tipo de ambiente ─────────────────────────────────────────────────────
  await page.waitForSelector('text=Tipo de ambiente a monitorar');
  await page.click('button:has-text("Comercial")');

  // ── Q2: Qual camera — select "Camera 4K Ultra HD" (NOT in CSV) ───────────────
  await page.waitForSelector('text=Qual camera voce deseja?');
  await page.click('button:has-text("Camera 4K Ultra HD")');

  // ── Q3: Quantas cameras ──────────────────────────────────────────────────────
  await page.waitForSelector('text=Quantas cameras?');
  await page.fill('input[type="number"]', '3');
  await page.click('button:has-text("Suivant")');

  // ── Q4: Tipo de instalacao — select "Embutida no teto" (NOT in CSV) ──────────
  await page.waitForSelector('text=Tipo de instalacao');
  await page.click('button:has-text("Embutida no teto")');

  // ── Q5: Metragem de cabeamento ───────────────────────────────────────────────
  await page.waitForSelector('text=Metragem de cabeamento');
  await page.fill('input[type="number"]', '30');
  await page.click('button:has-text("Suivant")');

  // ── Q6: Central de alarme — Oui (IS in CSV) ──────────────────────────────────
  await page.waitForSelector('text=Precisa de central de alarme?');
  await page.click('button:has-text("Oui")');

  // ── Wait for quote generation (AI call can take up to 60s) ──────────────────
  await page.waitForSelector('[data-testid="quote-items-table"]', { timeout: 90000 });

  const table = page.locator('[data-testid="quote-items-table"]');
  const tableText = await table.textContent() ?? '';
  const tableLower = tableText.toLowerCase();

  // ── Anti-hallucination assertions ────────────────────────────────────────────

  // 1. Camera 4K must NOT be replaced by "Camera IP 4MP" or "Camera IP 8MP"
  expect(tableLower).not.toMatch(/\bcamera ip 4mp\b/);
  expect(tableLower).not.toMatch(/\bcamera ip 8mp\b/);

  // 2. "Embutida no teto" must NOT be replaced by "Instalacao camera interna/externa"
  expect(tableLower).not.toContain('instalacao camera interna');
  expect(tableLower).not.toContain('instalacao camera externa');

  // 3. Rows for absent products must show "A consulter" (subtotal = 0).
  //    The page renders subtotal=0 as "A consulter".
  expect(tableLower).toContain('a consulter');

  // 4. "Camera 4K Ultra HD" row must show "A consulter" (no hallucinated price).
  //    Locate the row that contains "4k" and verify the price cell says "A consulter".
  const cameraRow = page.locator('[data-testid="quote-items-table"] tbody tr')
    .filter({ hasText: /4k/i });
  const cameraPriceCell = cameraRow.locator('td').last();
  await expect(cameraPriceCell).toContainText('A consulter', { ignoreCase: true });

  // 4. "Central de alarme" (present in CSV at $650) must appear with a real price,
  //    meaning the quote contains some formatted dollar amount (e.g. "$650").
  //    We verify the total is > $0 which confirms at least one priced item exists.
  const totalEl = page.locator('text=Total').last();
  const totalText = await totalEl.evaluate(el => el.parentElement?.textContent ?? '');
  // Total should contain a non-zero currency value (fr-CA format: "2 793,89 $")
  expect(totalText).toMatch(/[\d\s]+[,.]\d{2}\s*\$/);
  // Extract digits only and verify it's non-trivially non-zero
  const numericTotal = parseFloat(totalText.replace(/[^\d,]/g, '').replace(',', '.'));
  expect(numericTotal).toBeGreaterThan(0);

  console.log('✓ Quote table text:\n', tableText);
  console.log('✓ Total line text:', totalText);
});
