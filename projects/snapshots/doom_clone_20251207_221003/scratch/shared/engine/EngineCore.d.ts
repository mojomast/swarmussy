export declare class EngineCore {
  constructor(options?: { apiBaseUrl?: string; httpClient?: any; eventBus?: any });
  initContract(): Promise<any>;
  createProfile(data: any): Promise<any>;
  readProfile(id: string): Promise<any>;
  updateProfile(id: string, updates: any): Promise<any>;
  deleteProfile(id: string): Promise<any>;
  bootstrapFromEvent(profile: any): void;
}
