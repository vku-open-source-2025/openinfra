import * as React from "react"
import { cn } from "../../lib/utils"
import { ChevronLeft, ChevronRight } from "lucide-react"
import { Button } from "./button"

export interface PaginationProps extends React.HTMLAttributes<HTMLDivElement> {
  currentPage: number
  totalPages: number
  onPageChange: (page: number) => void
}

export interface PaginationButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  isActive?: boolean
}

const PaginationButton = React.forwardRef<HTMLButtonElement, PaginationButtonProps>(
  ({ className, isActive, ...props }, ref) => (
    <button
      ref={ref}
      className={cn(
        "h-10 w-10 rounded-md border border-slate-300 bg-white text-sm font-medium transition-colors hover:bg-slate-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-600 disabled:pointer-events-none disabled:opacity-50",
        isActive && "bg-blue-600 text-white border-blue-600 hover:bg-blue-700",
        className
      )}
      {...props}
    />
  )
)
PaginationButton.displayName = "PaginationButton"

const Pagination = React.forwardRef<HTMLDivElement, PaginationProps>(
  ({ className, currentPage, totalPages, onPageChange, ...props }, ref) => {
    const pages = Array.from({ length: totalPages }, (_, i) => i + 1)
    const maxVisiblePages = 5
    const startPage = Math.max(1, currentPage - Math.floor(maxVisiblePages / 2))
    const endPage = Math.min(totalPages, startPage + maxVisiblePages - 1)
    const visiblePages = pages.slice(startPage - 1, endPage)

    return (
      <div
        ref={ref}
        className={cn("flex items-center justify-center gap-2", className)}
        {...props}
      >
        <Button
          variant="outline"
          size="sm"
          onClick={() => onPageChange(currentPage - 1)}
          disabled={currentPage === 1}
        >
          <ChevronLeft className="h-4 w-4" />
        </Button>
        {startPage > 1 && (
          <>
            <PaginationButton onClick={() => onPageChange(1)}>1</PaginationButton>
            {startPage > 2 && <span className="px-2">...</span>}
          </>
        )}
        {visiblePages.map((page) => (
          <PaginationButton
            key={page}
            isActive={page === currentPage}
            onClick={() => onPageChange(page)}
          >
            {page}
          </PaginationButton>
        ))}
        {endPage < totalPages && (
          <>
            {endPage < totalPages - 1 && <span className="px-2">...</span>}
            <PaginationButton onClick={() => onPageChange(totalPages)}>
              {totalPages}
            </PaginationButton>
          </>
        )}
        <Button
          variant="outline"
          size="sm"
          onClick={() => onPageChange(currentPage + 1)}
          disabled={currentPage === totalPages}
        >
          <ChevronRight className="h-4 w-4" />
        </Button>
      </div>
    )
  }
)
Pagination.displayName = "Pagination"

export { Pagination }
