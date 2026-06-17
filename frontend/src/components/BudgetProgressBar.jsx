export default function BudgetProgressBar({ progress }) {
  const pct = Math.min(progress * 100, 100);
  const colorCls =
    progress >= 1.0 ? 'bg-red-500' :
    progress >= 0.7 ? 'bg-yellow-400' :
    'bg-emerald-500';

  return (
    <div className="w-full bg-gray-200 rounded-full h-2.5 overflow-hidden">
      <div
        className={`h-2.5 rounded-full transition-all ${colorCls}`}
        style={{ width: `${pct}%` }}
      />
    </div>
  );
}
