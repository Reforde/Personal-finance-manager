import { useAuth } from '../context/AuthContext';
import { useRates } from '../context/RatesContext';
import { formatCurrency } from '../utils/formatCurrency';

export function useCurrency() {
  const { user } = useAuth();
  const { rates } = useRates();
  const currency = user?.default_currency || 'UAH';

  return (kopecks, short = false) => {
    let amount = kopecks ?? 0;
    if (currency !== 'UAH' && rates[currency]) {
      // Convert UAH kopecks to target currency's smallest unit (cents/eurocents)
      amount = Math.round(amount / rates[currency]);
    }
    return formatCurrency(amount, short, currency);
  };
}
