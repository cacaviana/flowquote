export class UpdateAiSettingsRequest {
  readonly provider: string;
  readonly model: string;

  constructor(data: { provider: string; model: string }) {
    this.provider = data.provider;
    this.model = data.model;
  }

  isValid(): boolean {
    return this.provider.trim() !== '' && this.model.trim() !== '';
  }

  toPayload(): Record<string, string> {
    return { provider: this.provider, model: this.model };
  }
}
