import { useCurrency } from '../../hooks/useCurrency';

const DAYS = ['Нд', 'Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб'];

export default function SpendingHeatmap({ data = [] }) {
  const fmt = useCurrency();
  const matrix = Array.from({ length: 7 }, () => Array(24).fill(0));
  data.forEach(({ day, hour, amount }) => {
    matrix[day][hour] = amount;
  });

  const maxVal = Math.max(...data.map((d) => d.amount), 1);

  if (!data.length) {
    return (
      <div className="flex items-center justify-center h-40 text-gray-400 text-sm">
        Немає витрат за вибраний місяць
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <div className="min-w-max select-none">
        {/* Hours header */}
        <div className="flex gap-1 mb-1 ml-9">
          {Array.from({ length: 24 }, (_, h) => (
            <div key={h} className="w-6 text-center text-xs text-gray-400 leading-none">
              {h % 2 === 0 ? h : ''}
            </div>
          ))}
        </div>

        {/* Rows */}
        {DAYS.map((dayLabel, d) => (
          <div key={d} className="flex items-center gap-1 mb-1">
            <span className="w-8 text-xs text-gray-500 text-right pr-1 shrink-0">
              {dayLabel}
            </span>
            {matrix[d].map((amount, h) => {
              const intensity = amount > 0 ? 0.12 + (amount / maxVal) * 0.88 : 0;
              return (
                <div
                  key={h}
                  title={`${dayLabel} ${h}:00 — ${amount > 0 ? fmt(amount) : '—'}`}
                  className="w-6 h-6 rounded-sm cursor-default transition-opacity"
                  style={{
                    backgroundColor: amount > 0
                      ? `rgba(239, 68, 68, ${intensity.toFixed(2)})`
                      : '#f3f4f6',
                  }}
                />
              );
            })}
          </div>
        ))}

        {/* Legend */}
        <div className="flex items-center gap-2 mt-3 ml-9">
          <span className="text-xs text-gray-400">Менше</span>
          {[0.12, 0.34, 0.56, 0.78, 1.0].map((v, i) => (
            <div
              key={i}
              className="w-5 h-5 rounded-sm"
              style={{ backgroundColor: `rgba(239, 68, 68, ${v})` }}
            />
          ))}
          <span className="text-xs text-gray-400">Більше</span>
        </div>
      </div>
    </div>
  );
}
