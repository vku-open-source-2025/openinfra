import * as React from "react"
import { cn } from "../../lib/utils"

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "secondary" | "destructive" | "outline" | "success" | "warning"
}

const Badge = React.forwardRef<HTMLDivElement, BadgeProps>(
  ({ className, variant = "default", ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2",
          {
            "border-transparent bg-blue-600 text-white": variant === "default",
            "border-transparent bg-slate-100 text-slate-900": variant === "secondary",
            "border-transparent bg-red-600 text-white": variant === "destructive",
            "border-slate-200 bg-transparent text-slate-900": variant === "outline",
            "border-transparent bg-green-600 text-white": variant === "success",
            "border-transparent bg-amber-600 text-white": variant === "warning",
          },
          className
        )}
        {...props}
      />
    )
  }
)
Badge.displayName = "Badge"

export { Badge }
