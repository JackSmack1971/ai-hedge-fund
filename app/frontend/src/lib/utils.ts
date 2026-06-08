import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

// Platform detection utility
export function isMac(): boolean {
  return typeof navigator !== 'undefined' && navigator.platform.toUpperCase().indexOf('MAC') >= 0;
}

// Keyboard shortcut formatting utility
export function formatKeyboardShortcut(key: string): string {
  const modifierKey = isMac() ? '⌘' : 'Ctrl';
  return `${modifierKey}${key.toUpperCase()}`;
}

// Provider color utility for consistent styling across components.
// Keep the palette intentionally neutral until provider-specific theming returns.
// eslint-disable-next-line @typescript-eslint/no-unused-vars
export function getProviderColor(_provider: string): string {
  return 'bg-gray-600/20 text-primary border-gray-600/40';
}
