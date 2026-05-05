import clsx from "clsx";

const COLORS = ["orange", "blue", "purple", "green", "yellow", "teal", "gray"];

export function Avatar({ name = "Usuario", tone, className }) {
  const initials = name
    .split(/[\s._-]+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join("") || "U";
  const color = tone || COLORS[Math.abs(name.length) % COLORS.length];

  return <span className={clsx("avatar", `avatar-${color}`, className)}>{initials}</span>;
}
