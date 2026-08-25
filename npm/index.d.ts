/**
 * TypeScript definitions for termux-bitnet Node.js Gateway.
 */

export interface BitNetOptions {
  modelPath?: string;
  systemPrompt?: string;
  stopTokens?: string;
  threads?: number;
  contextSize?: number;
  batchSize?: number;
  ubatchSize?: number;
  temperature?: number;
  topP?: number;
  topK?: number;
  minP?: number;
  typicalP?: number;
  repeatPenalty?: number;
  repeatLastN?: number;
  freqPenalty?: number;
  presencePenalty?: number;
  seed?: number;
  flashAttn?: boolean;
  gpuLayers?: number;
  verbose?: boolean;
}

export interface GenerationMetrics {
  promptTokens: number;
  generatedTokens: number;
  tokensPerSecond: number;
  totalTimeMs: number;
}

export interface HardwareInfo {
  arch: string;
  hasNeon: boolean;
  hasDotProd: boolean;
  cpuCores: number;
}

export declare class BitNetEngine {
  constructor(options?: BitNetOptions);
  generate(prompt: string, maxTokens?: number): Promise<string>;
  generateStream(prompt: string, maxTokens?: number, onToken?: (token: string) => void): Promise<string>;
  getHardwareInfo(): HardwareInfo;
  close(): void;
}

export declare function createEngine(options?: BitNetOptions): BitNetEngine;
export declare function detectHardware(): HardwareInfo;
