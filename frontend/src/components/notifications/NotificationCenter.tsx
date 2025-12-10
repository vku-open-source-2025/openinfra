import { useState, useEffect } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { notificationsApi } from "../../api/notifications"
import { NotificationItem } from "./NotificationItem"
import { NotificationBadge } from "./NotificationBadge"
import { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem } from "../ui/dropdown-menu"
import { Button } from "../ui/button"
import { Skeleton } from "../ui/skeleton"
import { Bell, Check, CheckCheck } from "lucide-react"

export const NotificationCenter: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false)
  const queryClient = useQueryClient()

  const { data: notifications, isLoading } = useQuery({
    queryKey: ["notifications"],
    queryFn: () => notificationsApi.list({ limit: 20, unread_only: false }),
    refetchInterval: 60000, // Refresh every minute
  })

  const { data: unreadCount } = useQuery({
    queryKey: ["notifications", "unread-count"],
    queryFn: () => notificationsApi.getUnreadCount(),
    refetchInterval: 30000, // Refresh every 30 seconds
  })

  const markAsReadMutation = useMutation({
    mutationFn: (id: string) => notificationsApi.markAsRead(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications"] })
      queryClient.invalidateQueries({ queryKey: ["notifications", "unread-count"] })
    },
  })

  const markAllAsReadMutation = useMutation({
    mutationFn: () => notificationsApi.markAllAsRead(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications"] })
      queryClient.invalidateQueries({ queryKey: ["notifications", "unread-count"] })
    },
  })

  const unreadNotifications = notifications?.filter((n) => !n.read) || []
  const readNotifications = notifications?.filter((n) => n.read) || []

  return (
    <DropdownMenu open={isOpen} onOpenChange={setIsOpen}>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" className="relative">
          <NotificationBadge count={unreadCount?.unread_count || 0} />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-80 max-h-[500px] overflow-y-auto">
        <div className="p-2 border-b">
          <div className="flex items-center justify-between mb-2">
            <h3 className="font-semibold text-sm">Thông báo</h3>
            {unreadNotifications.length > 0 && (
                <Button
                variant="ghost"
                size="sm"
                onClick={() => markAllAsReadMutation.mutate()}
                disabled={markAllAsReadMutation.isPending}
                className="h-7 text-xs"
              >
                <CheckCheck className="h-3 w-3 mr-1" />
                Đánh dấu tất cả là đã đọc
              </Button>
            )}
          </div>
        </div>

        {isLoading ? (
          <div className="p-2 space-y-2">
            {[...Array(3)].map((_, i) => (
              <Skeleton key={i} className="h-20 w-full" />
            ))}
          </div>
        ) : notifications && notifications.length > 0 ? (
          <div className="p-2 space-y-2">
            {unreadNotifications.length > 0 && (
              <>
                {unreadNotifications.map((notification) => (
                  <div key={notification.id} className="relative">
                    <NotificationItem
                      notification={notification}
                      onClick={() => {
                        if (!notification.read) {
                          markAsReadMutation.mutate(notification.id)
                        }
                      }}
                    />
                  </div>
                ))}
                    {readNotifications.length > 0 && (
                  <div className="border-t pt-2 mt-2">
                    <p className="text-xs text-slate-500 mb-2 px-2">Trước đây</p>
                  </div>
                )}
              </>
            )}
            {readNotifications.map((notification) => (
              <NotificationItem key={notification.id} notification={notification} />
            ))}
          </div>
        ) : (
          <div className="p-8 text-center text-slate-500">
            <Bell className="h-8 w-8 mx-auto mb-2 text-slate-400" />
            <p className="text-sm">Không có thông báo</p>
          </div>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
