import { test, expect } from '@playwright/test';

const QUESTION_IMG = 'https://picsum.photos/seed/teste-question/400/300';

test.describe('Question with image at question level — feature E2E', () => {
  let createdFlowId: string;
  let createdSlug: string;

  test.afterAll(async ({ request }) => {
    if (createdFlowId) {
      await request.delete(`/api/flows/${createdFlowId}`);
    }
  });

  test('1. POST /api/flows persists imageUrl at question level', async ({ request }) => {
    const body = {
      name: 'TEST Image Feature',
      status: 'published',
      flow_type: 'quote',
      nodes: [
        {
          id: 'start-1',
          type: 'start',
          position: { x: 0, y: 0 },
          data: { title: 'Début', collectFields: ['name', 'email'] }
        },
        {
          id: 'q1',
          type: 'question',
          position: { x: 0, y: 200 },
          data: {
            title: 'Quel type de borne ?',
            questionType: 'single_choice',
            imageUrl: QUESTION_IMG,
            options: [
              { id: 'opt_a', label: 'Borne A 240V', value: 'a' },
              { id: 'opt_b', label: 'Borne B 120V', value: 'b' }
            ],
            required: true
          }
        },
        {
          id: 'end-1',
          type: 'end',
          position: { x: 0, y: 400 },
          data: { title: 'Fin', endType: 'thank_you', message: 'Merci' }
        }
      ],
      edges: [
        { id: 'e1', source: 'start-1', target: 'q1' },
        { id: 'e2', source: 'q1', sourceHandle: 'opt_a', target: 'end-1' },
        { id: 'e3', source: 'q1', sourceHandle: 'opt_b', target: 'end-1' }
      ]
    };

    const res = await request.post('/api/flows', { data: body });
    expect(res.status()).toBe(201);
    const created = await res.json();
    expect(created._id).toBeTruthy();
    expect(created.slug).toBeTruthy();
    createdFlowId = created._id;
    createdSlug = created.slug;
  });

  test('2. GET /api/flows/:id round-trips imageUrl at question level', async ({ request }) => {
    expect(createdFlowId).toBeTruthy();
    const res = await request.get(`/api/flows/${createdFlowId}`);
    expect(res.ok()).toBeTruthy();
    const flow = await res.json();

    const q = flow.nodes.find((n: any) => n.id === 'q1');
    expect(q).toBeTruthy();
    expect(q.data.imageUrl).toBe(QUESTION_IMG);
  });

  test('3. Runtime /q/:slug renders question image and plain option buttons', async ({ page }) => {
    expect(createdSlug).toBeTruthy();

    await page.goto(`/q/${createdSlug}`);

    // Fill the start form
    await page.fill('input[type="text"]', 'Test User');
    await page.fill('input[type="email"]', 'test@itvalley.test');
    await page.getByRole('button', { name: /commencer|start|começar/i }).click();

    // The question should now be visible. Verify the question-level image.
    const questionImg = page.locator(`img[src="${QUESTION_IMG}"]`);
    await expect(questionImg).toBeVisible({ timeout: 10000 });

    // Verify both option labels are visible (plain buttons, no per-option image)
    await expect(page.getByText('Borne A 240V')).toBeVisible();
    await expect(page.getByText('Borne B 120V')).toBeVisible();
  });
});
