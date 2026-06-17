import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import BudgetProgressBar from '../components/BudgetProgressBar';

function getBar(container) {
  return container.querySelector('.h-2\\.5.rounded-full.transition-all');
}

describe('BudgetProgressBar', () => {
  it('renders without crashing', () => {
    const { container } = render(<BudgetProgressBar progress={0.5} />);
    expect(container.firstChild).toBeTruthy();
  });

  it('uses green color when progress < 70%', () => {
    const { container } = render(<BudgetProgressBar progress={0.5} />);
    expect(getBar(container).className).toContain('bg-emerald-500');
  });

  it('uses yellow color when progress is between 70% and 100%', () => {
    const { container } = render(<BudgetProgressBar progress={0.85} />);
    expect(getBar(container).className).toContain('bg-yellow-400');
  });

  it('uses red color when progress >= 100%', () => {
    const { container } = render(<BudgetProgressBar progress={1.0} />);
    expect(getBar(container).className).toContain('bg-red-500');
  });

  it('caps width at 100% when progress > 1', () => {
    const { container } = render(<BudgetProgressBar progress={1.5} />);
    expect(getBar(container).style.width).toBe('100%');
  });

  it('sets width proportionally', () => {
    const { container } = render(<BudgetProgressBar progress={0.4} />);
    expect(getBar(container).style.width).toBe('40%');
  });
});
