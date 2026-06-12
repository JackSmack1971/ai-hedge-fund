import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { Copy, Edit, Trash2 } from 'lucide-react';
import { useEffect, useRef } from 'react';

interface FlowContextMenuProps {
  isOpen: boolean;
  position: { x: number; y: number };
  onClose: () => void;
  onEdit: () => void;
  onDuplicate: () => void;
  onDelete: () => void;
}

export function FlowContextMenu({ 
  isOpen, 
  position, 
  onClose, 
  onEdit, 
  onDuplicate, 
  onDelete 
}: FlowContextMenuProps) {
  const menuRef = useRef<HTMLDivElement>(null);
  const itemRefs = useRef<Array<HTMLButtonElement | null>>([]);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        onClose();
      }
    };

    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      document.addEventListener('keydown', handleEscape);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleEscape);
    };
  }, [isOpen, onClose]);

  useEffect(() => {
    if (isOpen) {
      itemRefs.current[0]?.focus();
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleAction = (action: () => void) => {
    action();
    onClose();
  };

  const handleItemKeyDown = (
    event: React.KeyboardEvent<HTMLButtonElement>,
    index: number,
    action: () => void
  ) => {
    const lastIndex = 2;

    if (event.key === 'ArrowDown' || event.key === 'ArrowUp' || event.key === 'Home' || event.key === 'End') {
      event.preventDefault();

      let nextIndex = index;
      if (event.key === 'ArrowDown') nextIndex = (index + 1) % (lastIndex + 1);
      if (event.key === 'ArrowUp') nextIndex = (index - 1 + (lastIndex + 1)) % (lastIndex + 1);
      if (event.key === 'Home') nextIndex = 0;
      if (event.key === 'End') nextIndex = lastIndex;

      itemRefs.current[nextIndex]?.focus();
      return;
    }

    if (event.key === 'Escape') {
      event.preventDefault();
      onClose();
      return;
    }

    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      handleAction(action);
    }
  };

  return (
    <div
      ref={menuRef}
      className={cn(
        "fixed z-50 min-w-[160px] bg-panel border border-border rounded-md shadow-lg",
        "animate-in fade-in-0 zoom-in-95"
      )}
      role="menu"
      style={{
        left: position.x,
        top: position.y,
      }}
    >
      <div className="p-1">
        <Button
          ref={(el) => { itemRefs.current[0] = el; }}
          variant="ghost"
          size="sm"
          className="w-full justify-start text-primary hover-bg"
          role="menuitem"
          tabIndex={0}
          aria-label="Edit flow"
          onKeyDown={(event) => handleItemKeyDown(event, 0, onEdit)}
          onClick={() => handleAction(onEdit)}
        >
          <Edit size={14} className="mr-2" />
          Edit
        </Button>
        
        <Button
          ref={(el) => { itemRefs.current[1] = el; }}
          variant="ghost"
          size="sm"
          className="w-full justify-start text-primary hover-bg"
          onClick={() => handleAction(onDuplicate)}
        >
          <Copy size={14} className="mr-2" />
          Duplicate
        </Button>
        
        <Button
          ref={(el) => { itemRefs.current[2] = el; }}
          variant="ghost"
          size="sm"
          className="w-full justify-start text-destructive hover:bg-destructive/10 hover:text-destructive"
          onClick={() => handleAction(onDelete)}
        >
          <Trash2 size={14} className="mr-2" />
          Delete
        </Button>
      </div>
    </div>
  );
}
