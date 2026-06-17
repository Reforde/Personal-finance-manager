import { useForm } from 'react-hook-form';
import { yupResolver } from '@hookform/resolvers/yup';
import * as yup from 'yup';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const schema = yup.object({
  email: yup.string().email('Невірний формат email').required("Обов'язкове поле"),
  password: yup.string().min(8, 'Мінімум 8 символів').required("Обов'язкове поле"),
  confirmPassword: yup
    .string()
    .oneOf([yup.ref('password')], 'Паролі не співпадають')
    .required("Обов'язкове поле"),
});

export default function RegisterPage() {
  const { register: registerUser } = useAuth();
  const navigate = useNavigate();

  const {
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm({ resolver: yupResolver(schema) });

  const onSubmit = async ({ email, password }) => {
    try {
      await registerUser(email, password);
      navigate('/dashboard', { replace: true });
    } catch (err) {
      const serverErrors = err.response?.data?.errors;
      if (serverErrors?.email) {
        setError('email', { message: serverErrors.email[0] });
      } else {
        const msg = err.response?.data?.error || 'Помилка реєстрації. Спробуйте ще раз.';
        setError('root', { message: msg });
      }
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
      <div className="bg-white p-8 rounded-2xl shadow-sm border border-gray-200 w-full max-w-md">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Реєстрація</h1>
        <p className="text-sm text-gray-500 mb-6">Створіть новий акаунт</p>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <Field label="Email" error={errors.email?.message}>
            <input
              {...register('email')}
              type="email"
              autoComplete="email"
              placeholder="you@example.com"
              className={inputCls(!!errors.email)}
            />
          </Field>

          <Field label="Пароль" error={errors.password?.message}>
            <input
              {...register('password')}
              type="password"
              autoComplete="new-password"
              placeholder="Мінімум 8 символів"
              className={inputCls(!!errors.password)}
            />
          </Field>

          <Field label="Підтвердіть пароль" error={errors.confirmPassword?.message}>
            <input
              {...register('confirmPassword')}
              type="password"
              autoComplete="new-password"
              placeholder="••••••••"
              className={inputCls(!!errors.confirmPassword)}
            />
          </Field>

          {errors.root && (
            <div className="bg-red-50 border border-red-200 text-red-700 text-sm px-4 py-3 rounded-lg">
              {errors.root.message}
            </div>
          )}

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full bg-blue-600 text-white py-2.5 rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            {isSubmitting ? 'Реєстрація...' : 'Зареєструватись'}
          </button>
        </form>

        <p className="text-center text-sm text-gray-500 mt-5">
          Вже є акаунт?{' '}
          <Link to="/login" className="text-blue-600 hover:underline font-medium">
            Увійти
          </Link>
        </p>
      </div>
    </div>
  );
}

function Field({ label, error, children }) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
      {children}
      {error && <p className="text-red-500 text-xs mt-1">{error}</p>}
    </div>
  );
}

const inputCls = (hasError) =>
  `w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 transition ${
    hasError ? 'border-red-400 bg-red-50' : 'border-gray-300'
  }`;
