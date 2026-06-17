const FORMATTERS = {};
const SYMBOLS = { UAH: '₴', USD: '$', EUR: '€' };

function getFormatter(currency) {
  if (!FORMATTERS[currency]) {
    FORMATTERS[currency] = new Intl.NumberFormat('uk-UA', {
      style: 'currency',
      currency,
      minimumFractionDigits: 2,
    });
  }
  return FORMATTERS[currency];
}

// currency is optional 3rd param — existing callers using (kopecks, true) still work
export function formatCurrency(kopecks, short = false, currency = 'UAH') {
  const amount = (kopecks ?? 0) / 100;
  if (short && Math.abs(amount) >= 1000) {
    return `${(amount / 1000).toFixed(1)}k ${SYMBOLS[currency] ?? currency}`;
  }
  return getFormatter(currency).format(amount);
}
