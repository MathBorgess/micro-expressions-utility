import type {
  ButtonHTMLAttributes,
  InputHTMLAttributes,
  LabelHTMLAttributes,
  ReactNode,
} from "react";
import type { JobStatus } from "@/lib/api";

export function Card({ children, className = "" }: { children: ReactNode; className?: string }) {
  return (
    <div className={`rounded-xl border border-line bg-white shadow-sm ${className}`}>{children}</div>
  );
}

export function Button({ className = "", ...props }: ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      {...props}
      className={`inline-flex h-9 items-center justify-center rounded-md bg-accent px-4 text-[14px] font-medium text-white transition-colors duration-150 ease-out hover:bg-accent-hover focus:outline-none focus-visible:ring-2 focus-visible:ring-accent/40 disabled:cursor-not-allowed disabled:opacity-60 ${className}`}
    />
  );
}

export function Input({ className = "", ...props }: InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      {...props}
      className={`h-9 rounded-lg border border-line bg-white px-3 text-[14px] outline-none transition focus:border-accent focus-visible:ring-2 focus-visible:ring-accent/40 ${className}`}
    />
  );
}

export function Label({ className = "", ...props }: LabelHTMLAttributes<HTMLLabelElement>) {
  return <label {...props} className={`text-[13px] font-medium text-ink ${className}`} />;
}

const STATUS_STYLES: Record<JobStatus, string> = {
  completed: "bg-ok-soft text-ok",
  processing: "bg-accent-soft text-accent",
  pending: "border border-line bg-page text-muted",
  failed: "bg-[#fdecec] text-danger",
};

const STATUS_LABEL: Record<JobStatus, string> = {
  completed: "concluído",
  processing: "processando",
  pending: "na fila",
  failed: "falhou",
};

export function StatusBadge({ status }: { status: JobStatus }) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 font-mono text-[11px] font-medium uppercase tracking-wide ${STATUS_STYLES[status]}`}
    >
      {STATUS_LABEL[status]}
    </span>
  );
}
