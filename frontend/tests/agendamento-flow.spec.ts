import { test, expect } from '@playwright/test';

test.describe('Fluxo Agendamento E2E', () => {

  test('Navegar pelo questionário chat de agendamento', async ({ page }) => {
    const slug = 'consultoria-agendamento';

    // 1. Abrir página pública
    await page.goto(`/q/${slug}`);
    await expect(page.locator('text=Consultoria Agendamento')).toBeVisible({ timeout: 10000 });

    // 2. Preencher dados do cliente (placeholders reais)
    await page.fill('input[placeholder="Seu nome completo"]', 'João Teste');
    await page.fill('input[placeholder="seu@email.com"]', 'joao@teste.com');
    await page.fill('input[placeholder="(00) 00000-0000"]', '11999999999');

    // Clicar "Começar conversa →"
    await page.click('button:has-text("Começar conversa")');

    // 3. Boas-vindas no chat
    await expect(page.locator('text=Olá, João')).toBeVisible({ timeout: 5000 });

    // 4. Primeira pergunta: "Qual tipo de consultoria?" (single_choice)
    await expect(page.locator('text=Qual tipo de consultoria')).toBeVisible({ timeout: 8000 });
    const chipFinanceira = page.locator('button', { hasText: 'Financeira' });
    await expect(chipFinanceira).toBeVisible({ timeout: 5000 });
    await chipFinanceira.click();

    // Resposta aparece no chat
    await expect(page.locator('.bg-gray-900:has-text("Financeira")')).toBeVisible({ timeout: 3000 });

    // 5. Segunda pergunta: "Qual a urgência?" (yes_no)
    await expect(page.locator('text=Qual a urgência?')).toBeVisible({ timeout: 8000 });
    const btnSim = page.locator('button', { hasText: 'Sim' });
    await expect(btnSim).toBeVisible({ timeout: 5000 });
    await btnSim.click();

    // 6. Terceira pergunta: "Descreva brevemente..." (text) — input bar
    await expect(page.locator('text=Descreva brevemente')).toBeVisible({ timeout: 8000 });
    const textInput = page.locator('input[placeholder="Digite sua resposta..."]');
    await expect(textInput).toBeVisible({ timeout: 5000 });
    await textInput.fill('Preciso de ajuda com planejamento financeiro');
    await textInput.press('Enter');

    // 7. Fase booking — header "Escolha um horário"
    await expect(page.locator('text=Escolha um horário')).toBeVisible({ timeout: 10000 });

    // Texto "Selecione o dia"
    await expect(page.locator('text=Selecione o dia')).toBeVisible({ timeout: 5000 });

    console.log('✅ Fluxo agendamento completo — chegou na fase de booking!');
  });

  test('Modal de seleção de módulo ao criar novo fluxo', async ({ page }) => {
    await page.goto('/admin/flows');
    await expect(page.locator('text=Meus Fluxos')).toBeVisible({ timeout: 10000 });

    // Esperar cards carregarem (loading: false)
    await page.waitForTimeout(1500);

    // Clicar em "+ Novo Fluxo"
    await page.click('button:has-text("Novo Fluxo")');

    // Modal deve aparecer
    await expect(page.locator('text=Escolha o tipo de fluxo')).toBeVisible({ timeout: 5000 });

    // Duas opções
    const devisBtn = page.locator('button:has-text("Devis")').first();
    const agendBtn = page.locator('button:has-text("Agendamento")').last();
    await expect(devisBtn).toBeVisible({ timeout: 3000 });
    await expect(agendBtn).toBeVisible({ timeout: 3000 });

    // Clicar em Agendamento
    await agendBtn.click();
    await page.waitForURL(/\/admin\/flows\/new\/edit\?module=agendamento/);

    // Não deve mostrar botão de CSV
    await expect(page.locator('[data-testid="btn-csv-upload"]')).toHaveCount(0);

    console.log('✅ Modal de módulo e builder agendamento OK!');
  });

  test('Badges de módulo nos cards de flows', async ({ page }) => {
    await page.goto('/admin/flows');
    await expect(page.locator('text=Meus Fluxos')).toBeVisible({ timeout: 10000 });

    // Esperar cards carregarem
    await page.waitForTimeout(2000);

    // Deve ter badges de módulo (texto "Devis" dentro de um span badge)
    const devisBadge = page.locator('span:has-text("Devis")').first();
    await expect(devisBadge).toBeVisible({ timeout: 5000 });

    console.log('✅ Badge de módulo encontrado!');
  });

  test('Multiple_choice deve exibir opções como chips', async ({ page }) => {
    // Criar flow com multiple_choice via API
    const res = await page.request.post('http://localhost:8001/api/flows', {
      data: {
        name: 'Test MC Flow',
        module: 'agendamento',
        nodes: [
          { id: 's1', type: 'start', position: { x: 0, y: 0 }, data: { title: 'Início', collectFields: ['name', 'email'] } },
          { id: 'q1', type: 'question', position: { x: 0, y: 180 }, data: { title: 'Quais áreas te interessam?', questionType: 'multiple_choice', options: [
            { id: 'o1', label: 'TI', value: 'ti' },
            { id: 'o2', label: 'Marketing', value: 'marketing' },
            { id: 'o3', label: 'RH', value: 'rh' }
          ], required: true } },
          { id: 'e1', type: 'end', position: { x: 0, y: 360 }, data: { title: 'Agendar', endType: 'booking' } }
        ],
        edges: [
          { id: 'e1', source: 's1', target: 'q1' },
          { id: 'e2', source: 'q1', target: 'e1' }
        ]
      }
    });
    const flow = await res.json();
    const flowId = flow._id;

    try {
      await page.goto(`/q/${flow.slug}`);
      await expect(page.locator(`text=${flow.name}`)).toBeVisible({ timeout: 10000 });

      // Preencher intro
      await page.fill('input[placeholder="Seu nome completo"]', 'Maria Teste');
      await page.fill('input[placeholder="seu@email.com"]', 'maria@teste.com');
      await page.click('button:has-text("Começar conversa")');

      // Boas-vindas
      await expect(page.locator('text=Olá, Maria')).toBeVisible({ timeout: 5000 });

      // Pergunta multiple_choice — DEVE ter chips
      await expect(page.locator('text=Quais áreas te interessam?')).toBeVisible({ timeout: 8000 });
      const chipTI = page.getByRole('button', { name: 'TI', exact: true });
      const chipMarketing = page.getByRole('button', { name: 'Marketing', exact: true });
      await expect(chipTI).toBeVisible({ timeout: 8000 });
      await expect(chipMarketing).toBeVisible();

      // Clicar em TI — deve avançar para booking
      await chipTI.click();
      await expect(page.locator('text=Escolha um horário')).toBeVisible({ timeout: 10000 });

      console.log('✅ Multiple choice com chips funciona!');
    } finally {
      // Cleanup
      await page.request.delete(`http://localhost:8001/api/flows/${flowId}`);
    }
  });
});
