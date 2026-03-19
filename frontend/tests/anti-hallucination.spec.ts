import { test, expect } from '@playwright/test';

/**
 * Testa que a IA NÃO alucina um produto similar quando o cliente
 * seleciona uma opção que não existe no CSV.
 *
 * Cenário: CSV tem "Installation murale exterieure" mas NÃO tem
 * "Installation interieure". Cliente escolhe "Interieur (garage ferme)".
 * Esperado: item aparece como "(prix à consulter)", NÃO como "murale extérieure".
 */

// CSV sem opção de instalação interior
const CSV_WITHOUT_INTERIOR = `produto,preco,unidade,categoria
Borne 16A Level 1,499,unidade,borne
Borne 32A Level 2,699,unidade,borne
Borne 48A Level 2,899,unidade,borne
Installation murale exterieure,490,unidade,installation
Installation sur poteau,690,unidade,installation
Cablage par pied,9,pied,cablage
Deplacement,69,unidade,deplacement`;

async function getMainFlow(request: any) {
  const listRes = await request.get('/api/flows');
  const flows = await listRes.json();
  for (const f of flows) {
    const fullRes = await request.get(`/api/flows/${f._id}`);
    const full = await fullRes.json();
    if (full.nodes && full.nodes.length > 3) return full;
  }
  return null;
}

test.describe('Anti-alucinação: interior não vira exterior', () => {

  test('setup: faz upload do CSV sem opção interior', async ({ request }) => {
    const flow = await getMainFlow(request);
    expect(flow).toBeTruthy();

    const res = await request.put(`/api/flows/${flow._id}`, {
      data: { ...flow, pricing_csv: CSV_WITHOUT_INTERIOR }
    });
    expect(res.ok()).toBeTruthy();

    const updated = await (await request.get(`/api/flows/${flow._id}`)).json();
    expect(updated.pricing_csv).toContain('Installation murale exterieure');
    // Garante que interior NÃO está no CSV
    expect(updated.pricing_csv ?? '').not.toContain('interieur');
  });

  test('cliente escolhe interior → quote não pode ter "exterieure"', async ({ page, request }) => {
    const flow = await getMainFlow(request);
    expect(flow).toBeTruthy();

    await page.goto(`/q/${flow.slug}`);
    await expect(page.locator('text=Commencer')).toBeVisible({ timeout: 10000 });

    // Preenche dados do cliente
    await page.locator('input').first().fill('Carlos Teste');
    await page.locator('input[type="email"]').fill('carlos@test.com');
    const telInput = page.locator('input[type="tel"]');
    if (await telInput.isVisible().catch(() => false)) {
      await telInput.fill('+1 450-555-1234');
    }
    const textInputs = page.locator('input[type="text"]');
    if (await textInputs.count() > 1) {
      await textInputs.last().fill('123 Rue Test, Laval QC');
    }
    await page.locator('text=Commencer').click();

    // Navega pelas perguntas com opções específicas
    const answerMap: Record<string, string> = {
      'region':      'Laval',        // Lanaudiere / Est de Montreal / Laval / Autre
      'panneau':     '200A',
      'espace':      '', // pega o primeiro disponível
      'type_borne':  '32A',          // Borne 32A
      'installation': 'Interieur',   // <-- opção que NÃO existe no CSV
      'distance':    '30',
    };

    let safetyCounter = 0;
    while (safetyCounter < 25) {
      safetyCounter++;
      await page.waitForTimeout(600);

      // Fim: spinner ou tabela de orçamento
      const spinnerVisible = await page.locator('.animate-spin').isVisible().catch(() => false);
      const tableVisible = await page.locator('[data-testid="quote-items-table"]').isVisible().catch(() => false);
      const preVisible = await page.locator('pre').isVisible().catch(() => false);
      if (spinnerVisible || tableVisible || preVisible) break;

      // Input numérico → distância
      const numberInput = page.locator('input[type="number"]');
      if (await numberInput.isVisible().catch(() => false)) {
        await numberInput.fill('30');
        await page.locator('button:has-text("Suivant")').click();
        continue;
      }

      // Tenta clicar em botão preferido pelo mapa de respostas
      const buttons = page.locator('button').filter({ hasNotText: /Retour|Commencer|Suivant/ });
      const btnCount = await buttons.count();
      if (btnCount > 0) {
        let clicked = false;
        for (const [key, label] of Object.entries(answerMap)) {
          if (!label) continue;
          const target = buttons.filter({ hasText: new RegExp(label, 'i') });
          if (await target.count() > 0) {
            await target.first().click();
            clicked = true;
            break;
          }
        }
        if (!clicked) {
          await buttons.first().click();
        }
        continue;
      }

      await page.waitForTimeout(2000);
    }

    // Aguarda tabela de orçamento (IA pode demorar até 90s)
    const quoteTable = page.locator('[data-testid="quote-items-table"]');
    await expect(quoteTable).toBeVisible({ timeout: 90000 });

    // Captura screenshot para inspeção
    await page.screenshot({ path: 'test-results/anti-hallucination.png', fullPage: true });

    // ─── VERIFICAÇÕES CRÍTICAS ────────────────────────────────────────
    const tableText = (await quoteTable.textContent()) ?? '';

    // 1. O item de instalação NÃO pode mostrar "extérieure" quando cliente escolheu interior
    expect(tableText.toLowerCase()).not.toContain('exterieure');
    expect(tableText.toLowerCase()).not.toContain('extérieure');

    // 2. Como "interior" não existe no CSV, deve aparecer como "prix à consulter"
    expect(tableText.toLowerCase()).toMatch(/prix.*(consulter|consult)/i);

    console.log('✅ Anti-alucinação OK: interior não virou exterior');
    console.log('Tabela:', tableText.slice(0, 500));
  });

});
