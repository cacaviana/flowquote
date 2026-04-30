import { test, expect } from '@playwright/test';

test.describe.serial('CSV catalog — French display layer', () => {
  let createdFlowId: string;

  test.afterAll(async ({ request }) => {
    if (createdFlowId) await request.delete(`/api/flows/${createdFlowId}`);
  });

  test('1. CSV with PT keys (produto/preco/unidade/categoria) is accepted by parser + persisted', async ({ request }) => {
    const ptCsv = [
      'produto,preco,unidade,categoria',
      'Borne Basic 16A,444,unite,borne',
      'Installation mur exterieur,490,unite,installation',
      'Deplacement,69,unite,deplacement'
    ].join('\n');

    const res = await request.post('/api/flows', {
      data: {
        name: 'TEST CSV FR Display',
        status: 'draft',
        flow_type: 'quote',
        pricing_csv: ptCsv,
        nodes: [
          { id: 'start-1', type: 'start', position: { x: 0, y: 0 },
            data: { title: 'Début', collectFields: ['name', 'email'] } },
          { id: 'end-1', type: 'end', position: { x: 0, y: 200 },
            data: { title: 'Fin', endType: 'thank_you', message: 'Merci' } }
        ],
        edges: [{ id: 'e1', source: 'start-1', target: 'end-1' }]
      }
    });
    expect(res.status()).toBe(201);
    const created = await res.json();
    createdFlowId = created._id;

    // CSV with PT keys is persisted (backend compat preserved)
    const flow = await (await request.get(`/api/flows/${createdFlowId}`)).json();
    expect(flow.pricing_csv).toContain('produto,preco,unidade,categoria');
    expect(flow.pricing_csv).toContain('Borne Basic 16A');
  });

  test('2. Editor page header is rendered in French (no PT remnants)', async ({ page }) => {
    expect(createdFlowId).toBeTruthy();
    await page.goto(`/admin/flows/${createdFlowId}/edit`);

    // Wait for editor to load — flow with pricing_csv shows "CSV chargé" pill
    const csvBtn = page.getByTestId('btn-csv-upload');
    await expect(csvBtn).toContainText('CSV chargé', { timeout: 10000 });

    // Verify other French strings are rendered (these come from various places)
    await expect(page.getByRole('button', { name: 'Enregistrer' })).toBeVisible();
    await expect(page.getByRole('button', { name: /^Preview$/ })).toBeVisible();
    await expect(page.getByText('Ajouter :')).toBeVisible();

    // No PT leakage
    const pageText = await page.locator('body').textContent();
    expect(pageText).not.toContain('CSV carregado');
    expect(pageText).not.toContain('Salvar');
    expect(pageText).not.toContain('Salvando');
    expect(pageText).not.toContain('Preços');
  });

  test('3. CSV modal — open and assert FR layer maps PT keys to FR labels', async ({ page }) => {
    expect(createdFlowId).toBeTruthy();
    await page.goto(`/admin/flows/${createdFlowId}/edit`);

    // Wait for "CSV chargé" pill (proves flow + csv loaded)
    await expect(page.getByTestId('btn-csv-upload')).toContainText('CSV chargé', { timeout: 10000 });

    // Click to open modal
    await page.getByTestId('btn-csv-upload').click();

    // Modal title (h2) should be in FR
    await expect(page.locator('h2:has-text("Catalogue de prix")')).toBeVisible({ timeout: 5000 });

    // Display headers must be the FR mapping (from csvHeaderLabel)
    await expect(page.locator('th').filter({ hasText: /^PRODUIT$/ })).toBeVisible();
    await expect(page.locator('th').filter({ hasText: /^PRIX$/ })).toBeVisible();
    await expect(page.locator('th').filter({ hasText: /^UNITÉ$/ })).toBeVisible();
    await expect(page.locator('th').filter({ hasText: /^CATÉGORIE$/ })).toBeVisible();

    // PT raw header labels must NOT appear
    await expect(page.locator('th').filter({ hasText: /^PRODUTO$/ })).toHaveCount(0);
    await expect(page.locator('th').filter({ hasText: /^PRECO$/ })).toHaveCount(0);

    // FR copy in modal body
    await expect(page.getByText('Aperçu du catalogue', { exact: false })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Télécharger le modèle' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Supprimer le CSV' })).toBeVisible();
  });
});
