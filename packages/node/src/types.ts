/**
 * Represents a detected PII entity in text.
 */
export interface DetectorResult {
  entityType: string;
  start: number;
  end: number;
  text: string;
}

/**
 * Mapping from placeholder to original value.
 */
export type Mapping = Record<string, string>;

/**
 * Result of anonymization operation.
 */
export interface AnonymizeResult {
  anonymized: string;
  mapping: Mapping;
}

/**
 * Policy configuration for PII detection and masking.
 */
export interface Policy {
  name: string;
  description: string;
  entities: Record<string, EntityConfig>;
}

/**
 * Configuration for a specific entity type.
 */
export interface EntityConfig {
  placeholder: string;
}

/**
 * Base interface for PII detectors.
 */
export interface Detector {
  detect(text: string): DetectorResult[];
}

/**
 * Configuration options for PromptGuard.
 */
export interface PromptGuardConfig {
  detectors?: string[];
  policy?: string;
  customPolicyPath?: string;
}
