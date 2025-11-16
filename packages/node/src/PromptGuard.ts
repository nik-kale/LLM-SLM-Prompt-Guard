import * as fs from "fs";
import * as path from "path";
import * as yaml from "js-yaml";
import {
  Detector,
  DetectorResult,
  Mapping,
  AnonymizeResult,
  Policy,
  PromptGuardConfig,
} from "./types";
import { RegexDetector } from "./RegexDetector";

/**
 * Core class for PII anonymization & de-anonymization in Node/TypeScript.
 *
 * @example
 * ```typescript
 * const guard = new PromptGuard({
 *   detectors: ["regex"],
 *   policy: "default_pii"
 * });
 *
 * const text = "Hi, I'm John Smith. My email is john@example.com.";
 * const { anonymized, mapping } = guard.anonymize(text);
 * console.log(anonymized);
 * // Output: "Hi, I'm [NAME_1]. My email is [EMAIL_1]."
 *
 * // After getting LLM/SLM response...
 * const final = guard.deanonymize(llmResponse, mapping);
 * ```
 */
export class PromptGuard {
  private detectors: Detector[];
  private policy: Policy;

  constructor(config: PromptGuardConfig = {}) {
    const {
      detectors = ["regex"],
      policy = "default_pii",
      customPolicyPath,
    } = config;

    this.detectors = this.initDetectors(detectors);
    this.policy = this.loadPolicy(policy, customPolicyPath);
  }

  private initDetectors(names: string[]): Detector[] {
    const instances: Detector[] = [];
    for (const name of names) {
      if (name === "regex") {
        instances.push(new RegexDetector());
      } else {
        throw new Error(
          `Unknown detector backend: ${name}. Currently supported: ['regex']`
        );
      }
    }
    return instances;
  }

  private loadPolicy(policyName: string, customPath?: string): Policy {
    let policyPath: string;

    if (customPath) {
      policyPath = customPath;
    } else {
      // Load from built-in policies
      policyPath = path.join(__dirname, "..", "policies", `${policyName}.yaml`);
    }

    if (!fs.existsSync(policyPath)) {
      throw new Error(`Policy file not found: ${policyPath}`);
    }

    const content = fs.readFileSync(policyPath, "utf-8");
    return yaml.load(content) as Policy;
  }

  /**
   * Anonymize PII in the given text.
   *
   * @param text - The text to anonymize
   * @returns An object containing the anonymized text and mapping
   */
  anonymize(text: string): AnonymizeResult {
    const allResults: DetectorResult[] = [];
    for (const detector of this.detectors) {
      allResults.push(...detector.detect(text));
    }

    // Sort by start index for stable replacements
    allResults.sort((a, b) => a.start - b.start);

    const policyEntities = this.policy.entities || {};
    const mapping: Mapping = {};
    const anonymized: string[] = [];
    let lastIdx = 0;

    // Counter per entity type
    const counters: Record<string, number> = {};

    for (const res of allResults) {
      const entityCfg = policyEntities[res.entityType];
      if (!entityCfg) {
        continue; // skip unconfigured entity types
      }

      // Add text before this entity
      anonymized.push(text.substring(lastIdx, res.start));

      // Compute placeholder
      counters[res.entityType] = (counters[res.entityType] || 0) + 1;
      const i = counters[res.entityType];
      const placeholderTpl = entityCfg.placeholder || `[${res.entityType}_{i}]`;
      const placeholder = placeholderTpl.replace("{i}", i.toString());

      anonymized.push(placeholder);
      mapping[placeholder] = res.text;

      lastIdx = res.end;
    }

    // Add trailing text
    anonymized.push(text.substring(lastIdx));

    return {
      anonymized: anonymized.join(""),
      mapping,
    };
  }

  /**
   * Replace placeholders in text with original values from mapping.
   *
   * @param text - Text containing placeholders
   * @param mapping - Dictionary mapping placeholders to original values
   * @returns Text with placeholders replaced by original values
   */
  deanonymize(text: string, mapping: Mapping): string {
    let result = text;
    for (const [placeholder, original] of Object.entries(mapping)) {
      result = result.replace(new RegExp(this.escapeRegex(placeholder), "g"), original);
    }
    return result;
  }

  private escapeRegex(str: string): string {
    return str.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  }
}

/**
 * Factory function to create a PromptGuard instance.
 *
 * @param config - Configuration options
 * @returns A new PromptGuard instance
 */
export function createPromptGuard(config?: PromptGuardConfig): PromptGuard {
  return new PromptGuard(config);
}
