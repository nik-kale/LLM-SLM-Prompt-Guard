import { Detector, DetectorResult } from "./types";

const EMAIL_RE = /[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}/g;
const PHONE_RE = /\+?\d[\d\-\s]{7,}\d/g;
const NAME_RE = /\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b/g;
const IP_RE = /\b(?:\d{1,3}\.){3}\d{1,3}\b/g;
const CC_RE = /\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b/g;
const SSN_RE = /\b\d{3}-\d{2}-\d{4}\b/g;

/**
 * Simple regex-based PII detector for Node/TypeScript.
 *
 * Detects:
 * - EMAIL: Email addresses
 * - PHONE: Phone numbers
 * - PERSON: Names (simple capitalized word patterns)
 * - IP_ADDRESS: IPv4 addresses
 * - CREDIT_CARD: Credit card numbers
 * - SSN: Social Security Numbers
 */
export class RegexDetector implements Detector {
  detect(text: string): DetectorResult[] {
    const results: DetectorResult[] = [];

    // Helper function to find all matches
    const findMatches = (regex: RegExp, entityType: string) => {
      // Reset regex lastIndex
      regex.lastIndex = 0;
      let match: RegExpExecArray | null;
      while ((match = regex.exec(text)) !== null) {
        results.push({
          entityType,
          start: match.index,
          end: match.index + match[0].length,
          text: match[0],
        });
      }
    };

    findMatches(EMAIL_RE, "EMAIL");
    findMatches(PHONE_RE, "PHONE");
    findMatches(NAME_RE, "PERSON");
    findMatches(IP_RE, "IP_ADDRESS");
    findMatches(CC_RE, "CREDIT_CARD");
    findMatches(SSN_RE, "SSN");

    return results;
  }
}
