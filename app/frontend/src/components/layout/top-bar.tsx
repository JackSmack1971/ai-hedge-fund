import { Button } from '@/components/ui/button';
import { getShortcutLabel } from '@/hooks/use-keyboard-shortcuts';
import { cn } from '@/lib/utils';
import { CircleHelp, PanelBottom, PanelLeft, PanelRight, Settings } from 'lucide-react';

interface TopBarProps {
  isLeftCollapsed: boolean;
  isRightCollapsed: boolean;
  isBottomCollapsed: boolean;
  onToggleLeft: () => void;
  onToggleRight: () => void;
  onToggleBottom: () => void;
  onSettingsClick: () => void;
  onShortcutsClick: () => void;
}

export function TopBar({
  isLeftCollapsed,
  isRightCollapsed,
  isBottomCollapsed,
  onToggleLeft,
  onToggleRight,
  onToggleBottom,
  onSettingsClick,
  onShortcutsClick,
}: TopBarProps) {
  const leftSidebarShortcut = getShortcutLabel('toggleLeftSidebar');
  const bottomPanelShortcut = getShortcutLabel('toggleBottomPanel');
  const rightSidebarShortcut = getShortcutLabel('toggleRightSidebar');
  const settingsShortcut = getShortcutLabel('openSettings');
  const shortcutsShortcut = getShortcutLabel('openShortcutsDialog');

  return (
    <div className="absolute top-0 right-0 z-40 flex items-center gap-0 py-1 px-2 bg-panel/80">
      {/* Left Sidebar Toggle */}
      <Button
        variant="ghost"
        size="sm"
        onClick={onToggleLeft}
        className={cn(
          "h-8 w-8 p-0 text-muted-foreground hover:text-foreground hover:bg-ramp-grey-700 transition-colors",
          !isLeftCollapsed && "text-foreground"
        )}
        aria-label="Toggle left sidebar"
        title={`Toggle left sidebar (${leftSidebarShortcut})`}
      >
        <PanelLeft size={16} />
      </Button>

      {/* Bottom Panel Toggle */}
      <Button
        variant="ghost"
        size="sm"
        onClick={onToggleBottom}
        className={cn(
          "h-8 w-8 p-0 text-muted-foreground hover:text-foreground hover:bg-ramp-grey-700 transition-colors",
          !isBottomCollapsed && "text-foreground"
        )}
        aria-label="Toggle bottom panel"
        title={`Toggle bottom panel (${bottomPanelShortcut})`}
      >
        <PanelBottom size={16} />
      </Button>

      {/* Right Sidebar Toggle */}
      <Button
        variant="ghost"
        size="sm"
        onClick={onToggleRight}
        className={cn(
          "h-8 w-8 p-0 text-muted-foreground hover:text-foreground hover:bg-ramp-grey-700 transition-colors",
          !isRightCollapsed && "text-foreground"
        )}
        aria-label="Toggle right sidebar"
        title={`Toggle right sidebar (${rightSidebarShortcut})`}
      >
        <PanelRight size={16} />
      </Button>

      {/* Divider */}
      <div className="w-px h-5 bg-ramp-grey-700 mx-1" />

      {/* Settings */}
      <Button
        variant="ghost"
        size="sm"
        onClick={onSettingsClick}
        className="h-8 w-8 p-0 text-muted-foreground hover:text-foreground hover:bg-ramp-grey-700 transition-colors"
        aria-label="Open settings"
        title={`Open settings (${settingsShortcut})`}
      >
        <Settings size={16} />
      </Button>

      {/* Shortcuts Help */}
      <Button
        variant="ghost"
        size="sm"
        onClick={onShortcutsClick}
        className="h-8 w-8 p-0 text-muted-foreground hover:text-foreground hover:bg-ramp-grey-700 transition-colors"
        aria-label="Keyboard shortcuts"
        title={`Keyboard shortcuts (${shortcutsShortcut})`}
      >
        <CircleHelp size={16} />
      </Button>
    </div>
  );
} 
