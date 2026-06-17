import { describe, it, expect } from 'vitest';
import { formatCurrency } from '../utils/formatCurrency';

describe('formatCurrency', () => {
  it('formats kopecks as UAH', () => {
    const result = formatCurrency(10000);
    expect(result).toContain('100');
    expect(result).toMatch(/₴|UAH|грн/);
  });

  it('handles zero', () => {
    const result = formatCurrency(0);
    expect(result).toContain('0');
  });

  it('handles null/undefined as zero', () => {
    expect(formatCurrency(null)).toContain('0');
    expect(formatCurrency(undefined)).toContain('0');
  });

  it('returns short format for amounts >= 1000 UAH when short=true', () => {
    const result = formatCurrency(1500000, true);
    expect(result).toBe('15.0k ₴');
  });

  it('does NOT shorten amounts < 1000 UAH even with short=true', () => {
    const result = formatCurrency(50000, true);
    expect(result).not.toContain('k');
  });

  it('formats negative amounts correctly', () => {
    const result = formatCurrency(-5000);
    expect(result).toContain('50');
    expect(result).toMatch(/-|мінус/i);
  });
});
