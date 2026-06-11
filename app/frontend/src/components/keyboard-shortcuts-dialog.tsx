import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  SHORTCUT_DEFINITIONS,
  formatShortcutDefinition,
  isMacPlatform,
  type KeyboardShortcutDefinition,
} from '@/hooks/use-keyboard-shortcuts';

interface KeyboardShortcutsDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const GROUP_ORDER = ['Flow Editing', 'Execution', 'Panels', 'Settings', 'Help'] as const;

function ShortcutPill({ label }: { label: string }) {
  return (
    <kbd className="inline-flex items-center rounded-md border border-border bg-muted px-2 py-1 text-[11px] font-mono font-medium text-foreground shadow-sm">
      {label}
    </kbd>
  );
}

function ShortcutRow({ shortcut }: { shortcut: KeyboardShortcutDefinition }) {
  return (
    <div className="flex flex-col gap-2 rounded-lg border border-border/60 bg-background/40 p-3 sm:flex-row sm:items-center sm:justify-between">
      <div className="space-y-0.5">
        <div className="font-medium text-foreground">{shortcut.label}</div>
      </div>
      <div className="flex flex-wrap items-center gap-1.5">
        {shortcut.triggers.map(trigger => (
          <ShortcutPill
            key={`${shortcut.id}:${trigger.key}:${trigger.ctrlKey ? 'c' : ''}${trigger.metaKey ? 'm' : ''}${trigger.shiftKey ? 's' : ''}${trigger.altKey ? 'a' : ''}`}
            label={formatShortcutDefinition({
              ...shortcut,
              triggers: [trigger],
            }, isMacPlatform())}
          />
        ))}
      </div>
    </div>
  );
}

export function KeyboardShortcutsDialog({ open, onOpenChange }: KeyboardShortcutsDialogProps) {
  const groupedShortcuts = GROUP_ORDER
    .map(group => ({
      group,
      shortcuts: SHORTCUT_DEFINITIONS.filter(shortcut => shortcut.group === group),
    }))
    .filter(section => section.shortcuts.length > 0);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl">
        <DialogHeader>
          <DialogTitle>Keyboard shortcuts</DialogTitle>
          <DialogDescription>
            Fast paths for navigation, editing, and execution. Press Esc to close.
          </DialogDescription>
        </DialogHeader>

        <div className="grid gap-6 md:grid-cols-2">
          {groupedShortcuts.map(section => (
            <section key={section.group} className="space-y-3">
              <h3 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
                {section.group}
              </h3>
              <div className="space-y-2">
                {section.shortcuts.map(shortcut => (
                  <ShortcutRow key={shortcut.id} shortcut={shortcut} />
                ))}
              </div>
            </section>
          ))}
        </div>
      </DialogContent>
    </Dialog>
  );
}
