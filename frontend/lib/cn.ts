import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

/** Combines conditional class names (clsx) and resolves Tailwind class
 * conflicts (tailwind-merge) - e.g. cn("px-2", condition && "px-4"). */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
