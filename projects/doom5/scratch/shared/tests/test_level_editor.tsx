import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import LevelEditor, { LevelDefinition } from '../../src/editor/levels/level_editor';

describe('LevelEditor UI integration and rendering', () => {
  test('end-to-end: paint and Save Level returns updated grid', () => {
    let savedLevel: LevelDefinition | undefined;
    render(<LevelEditor onSave={(lvl) => (savedLevel = lvl)} />);

    const cell00 = screen.getByTestId('cell-0-0');
    const cell01 = screen.getByTestId('cell-0-1');

    // simulate drag painting two cells
    fireEvent.mouseDown(cell00);
    fireEvent.mouseEnter(cell01);
    fireEvent.mouseUp(cell01);

    const saveBtn = screen.getByRole('button', { name: /save level/i });
    fireEvent.click(saveBtn);

    expect(savedLevel).toBeDefined();
    expect(savedLevel?.grid[0][0]).toBe(1);
    expect(savedLevel?.grid[0][1]).toBe(1);
  });

  test('end-to-end: load provided level and Save preserves data', () => {
    const initial: LevelDefinition = {
      id: 'level-42',
      name: 'Test Level',
      grid: [
        [0, 1],
        [1, 0],
      ],
    };
    let captured: LevelDefinition | undefined;
    render(<LevelEditor level={initial} onSave={(lvl) => (captured = lvl)} />);

    // Save should reflect the provided level grid
    const saveBtn = screen.getByRole('button', { name: /save level/i });
    fireEvent.click(saveBtn);

    expect(captured).toBeDefined();
    expect(captured?.grid).toEqual(initial.grid);
  });

  test('undo basics: after a paint action, Undo reverts last change', () => {
    let saved: LevelDefinition | undefined;
    render(<LevelEditor onSave={(lvl) => (saved = lvl)} />);

    const cell00 = screen.getByTestId('cell-0-0');
    const cell01 = screen.getByTestId('cell-0-1');

    // Paint first cell and capture before undo
    fireEvent.mouseDown(cell00);
    fireEvent.mouseEnter(cell01);
    fireEvent.mouseUp(cell01);

    // Undo
    const undoBtn = screen.getByRole('button', { name: /undo/i });
    fireEvent.click(undoBtn);

    // Save after undo
    const saveBtn = screen.getByRole('button', { name: /save level/i });
    fireEvent.click(saveBtn);

    expect(saved).toBeDefined();
    expect(saved?.grid[0][0]).toBe(0);
  });

  test('input latency: painting a cell and saving completes within a threshold', async () => {
    let saved: LevelDefinition | undefined;
    let t0 = performance.now();

    render(<LevelEditor onSave={(lvl) => { saved = lvl; t0 = t0; }} />);

    const cell00 = screen.getByTestId('cell-0-0');
    fireEvent.mouseDown(cell00);
    fireEvent.mouseUp(cell00);

    const saveBtn = screen.getByRole('button', { name: /save level/i });
    const start = performance.now();
    fireEvent.click(saveBtn);
    // Allow any microtasks to flush
    await new Promise((r) => setTimeout(r, 0));
    const duration = performance.now() - start;
    // Expect the save path to complete quickly (threshold 200ms)
    expect(duration).toBeLessThan(300);
  });

  test('keyboard navigation: arrow keys move focus between cells', () => {
    render(<LevelEditor />);
    const first = screen.getByTestId('cell-0-0');
    // Focus first cell
    (first as HTMLElement).focus();
    expect(document.activeElement).toBe(first);

    // Press ArrowRight to move to cell-0-1
    fireEvent.keyDown(first as HTMLElement, { key: 'ArrowRight' } as KeyboardEventInit);
    const next = screen.getByTestId('cell-0-1');
    // Focus should have moved to the right cell
    expect(document.activeElement).toBe(next);
  });

  test('loadable grid through LevelEditor props exposes accessible labels', () => {
    const { container } = render(
      <LevelEditor level={{ id: 'Aid', name: 'Accessible Level', grid: [[0, 0], [0, 0]] }} />
    );
    // Root should have aria-label
    const root = container.querySelector('[aria-label="Level editor grid"]');
    expect(root).not.toBeNull();

    // All cells should have aria-label attributes
    const cells = container.querySelectorAll('button[aria-label]');
    expect(cells.length).toBeGreaterThan(0);
  });
});
