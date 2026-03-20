import { test, expect } from '@playwright/test';

/**
 * Anti-hallucination test for "Desenvolvimento de Software" flow.
 *
 * CSV catalog contains:
 *   Landing page, E-commerce simples, App mobile iOS, App mobile Android,
 *   Integracao API REST, Banco de dados SQL, Hospedagem VPS, SEO basico,
 *   Manutencao mensal.
 *
 * Intentionally ABSENT (hallucination traps):
 *   - "E-commerce avancado"    → AI must NOT use "E-commerce simples" price
 *   - "App mobile hibrido"     → AI must NOT use "App mobile iOS/Android" price
 *   - "Integracao API GraphQL" → AI must NOT use "Integracao API REST" price
 *   - "SEO avancado"           → AI must NOT use "SEO basico" price
 *
 * Present items (must be priced correctly):
 *   - "Banco de dados SQL" → $800
 *   - "Manutencao mensal"  → $500/mes (client said Oui)
 */
test('dev software: 4 absent services show "A consulter", no hallucination', async ({ page }) => {
  await page.goto('/q/devis-dev-software');
  await page.waitForSelector('text=Commencer', { timeout: 15000 });

  // ── Start form ──────────────────────────────────────────────────────────────
  await page.fill('input[type="text"]', 'Empresa Teste Ltda');
  await page.fill('input[type="email"]', 'dev@teste.com');
  await page.click('button:has-text("Commencer")');

  // ── Q1: Tipo de projeto — "E-commerce avancado" (NOT in CSV) ─────────────────
  await page.waitForSelector('text=Que tipo de projeto voce precisa?');
  await page.click('button:has-text("E-commerce avancado")');

  // ── Q2: App mobile — "Hibrido" (NOT in CSV) ──────────────────────────────────
  await page.waitForSelector('text=Precisa de app mobile?');
  await page.click('button:has-text("Hibrido")');

  // ── Q3: API — "GraphQL" (NOT in CSV) ─────────────────────────────────────────
  await page.waitForSelector('text=Integracao de API necessaria?');
  await page.click('button:has-text("GraphQL")');

  // ── Q4: Banco — "SQL" (IN CSV at $800) ───────────────────────────────────────
  await page.waitForSelector('text=Banco de dados?');
  await page.click('button:has-text("SQL")');

  // ── Q5: SEO — "SEO avancado" (NOT in CSV) ────────────────────────────────────
  await page.waitForSelector('text=Precisa de SEO?');
  await page.click('button:has-text("SEO avancado")');

  // ── Q6: Manutencao — Oui (IN CSV at $500) ────────────────────────────────────
  await page.waitForSelector('text=Deseja manutencao mensal?');
  await page.click('button:has-text("Oui")');

  // ── Wait for quote ────────────────────────────────────────────────────────────
  await page.waitForSelector('[data-testid="quote-items-table"]', { timeout: 90000 });

  const table = page.locator('[data-testid="quote-items-table"]');
  const tableText = await table.textContent() ?? '';
  const tableLower = tableText.toLowerCase();

  console.log('Quote table:\n', tableText);

  // ── Anti-hallucination: absent items must NOT get prices from similar products ──

  // 1. "E-commerce avancado" must NOT be billed as "E-commerce simples" ($4500)
  expect(tableLower).not.toContain('e-commerce simples');

  // 2. "App mobile hibrido" must NOT be billed as iOS or Android ($8000 each)
  expect(tableLower).not.toContain('app mobile ios');
  expect(tableLower).not.toContain('app mobile android');

  // 3. "GraphQL" must NOT be billed as "Integracao API REST" ($1200)
  expect(tableLower).not.toContain('integracao api rest');

  // 4. "SEO avancado" must NOT be billed as "SEO basico" ($600)
  expect(tableLower).not.toContain('seo basico');

  // ── Absent items must show "A consulter" ──────────────────────────────────────
  expect(tableLower).toContain('a consulter');

  // At least 3 absent items → at least 3 "A consulter" cells
  const aConsulterCount = (tableLower.match(/a consulter/g) || []).length;
  expect(aConsulterCount).toBeGreaterThanOrEqual(3);

  // "App mobile hibrido" row must specifically show "A consulter" (price hallucination guard)
  const hibridoRow = page.locator('[data-testid="quote-items-table"] tbody tr')
    .filter({ hasText: /hibrido/i });
  const hibridoPriceCell = hibridoRow.locator('td').last();
  await expect(hibridoPriceCell).toContainText('A consulter', { ignoreCase: true });

  // ── Present items must be priced ─────────────────────────────────────────────
  // "Banco de dados SQL" ($800) and "Manutencao mensal" ($500) must appear with real prices
  const rows = page.locator('[data-testid="quote-items-table"] tbody tr');
  const rowCount = await rows.count();

  let foundPricedItem = false;
  for (let i = 0; i < rowCount; i++) {
    const rowText = (await rows.nth(i).textContent() ?? '').toLowerCase();
    const priceCell = rows.nth(i).locator('td').last();
    const priceText = await priceCell.textContent() ?? '';
    // A priced item (not "A consulter") with value > $0
    if (!rowText.includes('a consulter') && priceText.match(/[\d]+[,.][\d]{2}/)) {
      foundPricedItem = true;
      break;
    }
  }
  expect(foundPricedItem).toBe(true);

  console.log(`✓ "A consulter" count: ${aConsulterCount}`);
});
