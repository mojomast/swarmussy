# FRONTEND Architecture and Guidelines

This document outlines the frontend scaffolding for the ECS demo and Level Editor.

## Components
- LevelEditor
  - Grid-based editing surface with 36px cells.
  - Click to toggle, drag to paint walls, save to JSON.
- EditorUI
  - Simple header with New/Load/Save and a content slot.
- GamePreview
  - Canvas-backed render of a world-like state with a grid backdrop and entities.

## Data Contracts
- LevelDefinition: { id: string; name: string; grid: number[][] }
- WorldLike: { grid?: number[][]; entities?: {id?: string; x: number; y: number; w?: number; h?: number; color?: string}[] }

## Accessibility
- All interactive grid cells have ARIA labels.
- Canvas has aria-labels for screen readers.

## Integrations
- LevelEditor saves LevelDefinition; wire to ECS world to spawn walls/tiles.
- GamePreview consumes a WorldLike object for visualizing the ECS state.
