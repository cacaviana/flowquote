export type ModelOption = { id: string; label: string };
export type AvailableModels = Record<string, ModelOption[]>;

export class AiSettingsResponse {
  readonly provider: string;
  readonly model: string;
  readonly available_models: AvailableModels;

  constructor(raw: Record<string, unknown>) {
    this.provider = String(raw.provider ?? '');
    this.model = String(raw.model ?? '');
    this.available_models = (raw.available_models ?? {}) as AvailableModels;
  }

  getModelsForProvider(provider: string): ModelOption[] {
    return this.available_models[provider] ?? [];
  }

  getProviders(): string[] {
    return Object.keys(this.available_models);
  }
}
