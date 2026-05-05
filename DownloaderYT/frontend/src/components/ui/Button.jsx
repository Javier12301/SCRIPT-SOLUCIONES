import clsx from "clsx";

export function Button({ className, variant = "primary", size = "md", ...props }) {
  return <button className={clsx("btn", `btn-${variant}`, `btn-${size}`, className)} {...props} />;
}
