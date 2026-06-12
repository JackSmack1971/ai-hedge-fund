import { useEffect } from 'react';

export type ShortcutGroup = 'Flow Editing' | 'Execution' | 'Panels' | 'Settings' | 'Help';
export type ShortcutAction =
  | 'saveFlow'
  | 'toggleRightSidebar'
  | 'toggleLeftSidebar'
  | 'fitView'
  | 'undo'
  | 'redo'
  | 'toggleBottomPanel'
  | 'runPortfolioAnalyzer'
  | 'openSettings'
  | 'openShortcutsDialog';

interface KeyboardShortcutTrigger {
  key: string;
  ctrlKey?: boolean;
  metaKey?: boolean;
  shiftKey?: boolean;
  altKey?: boolean;
}

export interface KeyboardShortcutDefinition {
  id: string;
  group: ShortcutGroup;
  label: string;
  action: ShortcutAction;
  triggers: KeyboardShortcutTrigger[];
  ignoreWhenTyping?: boolean;
}

interface KeyboardShortcut extends KeyboardShortcutTrigger {
  callback: () => void;
  preventDefault?: boolean;
  ignoreWhenTyping?: boolean;
}

interface UseKeyboardShortcutsProps {
  shortcuts: KeyboardShortcut[];
}

export const SHORTCUT_DEFINITIONS: KeyboardShortcutDefinition[] = [
  {
    id: 'save-flow',
    group: 'Flow Editing',
    label: 'Save flow',
    action: 'saveFlow',
    triggers: [
      { key: 's', ctrlKey: true, metaKey: true },
    ],
  },
  {
    id: 'toggle-left-sidebar',
    group: 'Panels',
    label: 'Toggle left sidebar',
    action: 'toggleLeftSidebar',
    triggers: [
      { key: 'b', ctrlKey: true, metaKey: true },
    ],
  },
  {
    id: 'toggle-right-sidebar',
    group: 'Panels',
    label: 'Toggle right sidebar',
    action: 'toggleRightSidebar',
    triggers: [
      { key: 'i', ctrlKey: true, metaKey: true },
    ],
  },
  {
    id: 'fit-view',
    group: 'Panels',
    label: 'Fit view',
    action: 'fitView',
    triggers: [
      { key: 'o', ctrlKey: true, metaKey: true },
    ],
  },
  {
    id: 'toggle-bottom-panel',
    group: 'Panels',
    label: 'Toggle bottom panel',
    action: 'toggleBottomPanel',
    triggers: [
      { key: 'j', ctrlKey: true, metaKey: true },
    ],
  },
  {
    id: 'run-portfolio-analyzer',
    group: 'Execution',
    label: 'Run portfolio analyzer',
    action: 'runPortfolioAnalyzer',
    triggers: [
      { key: 'enter', ctrlKey: true, metaKey: true },
    ],
  },
  {
    id: 'undo',
    group: 'Flow Editing',
    label: 'Undo',
    action: 'undo',
    triggers: [
      { key: 'z', ctrlKey: true, metaKey: true },
    ],
  },
  {
    id: 'redo',
    group: 'Flow Editing',
    label: 'Redo',
    action: 'redo',
    triggers: [
      { key: 'z', ctrlKey: true, metaKey: true, shiftKey: true },
    ],
  },
  {
    id: 'open-settings-shortcut',
    group: 'Settings',
    label: 'Open settings',
    action: 'openSettings',
    triggers: [
      { key: 'j', ctrlKey: true, metaKey: true, shiftKey: true },
      { key: ',', ctrlKey: true, metaKey: true },
    ],
  },
  {
    id: 'open-shortcuts-dialog',
    group: 'Help',
    label: 'Keyboard shortcuts',
    action: 'openShortcutsDialog',
    triggers: [
      { key: '/', shiftKey: true },
      { key: '/', ctrlKey: true, metaKey: true },
    ],
    ignoreWhenTyping: true,
  },
];

export function isMacPlatform(): boolean {
  if (typeof navigator === 'undefined') {
    return false;
  }

  return /Mac|iPhone|iPad|iPod/.test(navigator.platform);
}

export function formatShortcutTrigger(trigger: KeyboardShortcutTrigger, useMac = isMacPlatform()): string {
  if (trigger.key === '/' && trigger.shiftKey && !trigger.ctrlKey && !trigger.metaKey) {
    return '?';
  }

  const modifierLabels: string[] = [];

  if (trigger.ctrlKey || trigger.metaKey) {
    modifierLabels.push(useMac ? '⌘' : 'Ctrl');
  }

  if (trigger.shiftKey) {
    modifierLabels.push(useMac ? '⇧' : 'Shift');
  }

  if (trigger.altKey) {
    modifierLabels.push(useMac ? '⌥' : 'Alt');
  }

  const keyLabel = trigger.key.length === 1 ? trigger.key.toUpperCase() : trigger.key;

  if (useMac) {
    return `${modifierLabels.join('')}${keyLabel}`;
  }

  return modifierLabels.length > 0 ? `${modifierLabels.join('+')}+${keyLabel}` : keyLabel;
}

export function formatShortcutDefinition(definition: KeyboardShortcutDefinition, useMac = isMacPlatform()): string {
  return definition.triggers.map(trigger => formatShortcutTrigger(trigger, useMac)).join(' / ');
}

export function getShortcutDefinition(action: ShortcutAction): KeyboardShortcutDefinition | undefined {
  return SHORTCUT_DEFINITIONS.find(definition => definition.action === action);
}

export function getShortcutLabel(action: ShortcutAction, useMac = isMacPlatform()): string {
  const definition = getShortcutDefinition(action);
  return definition ? formatShortcutDefinition(definition, useMac) : '';
}

function isEditableTarget(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) {
    return false;
  }

  return target.isContentEditable || ['INPUT', 'TEXTAREA', 'SELECT'].includes(target.tagName);
}

function matchesTrigger(event: KeyboardEvent, trigger: KeyboardShortcutTrigger): boolean {
  const eventKey = event.key.toLowerCase();
  const triggerKey = trigger.key.toLowerCase();
  const keyMatch = eventKey === triggerKey
    || (triggerKey === '/' && trigger.shiftKey && eventKey === '?')
    || (triggerKey === '?' && trigger.shiftKey && eventKey === '/');
  const shiftMatch = trigger.shiftKey ? event.shiftKey : !event.shiftKey;
  const altMatch = trigger.altKey ? event.altKey : !event.altKey;
  const modifierMatch = trigger.ctrlKey || trigger.metaKey
    ? (event.ctrlKey || event.metaKey)
    : (!event.ctrlKey && !event.metaKey);

  return keyMatch && shiftMatch && altMatch && modifierMatch;
}

export function buildKeyboardShortcuts(
  actionHandlers: Partial<Record<ShortcutAction, () => void>>,
): KeyboardShortcut[] {
  return SHORTCUT_DEFINITIONS.flatMap(definition => {
    const handler = actionHandlers[definition.action];

    if (!handler) {
      return [];
    }

    return definition.triggers.map(trigger => ({
      ...trigger,
      callback: handler,
      preventDefault: true,
      ignoreWhenTyping: definition.ignoreWhenTyping,
    }));
  });
}

export function useKeyboardShortcuts({ shortcuts }: UseKeyboardShortcutsProps) {
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      shortcuts.forEach(({ key, ctrlKey, metaKey, shiftKey, altKey, callback, preventDefault = true, ignoreWhenTyping }) => {
        if (ignoreWhenTyping && isEditableTarget(event.target)) {
          return;
        }

        const shortcutMatches = matchesTrigger(event, { key, ctrlKey, metaKey, shiftKey, altKey });

        if (!shortcutMatches) {
          return;
        }

        if (preventDefault) {
          event.preventDefault();
        }

        callback();
      });
    };

    document.addEventListener('keydown', handleKeyDown);

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [shortcuts]);
}

// Convenience hook specifically for common shortcuts
export function useFlowKeyboardShortcuts(saveFlow: (showToast?: boolean) => void) {
  const shortcuts = buildKeyboardShortcuts({
    saveFlow: () => saveFlow(true),
  });

  useKeyboardShortcuts({ shortcuts });
}

// Convenience hook for layout keyboard shortcuts
export function useLayoutKeyboardShortcuts(
  toggleRightSidebar: () => void,
  toggleLeftSidebar?: () => void,
  fitView?: () => void,
  undo?: () => void,
  redo?: () => void,
  toggleBottomPanel?: () => void,
  openSettings?: () => void,
  openShortcutsDialog?: () => void
) {
  const shortcuts = buildKeyboardShortcuts({
    toggleRightSidebar,
    toggleLeftSidebar,
    fitView,
    undo,
    redo,
    toggleBottomPanel,
    openSettings,
    openShortcutsDialog,
  });

  useKeyboardShortcuts({ shortcuts });
}
