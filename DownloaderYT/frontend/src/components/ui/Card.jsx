import clsx from "clsx";

export function Card({ className, children, ...props }) {
  return (
    <section className={clsx("card", className)} {...props}>
      {children}
    </section>
  );
}
