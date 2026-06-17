import BudgetProgressBar from './BudgetProgressBar';
import { useCurrency } from '../hooks/useCurrency';

export default function BudgetCard({ budget }) {
  const fmt = useCurrency();
  const { category, planned_amount, spent, remaining, progress } = budget;
  const overBudget = progress >= 1.0;

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-4">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium text-gray-800">
          {category?.icon} {category?.name}
        </span>
        <span className={`text-xs font-semibold ${overBudget ? 'text-red-600' : 'text-gray-500'}`}>
          {Math.round(progress * 100)}%
        </span>
      </div>

      <BudgetProgressBar progress={progress} />

      <div className="flex justify-between mt-2 text-xs text-gray-500">
        <span>Витрачено: <strong>{fmt(spent)}</strong></span>
        <span>Ліміт: {fmt(planned_amount)}</span>
      </div>

      {overBudget && (
        <p className="text-xs text-red-500 mt-1">
          Перевищено на {fmt(Math.abs(remaining))}
        </p>
      )}
    </div>
  );
}
