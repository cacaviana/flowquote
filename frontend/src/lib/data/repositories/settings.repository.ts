import type { AiSettingsResponse } from '$lib/dto/settings/responses';
import type { UpdateAiSettingsRequest } from '$lib/dto/settings/requests';

export class SettingsRepository {
  async getAiConfig(): Promise<Record<string, unknown>> {
    const res = await fetch('/api/settings');
    if (!res.ok) throw new Error('Erro ao buscar configuracoes de IA');
    return res.json();
  }

  async updateAiConfig(dto: UpdateAiSettingsRequest): Promise<Record<string, unknown>> {
    const res = await fetch('/api/settings', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(dto.toPayload())
    });
    if (!res.ok) throw new Error('Erro ao salvar configuracoes de IA');
    return res.json();
  }
}
