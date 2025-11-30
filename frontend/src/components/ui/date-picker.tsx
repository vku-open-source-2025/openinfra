import * as React from "react"
import { cn } from "../../lib/utils"
import { Calendar } from "lucide-react"
import { format } from "date-fns"

export interface DatePickerProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, "value" | "onChange"> {
  value?: Date | null
  onChange?: (date: Date | null) => void
  placeholder?: string
}

const DatePicker = React.forwardRef<HTMLInputElement, DatePickerProps>(
  ({ className, value, onChange, placeholder = "Select date", ...props }, ref) => {
    const [isOpen, setIsOpen] = React.useState(false)
    const inputRef = React.useRef<HTMLInputElement>(null)
    const calendarRef = React.useRef<HTMLDivElement>(null)

    React.useImperativeHandle(ref, () => inputRef.current!)

    React.useEffect(() => {
      const handleClickOutside = (event: MouseEvent) => {
        if (
          calendarRef.current &&
          !calendarRef.current.contains(event.target as Node) &&
          inputRef.current &&
          !inputRef.current.contains(event.target as Node)
        ) {
          setIsOpen(false)
        }
      }
      if (isOpen) {
        document.addEventListener("mousedown", handleClickOutside)
        return () => document.removeEventListener("mousedown", handleClickOutside)
      }
    }, [isOpen])

    const handleDateSelect = (date: Date) => {
      onChange?.(date)
      setIsOpen(false)
    }

    const renderCalendar = () => {
      if (!isOpen) return null

      const today = new Date()
      const currentMonth = value ? value.getMonth() : today.getMonth()
      const currentYear = value ? value.getFullYear() : today.getFullYear()

      const firstDay = new Date(currentYear, currentMonth, 1)
      const lastDay = new Date(currentYear, currentMonth + 1, 0)
      const daysInMonth = lastDay.getDate()
      const startingDayOfWeek = firstDay.getDay()

      const days: (number | null)[] = []
      for (let i = 0; i < startingDayOfWeek; i++) {
        days.push(null)
      }
      for (let i = 1; i <= daysInMonth; i++) {
        days.push(i)
      }

      return (
        <div
          ref={calendarRef}
          className="absolute z-50 mt-1 w-64 rounded-md border border-slate-200 bg-white shadow-lg p-3"
        >
          <div className="flex items-center justify-between mb-2">
            <button
              type="button"
              onClick={() => {
                const prevMonth = new Date(currentYear, currentMonth - 1, 1)
                onChange?.(prevMonth)
              }}
              className="p-1 hover:bg-slate-100 rounded"
            >
              ←
            </button>
            <div className="font-semibold">
              {format(new Date(currentYear, currentMonth, 1), "MMMM yyyy")}
            </div>
            <button
              type="button"
              onClick={() => {
                const nextMonth = new Date(currentYear, currentMonth + 1, 1)
                onChange?.(nextMonth)
              }}
              className="p-1 hover:bg-slate-100 rounded"
            >
              →
            </button>
          </div>
          <div className="grid grid-cols-7 gap-1 mb-2">
            {["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"].map((day) => (
              <div key={day} className="text-xs font-medium text-slate-500 text-center p-1">
                {day}
              </div>
            ))}
          </div>
          <div className="grid grid-cols-7 gap-1">
            {days.map((day, idx) => {
              if (day === null) {
                return <div key={idx} className="p-2" />
              }
              const date = new Date(currentYear, currentMonth, day)
              const isSelected = value && format(value, "yyyy-MM-dd") === format(date, "yyyy-MM-dd")
              const isToday = format(today, "yyyy-MM-dd") === format(date, "yyyy-MM-dd")

              return (
                <button
                  key={idx}
                  type="button"
                  onClick={() => handleDateSelect(date)}
                  className={cn(
                    "p-2 text-sm rounded hover:bg-slate-100",
                    isSelected && "bg-blue-600 text-white hover:bg-blue-700",
                    !isSelected && isToday && "bg-slate-100 font-semibold"
                  )}
                >
                  {day}
                </button>
              )
            })}
          </div>
        </div>
      )
    }

    return (
      <div className="relative">
        <div className="relative">
          <input
            ref={inputRef}
            type="text"
            readOnly
            value={value ? format(value, "yyyy-MM-dd") : ""}
            placeholder={placeholder}
            onClick={() => setIsOpen(!isOpen)}
            className={cn(
              "flex h-10 w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm ring-offset-white placeholder:text-slate-500 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-600 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 pr-10",
              className
            )}
            {...props}
          />
          <Calendar className="absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 pointer-events-none text-slate-500" />
        </div>
        {renderCalendar()}
      </div>
    )
  }
)
DatePicker.displayName = "DatePicker"

export { DatePicker }
