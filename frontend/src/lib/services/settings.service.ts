import { SettingsRepository } from '$lib/data/repositories/settings.repository';
import { AiSettingsResponse } from '$lib/dto/settings/responses';
import { UpdateAiSettingsRequest } from '$lib/dto/settings/requests';

export class SettingsService {
  private repo = new SettingsRepository();

  async getAiConfig(): Promise<AiSettingsResponse> {
    const raw = await this.repo.getAiConfig();
    return new AiSettingsResponse(raw);
  }

  async updateAiConfig(provider: string, model: string): Promise<void> {
    const dto = new UpdateAiSettingsRequest({ provider, model });
    if (!dto.isValid()) throw new Error('Dados invalidos');
    await this.repo.updateAiConfig(dto);
  }
}
