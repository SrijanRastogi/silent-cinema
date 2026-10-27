import type { ReactNode } from "react";

type PageHeaderProps = {
  title: string;
  description: string;
  children?: ReactNode;
};

export function PageHeader({ title, description, children }: PageHeaderProps) {
  return (
    <header className="max-w-3xl">
      <h1 className="text-3xl font-medium tracking-tight md:text-4xl">{title}</h1>
      <p className="mt-3 max-w-prose text-base leading-7 text-muted-foreground">{description}</p>
      {children}
    </header>
  );
}
