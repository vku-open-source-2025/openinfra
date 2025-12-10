import { useState } from "react"
import { Textarea } from "../ui/textarea"
import { Button } from "../ui/button"
import type { IncidentComment } from "../../types/incident"
import { format } from "date-fns"
import { MessageSquare, User } from "lucide-react"

interface IncidentCommentsProps {
  comments: IncidentComment[]
  onAddComment: (comment: string, isInternal: boolean) => Promise<void>
  canAddInternal?: boolean
}

export const IncidentComments: React.FC<IncidentCommentsProps> = ({
  comments,
  onAddComment,
  canAddInternal = false,
}) => {
  const [newComment, setNewComment] = useState("")
  const [isInternal, setIsInternal] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleSubmit = async () => {
    if (!newComment.trim()) return
    setIsSubmitting(true)
    try {
      await onAddComment(newComment, isInternal)
      setNewComment("")
      setIsInternal(false)
    } catch (error) {
      console.error("Failed to add comment:", error)
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 mb-4">
        <MessageSquare className="h-5 w-5 text-slate-500" />
        <h3 className="font-semibold">Bình luận ({comments.length})</h3>
      </div>

      <div className="space-y-3">
        {comments.map((comment) => (
          <div
            key={comment.id}
            className={`p-3 rounded-lg border ${
              comment.is_internal ? "bg-amber-50 border-amber-200" : "bg-slate-50 border-slate-200"
            }`}
          >
            <div className="flex items-start justify-between mb-2">
              <div className="flex items-center gap-2">
                <User className="h-4 w-4 text-slate-400" />
                <span className="font-medium text-sm">
                  {comment.user_name || "Ẩn danh"}
                </span>
                {comment.is_internal && (
                  <span className="text-xs bg-amber-100 text-amber-800 px-2 py-0.5 rounded">
                    Nội bộ
                  </span>
                )}
              </div>
              <span className="text-xs text-slate-500">
                {(() => {
                  const dateStr = comment.posted_at || comment.created_at;
                  if (!dateStr) return "Không xác định";
                  const date = new Date(dateStr);
                  return isNaN(date.getTime()) ? "Unknown" : format(date, "MMM d, yyyy HH:mm");
                })()}
              </span>
            </div>
            <p className="text-sm text-slate-700">{comment.comment}</p>
          </div>
        ))}
      </div>

      <div className="border-t pt-4">
        <Textarea
          placeholder="Thêm bình luận..."
          value={newComment}
          onChange={(e) => setNewComment(e.target.value)}
          rows={3}
          className="mb-2"
        />
        {canAddInternal && (
          <label className="flex items-center gap-2 mb-2 text-sm">
            <input
              type="checkbox"
              checked={isInternal}
              onChange={(e) => setIsInternal(e.target.checked)}
              className="rounded"
            />
            <span>Bình luận nội bộ (chỉ nhân viên thấy)</span>
          </label>
        )}
        <Button onClick={handleSubmit} disabled={!newComment.trim() || isSubmitting}>
          Thêm bình luận
        </Button>
      </div>
    </div>
  )
}
