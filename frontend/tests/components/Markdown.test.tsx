import { render } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { Markdown } from '@/components/Markdown';

describe('Markdown', () => {
  it('рендерит картинку с размером через сырой <img>', () => {
    const { container } = render(
      <Markdown>{'<img src="https://example.com/a.png" height="400" alt="x" />'}</Markdown>,
    );
    const img = container.querySelector('img');
    expect(img).not.toBeNull();
    expect(img?.getAttribute('src')).toBe('https://example.com/a.png');
    expect(img?.style.height).toBe('400px');
    // ширина не задана — auto, пропорции сохраняются
    expect(img?.style.width).toBe('auto');
  });

  it('вырезает <script> и обработчики событий (санитизация)', () => {
    const { container } = render(
      <Markdown>
        {'<script>window.__pwned = 1</script><img src="x" onerror="window.__pwned = 1" />'}
      </Markdown>,
    );
    expect(container.querySelector('script')).toBeNull();
    const img = container.querySelector('img');
    expect(img?.getAttribute('onerror')).toBeNull();
  });

  it('рендерит обычный Markdown (жирный текст)', () => {
    const { container } = render(<Markdown>{'Текст с **жирным**.'}</Markdown>);
    expect(container.querySelector('strong')?.textContent).toBe('жирным');
  });
});
