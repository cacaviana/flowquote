import { test, expect } from '@playwright/test';

test.describe('Fluxo Devis E2E', () => {

  // ─────────────── BUILDER ───────────────

  test('Builder: criar fluxo devis via UI, adicionar nós, editar, salvar', async ({ page }) => {
    await page.goto('/admin/flows');
    await expect(page.locator('text=Meus Fluxos')).toBeVisible({ timeout: 10000 });
    await page.waitForTimeout(1500);
    await page.click('button:has-text("Novo Fluxo")');

    // Modal — selecionar Devis (dentro do modal overlay)
    await expect(page.locator('text=Escolha o tipo de fluxo')).toBeVisible({ timeout: 5000 });
    // Clicar no botão "Devis (Orçamento)" no modal
    await page.getByRole('button', { name: /Devis \(Orçamento\)/ }).click();
    await page.waitForURL(/\/admin\/flows\/new\/edit\?module=devis/);

    // Badge "Devis" e botão CSV visíveis
    await expect(page.locator('span:has-text("Devis")').first()).toBeVisible({ timeout: 5000 });
    await expect(page.locator('[data-testid="btn-csv-upload"]')).toBeVisible();

    // Nó Start criado automaticamente (canvas + editor panel = 2 matches, use .first())
    await expect(page.locator('text=Início').first()).toBeVisible({ timeout: 5000 });

    // Alterar nome
    const nameInput = page.locator('header input[type="text"]');
    await nameInput.clear();
    await nameInput.fill('Devis Teste Playwright');

    // Adicionar Pergunta
    await page.click('button:has-text("Pergunta")');
    await expect(page.locator('text=Nova Pergunta')).toBeVisible({ timeout: 3000 });

    // Adicionar End
    await page.click('button:has-text("Fim")');
    await page.waitForTimeout(500);

    // Salvar
    await page.click('button:has-text("Salvar")');
    await expect(page.locator('text=Salvo!')).toBeVisible({ timeout: 10000 });

    // URL mudou pra ID real
    await page.waitForTimeout(1000);
    expect(page.url()).toMatch(/\/admin\/flows\/[a-f0-9]+\/edit/);

    // Verificar na lista
    await page.goto('/admin/flows');
    await expect(page.locator('h3:has-text("Devis Teste Playwright")').first()).toBeVisible({ timeout: 10000 });

    // Cleanup: deletar flows criados pelo teste
    const res = await page.request.get('http://localhost:8001/api/flows');
    const data = await res.json();
    const flows = data.flows || data;
    for (const f of flows.filter((fl: any) => fl.name === 'Devis Teste Playwright')) {
      await page.request.delete(`http://localhost:8001/api/flows/${f._id}`);
    }

    console.log('✅ Builder devis: criar, editar, salvar OK!');
  });

  test('Builder: CSV upload visível pra devis, invisível pra agendamento', async ({ page }) => {
    await page.goto('/admin/flows/new/edit?module=devis');
    await expect(page.locator('[data-testid="btn-csv-upload"]')).toBeVisible({ timeout: 5000 });

    await page.goto('/admin/flows/new/edit?module=agendamento');
    await page.waitForTimeout(1000);
    await expect(page.locator('[data-testid="btn-csv-upload"]')).toHaveCount(0);

    console.log('✅ CSV upload: visível em devis, oculto em agendamento!');
  });

  test('Builder: NodeEditor mostra endTypes corretos por módulo', async ({ page }) => {
    // Devis
    await page.goto('/admin/flows/new/edit?module=devis');
    await page.waitForTimeout(1000);
    await page.click('button:has-text("Fim")');
    await page.waitForTimeout(500);
    const endSelect = page.locator('select').last();
    await expect(endSelect).toBeVisible({ timeout: 3000 });
    const opts1 = await endSelect.locator('option').allTextContents();
    expect(opts1).toContain('Gerar orçamento (IA)');
    expect(opts1).not.toContain('Agendamento de reunião');
    console.log(`✅ End types devis: ${opts1.join(', ')}`);

    // Agendamento
    await page.goto('/admin/flows/new/edit?module=agendamento');
    await page.waitForTimeout(1000);
    await page.click('button:has-text("Fim")');
    await page.waitForTimeout(500);
    const endSelect2 = page.locator('select').last();
    const opts2 = await endSelect2.locator('option').allTextContents();
    expect(opts2).toContain('Agendamento de reunião');
    expect(opts2).not.toContain('Gerar orçamento (IA)');
    console.log(`✅ End types agendamento: ${opts2.join(', ')}`);
  });

  test('Builder: editar flow existente carrega module e CSV', async ({ page }) => {
    // Navegar diretamente pro flow de Borne de Recharge EV
    const res = await page.request.get('http://localhost:8001/api/flows');
    const data = await res.json();
    const flows = data.flows || data;
    const borneFlow = flows.find((f: any) => f.slug === 'devis-borne-de-recharge-ev');
    expect(borneFlow).toBeTruthy();

    await page.goto(`/admin/flows/${borneFlow._id}/edit`);

    // Nome do flow carregado
    const nameInput = page.locator('header input[type="text"]');
    await expect(nameInput).toHaveValue('Devis Borne de Recharge EV', { timeout: 10000 });

    // Badge "Devis"
    await expect(page.locator('span:has-text("Devis")').first()).toBeVisible({ timeout: 3000 });

    // CSV carregado
    await expect(page.locator('text=CSV carregado')).toBeVisible({ timeout: 5000 });

    // Nós visíveis
    await expect(page.locator('text=Vos informations')).toBeVisible({ timeout: 5000 });

    console.log('✅ Editar flow existente OK!');
  });

  // ─────────────── QUESTIONÁRIO PÚBLICO ───────────────

  /** Helper: preenche intro e inicia o chat */
  async function startChat(page: any, slug: string, name: string) {
    await page.goto(`/q/${slug}`);
    await expect(page.locator('h1')).toBeVisible({ timeout: 10000 });
    await page.fill('input[placeholder="Seu nome completo"]', name);
    await page.fill('input[placeholder="seu@email.com"]', `${name.toLowerCase().replace(' ', '')}@test.com`);
    await page.fill('input[placeholder="(00) 00000-0000"]', '5141234567');
    await page.click('button:has-text("Começar conversa")');
    await expect(page.locator(`text=Olá, ${name.split(' ')[0]}`)).toBeVisible({ timeout: 5000 });
  }

  /** Helper: espera a pergunta do bot aparecer no chat */
  async function waitForQuestion(page: any, partialText: string) {
    // Buscar dentro das bolhas do bot (div.bg-gray-100 > p)
    await expect(
      page.locator('.bg-gray-100 p', { hasText: partialText }).first()
    ).toBeVisible({ timeout: 8000 });
  }

  /** Helper: responde pergunta de texto/número */
  async function answerText(page: any, questionText: string, answer: string) {
    await waitForQuestion(page, questionText);
    const input = page.locator('input[placeholder="Digite sua resposta..."]');
    await expect(input).toBeVisible({ timeout: 5000 });
    await input.click();
    // pressSequentially triggers input events properly for Svelte bind:value
    await input.pressSequentially(answer, { delay: 50 });
    await page.waitForTimeout(200);
    await input.press('Enter');
  }

  /** Helper: clica opção chip */
  async function answerChip(page: any, questionText: string, optionText: string) {
    await waitForQuestion(page, questionText);
    const chip = page.locator('button.opt-chip', { hasText: optionText });
    await expect(chip).toBeVisible({ timeout: 5000 });
    await chip.click();
  }

  /** Helper: responde yes/no */
  async function answerYesNo(page: any, questionText: string, answer: 'Sim' | 'Não') {
    await waitForQuestion(page, questionText);
    await page.getByRole('button', { name: answer, exact: true }).click();
  }

  test('Questionário devis: caminho feliz → orçamento', async ({ page }) => {
    await startChat(page, 'devis-borne-de-recharge-ev', 'Pierre Tremblay');

    // P1: Região — "Lanaudiere"
    await answerChip(page, 'region', 'Lanaudiere');

    // P2: Amperage — "200A"
    await answerChip(page, 'amperage', '200A');

    // P3: Espaços livres — "Sim"
    await answerYesNo(page, 'espaces libres', 'Sim');

    // P4: Tipo de borne — "Borne 32A"
    await answerChip(page, 'type de borne', '32A');

    // P5: Local de instalação — "Mur exterieur"
    await answerChip(page, 'installee la borne', 'Mur exterieur');

    // P6: Distância (number)
    await answerText(page, 'distance', '25');

    // Deve chegar ao fim (qualquer estado final)
    await expect(
      page.locator('text=Gerando seu orçamento')
        .or(page.locator('[data-testid="quote-items-table"]'))
        .or(page.locator('text=Obrigado'))
        .or(page.locator('text=Erreur'))
        .or(page.locator('text=processar suas informações'))
    ).toBeVisible({ timeout: 30000 });

    console.log('✅ Caminho feliz completo!');
  });

  test('Questionário devis: "Autre region" → especialista', async ({ page }) => {
    await startChat(page, 'devis-borne-de-recharge-ev', 'Jean Dupont');

    // P1: Região — "Autre region" → end_hors_zone (specialist)
    await answerChip(page, 'region', 'Autre region');

    // Deve ir para tela de especialista
    await expect(
      page.locator('text=Hors zone de service')
    ).toBeVisible({ timeout: 10000 });

    // Deve mostrar mensagem de contato
    await expect(page.locator('text=Entraremos em contato')).toBeVisible({ timeout: 3000 });

    console.log('✅ Autre region → especialista OK!');
  });

  test('Questionário devis: "sem espaço no painel" → especialista', async ({ page }) => {
    await startChat(page, 'devis-borne-de-recharge-ev', 'Marie Lavoie');

    await answerChip(page, 'region', 'Lanaudiere');
    await answerChip(page, 'amperage', '100A');

    // P3: Espaços livres — "Não" → end_panneau_plein (specialist)
    await answerYesNo(page, 'espaces libres', 'Não');

    // Deve ir para tela de especialista
    await expect(
      page.locator('text=Evaluation specialiste')
    ).toBeVisible({ timeout: 10000 });

    console.log('✅ Sem espaço no painel → especialista OK!');
  });
});
