import clsx from "clsx";

export function Badge({ children, kind = "neutral", className }) {
  return <span className={clsx("badge", `badge-${kind}`, className)}>{children}</span>;
}
