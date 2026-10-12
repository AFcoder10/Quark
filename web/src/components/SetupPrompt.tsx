import { useState, type ReactNode } from "react";
import { LibrarySetup } from "./LibrarySetup";

interface Props {
  icon: ReactNode;
  title: string;
  description: string;
  type: "movie" | "show" | "music" | "photo" | "mixed";
  onCreated?: () => void;
}

/**
 * Empty state shown when a library type has no folder configured yet.
 * Instead of a dead end, it lets the user pick the folder right here.
 */
export function SetupPrompt({ icon, title, description, type, onCreated }: Props) {
  const [open, setOpen] = useState(false);

  return (
    <div className="empty-state setup-prompt">
      {icon}
      <h3>{title}</h3>
      <p>{description}</p>
      {!open && (
        <button className="btn btn-primary" onClick={() => setOpen(true)}>
          Choose folder
        </button>
      )}
      {open && <LibrarySetup type={type} onCreated={onCreated} />}
    </div>
  );
}
