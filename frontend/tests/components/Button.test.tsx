/**
 * Тесты для компонента Button.
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';

// Простой компонент кнопки для демонстрации тестирования
function Button({
  children,
  onClick,
  disabled = false,
  variant = 'primary',
}: {
  children: React.ReactNode;
  onClick?: () => void;
  disabled?: boolean;
  variant?: 'primary' | 'secondary';
}) {
  const baseStyles = 'px-4 py-2 rounded font-medium transition-colors';
  const variantStyles = {
    primary: 'bg-primary-600 text-white hover:bg-primary-700',
    secondary: 'bg-gray-200 text-gray-800 hover:bg-gray-300',
  };

  return (
    <button
      className={`${baseStyles} ${variantStyles[variant]}`}
      onClick={onClick}
      disabled={disabled}
    >
      {children}
    </button>
  );
}

describe('Button', () => {
  it('отображает текст кнопки', () => {
    render(<Button>Нажми меня</Button>);

    expect(screen.getByText('Нажми меня')).toBeInTheDocument();
  });

  it('вызывает onClick при клике', () => {
    const handleClick = vi.fn();
    render(<Button onClick={handleClick}>Кнопка</Button>);

    fireEvent.click(screen.getByText('Кнопка'));

    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('не вызывает onClick когда disabled', () => {
    const handleClick = vi.fn();
    render(
      <Button onClick={handleClick} disabled>
        Кнопка
      </Button>
    );

    fireEvent.click(screen.getByText('Кнопка'));

    expect(handleClick).not.toHaveBeenCalled();
  });

  it('имеет атрибут disabled когда передан disabled prop', () => {
    render(<Button disabled>Отключена</Button>);

    expect(screen.getByText('Отключена')).toBeDisabled();
  });

  it('отображает разные варианты стилей', () => {
    const { rerender } = render(<Button variant="primary">Primary</Button>);

    const primaryButton = screen.getByText('Primary');
    expect(primaryButton).toHaveClass('bg-primary-600');

    rerender(<Button variant="secondary">Secondary</Button>);

    const secondaryButton = screen.getByText('Secondary');
    expect(secondaryButton).toHaveClass('bg-gray-200');
  });
});
