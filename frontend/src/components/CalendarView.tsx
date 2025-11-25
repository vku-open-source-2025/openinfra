import React from 'react';
import { startOfMonth, endOfMonth, startOfWeek, endOfWeek, eachDayOfInterval, format, isSameMonth, isSameDay, addMonths, subMonths } from 'date-fns';
import { ChevronLeft, ChevronRight } from 'lucide-react';

interface CalendarViewProps {
    logs: any[]; // Maintenance logs
}

const CalendarView: React.FC<CalendarViewProps> = ({ logs }) => {
    const [currentDate, setCurrentDate] = React.useState(new Date());

    const nextMonth = () => setCurrentDate(addMonths(currentDate, 1));
    const prevMonth = () => setCurrentDate(subMonths(currentDate, 1));

    const monthStart = startOfMonth(currentDate);
    const monthEnd = endOfMonth(monthStart);
    const startDate = startOfWeek(monthStart);
    const endDate = endOfWeek(monthEnd);

    const days = eachDayOfInterval({ start: startDate, end: endDate });

    const getLogsForDay = (day: Date) => {
        return logs.filter(log => isSameDay(new Date(log.scheduled_date), day));
    };

    return (
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 h-full flex flex-col">
            <div className="flex justify-between items-center mb-6">
                <h2 className="text-xl font-bold text-slate-800">
                    {format(currentDate, 'MMMM yyyy')}
                </h2>
                <div className="flex gap-2">
                    <button onClick={prevMonth} className="p-2 hover:bg-slate-100 rounded-lg">
                        <ChevronLeft size={20} />
                    </button>
                    <button onClick={nextMonth} className="p-2 hover:bg-slate-100 rounded-lg">
                        <ChevronRight size={20} />
                    </button>
                </div>
            </div>

            <div className="grid grid-cols-7 gap-px bg-slate-200 border border-slate-200 rounded-lg overflow-hidden flex-1">
                {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(day => (
                    <div key={day} className="bg-slate-50 p-2 text-center text-xs font-semibold text-slate-500 uppercase">
                        {day}
                    </div>
                ))}
                {days.map((day, idx) => {
                    const dayLogs = getLogsForDay(day);
                    return (
                        <div
                            key={day.toString()}
                            className={`bg-white p-2 min-h-[80px] ${!isSameMonth(day, monthStart) ? 'text-slate-300 bg-slate-50/50' : ''}`}
                        >
                            <div className="text-right text-sm mb-1">{format(day, 'd')}</div>
                            <div className="space-y-1">
                                {dayLogs.map((log: any) => (
                                    <div key={log._id} className={`text-[10px] px-1 py-0.5 rounded truncate ${log.status === 'Completed' ? 'bg-green-100 text-green-700' :
                                            log.status === 'In Progress' ? 'bg-blue-100 text-blue-700' :
                                                'bg-amber-100 text-amber-700'
                                        }`}>
                                        {log.description}
                                    </div>
                                ))}
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
};

export default CalendarView;
