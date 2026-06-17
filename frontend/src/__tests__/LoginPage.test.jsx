import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import LoginPage from '../pages/LoginPage';
import { AuthContext } from '../context/AuthContext';

function renderLogin(loginFn = vi.fn()) {
  return render(
    <MemoryRouter>
      <AuthContext.Provider value={{ login: loginFn }}>
        <LoginPage />
      </AuthContext.Provider>
    </MemoryRouter>,
  );
}

describe('LoginPage', () => {
  it('renders email and password fields', () => {
    renderLogin();
    expect(screen.getByPlaceholderText('you@example.com')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('••••••••')).toBeInTheDocument();
  });

  it('shows validation errors for empty submit', async () => {
    const user = userEvent.setup();
    renderLogin();
    await user.click(screen.getByRole('button', { name: /увійти/i }));
    await waitFor(() => {
      expect(screen.getByText(/обов'язкове поле/i)).toBeInTheDocument();
    });
  });

  it('shows error for short password', async () => {
    const user = userEvent.setup();
    renderLogin();
    await user.type(screen.getByPlaceholderText('you@example.com'), 'user@test.com');
    await user.type(screen.getByPlaceholderText('••••••••'), '123');
    await user.click(screen.getByRole('button', { name: /увійти/i }));
    await waitFor(() => {
      expect(screen.getByText(/мінімум 8 символів/i)).toBeInTheDocument();
    });
  });

  it('calls login with correct credentials on success', async () => {
    const user = userEvent.setup();
    const loginFn = vi.fn().mockResolvedValue({});
    renderLogin(loginFn);

    await user.type(screen.getByPlaceholderText('you@example.com'), 'user@test.com');
    await user.type(screen.getByPlaceholderText('••••••••'), 'password123');
    await user.click(screen.getByRole('button', { name: /увійти/i }));

    await waitFor(() => {
      expect(loginFn).toHaveBeenCalledWith('user@test.com', 'password123');
    });
  });

  it('shows server error message on login failure', async () => {
    const user = userEvent.setup();
    const loginFn = vi.fn().mockRejectedValue({
      response: { data: { error: 'Невірний пароль' } },
    });
    renderLogin(loginFn);

    await user.type(screen.getByPlaceholderText('you@example.com'), 'user@test.com');
    await user.type(screen.getByPlaceholderText('••••••••'), 'wrongpassword');
    await user.click(screen.getByRole('button', { name: /увійти/i }));

    await waitFor(() => {
      expect(screen.getByText('Невірний пароль')).toBeInTheDocument();
    });
  });

  it('shows fallback error when no server message', async () => {
    const user = userEvent.setup();
    const loginFn = vi.fn().mockRejectedValue(new Error('Network error'));
    renderLogin(loginFn);

    await user.type(screen.getByPlaceholderText('you@example.com'), 'user@test.com');
    await user.type(screen.getByPlaceholderText('••••••••'), 'somepassword');
    await user.click(screen.getByRole('button', { name: /увійти/i }));

    await waitFor(() => {
      expect(screen.getByText(/помилка входу/i)).toBeInTheDocument();
    });
  });
});
